"""
approval_gate.py

Minimal illustration of how CastelOS classifies outputs by risk and routes
them through an approval gate before they reach users or external systems.

This is a public example, not the production implementation. Real
classification rules, thresholds, and routing policies stay private.

Usage:
    python approval_gate.py

The point is to show the shape of the idea:
    1. An output is produced.
    2. It gets classified (LOW / MEDIUM / HIGH).
    3. The gate decides: auto-pass, queue for review, or block until approved.
    4. Every decision is logged with metadata (who, what, when, which model).

Nothing fancy. No external dependencies. Runs as-is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional
import json
import uuid


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(str, Enum):
    AUTO_PASS = "auto_pass"
    QUEUED_FOR_REVIEW = "queued_for_review"
    BLOCKED_UNTIL_APPROVED = "blocked_until_approved"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Output:
    """An output the system wants to release."""
    output_id: str
    task_type: str
    payload: str
    model: str
    pack: str
    destination: str  # e.g. "internal_log", "shared_doc", "client_email"


@dataclass
class AuditEntry:
    """A single decision in the audit trail."""
    entry_id: str
    output_id: str
    risk: Risk
    decision: Decision
    approver: Optional[str]
    timestamp: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "output_id": self.output_id,
            "risk": self.risk.value,
            "decision": self.decision.value,
            "approver": self.approver,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# Classification rules for this demo.
# In the real system these live in a private config and get adjusted
# based on where hallucinations actually show up.
SAFE_TASK_TYPES = {"structured_extraction", "known_template_fill"}
SHARED_DESTINATIONS = {"shared_doc", "team_channel"}
EXTERNAL_DESTINATIONS = {"client_email", "public_post", "published_doc"}


def classify(output: Output) -> Risk:
    """Decide the risk level for an output.

    Low:    known template, internal use only.
    Medium: new task type or shared inside the team.
    High:   anything that leaves the system.
    """
    if output.destination in EXTERNAL_DESTINATIONS:
        return Risk.HIGH
    if output.destination in SHARED_DESTINATIONS:
        return Risk.MEDIUM
    if output.task_type in SAFE_TASK_TYPES:
        return Risk.LOW
    return Risk.MEDIUM


@dataclass
class ApprovalGate:
    """Routes outputs through classification and approval.

    Every decision, including auto-passes, is written to the audit log.
    Nothing is silent.
    """
    audit_log: list[AuditEntry] = field(default_factory=list)
    pending: dict[str, Output] = field(default_factory=dict)

    def submit(self, output: Output) -> AuditEntry:
        risk = classify(output)

        if risk is Risk.LOW:
            entry = AuditEntry(
                entry_id=_new_id("audit"),
                output_id=output.output_id,
                risk=risk,
                decision=Decision.AUTO_PASS,
                approver=None,
                timestamp=_now(),
                reason="low_risk_template_path",
            )
        elif risk is Risk.MEDIUM:
            entry = AuditEntry(
                entry_id=_new_id("audit"),
                output_id=output.output_id,
                risk=risk,
                decision=Decision.QUEUED_FOR_REVIEW,
                approver=None,
                timestamp=_now(),
                reason="new_or_shared_surface",
            )
            self.pending[output.output_id] = output
        else:  # HIGH
            entry = AuditEntry(
                entry_id=_new_id("audit"),
                output_id=output.output_id,
                risk=risk,
                decision=Decision.BLOCKED_UNTIL_APPROVED,
                approver=None,
                timestamp=_now(),
                reason="external_destination",
            )
            self.pending[output.output_id] = output

        self.audit_log.append(entry)
        return entry

    def approve(self, output_id: str, approver: str, reason: str = "ok") -> AuditEntry:
        if output_id not in self.pending:
            raise KeyError(f"{output_id} not pending")
        del self.pending[output_id]
        entry = AuditEntry(
            entry_id=_new_id("audit"),
            output_id=output_id,
            risk=Risk.HIGH,  # approvals always log at high visibility
            decision=Decision.APPROVED,
            approver=approver,
            timestamp=_now(),
            reason=reason,
        )
        self.audit_log.append(entry)
        return entry

    def reject(self, output_id: str, approver: str, reason: str) -> AuditEntry:
        if output_id not in self.pending:
            raise KeyError(f"{output_id} not pending")
        del self.pending[output_id]
        entry = AuditEntry(
            entry_id=_new_id("audit"),
            output_id=output_id,
            risk=Risk.HIGH,
            decision=Decision.REJECTED,
            approver=approver,
            timestamp=_now(),
            reason=reason,
        )
        self.audit_log.append(entry)
        return entry

    def dump_log(self) -> str:
        return json.dumps([e.to_dict() for e in self.audit_log], indent=2)


def _demo() -> None:
    gate = ApprovalGate()

    # Low risk: structured extraction into internal log.
    o1 = Output(
        output_id=_new_id("out"),
        task_type="structured_extraction",
        payload="{invoice_total: 1240}",
        model="local-sml-4b",
        pack="finance_extract",
        destination="internal_log",
    )
    gate.submit(o1)

    # Medium risk: new task type shared inside the team.
    o2 = Output(
        output_id=_new_id("out"),
        task_type="meeting_summary",
        payload="3 action items, 2 blockers.",
        model="local-mid-8b",
        pack="ops_summarize",
        destination="shared_doc",
    )
    gate.submit(o2)

    # High risk: going to a client.
    o3 = Output(
        output_id=_new_id("out"),
        task_type="client_update",
        payload="We shipped the reconciliation module.",
        model="local-mid-8b",
        pack="client_comms",
        destination="client_email",
    )
    entry = gate.submit(o3)
    gate.approve(entry.output_id, approver="dmytro", reason="checked facts")

    print(gate.dump_log())


if __name__ == "__main__":
    _demo()
