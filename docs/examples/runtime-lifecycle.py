# CastelOS Runtime Lifecycle State Machine
# Shows the promotion and shadow-testing workflow
# Actual state transition validation is private

# The system defines six promotion states for every runtime entry.
# Only one state allows normal execution. The rest are gatekeeping stages.

ALLOWED_NORMAL = {"approved_active"}       # Can serve production traffic
ALLOWED_WITH_FALLBACK = {                  # Used when primary is unavailable
    "approved_active", "fallback_only"
}
BLOCKED_STATES = {                         # Cannot serve any traffic
    "blocked", "deprecated", "candidate", "shadow"
}

class RuntimeLifecycle:
    """
    Manages runtime promotion through governance states.

    Lifecycle flow:
      candidate -> shadow -> approved_active
                          -> fallback_only (conditional)
      Any state -> blocked (policy violation)
      Any state -> deprecated (end-of-life)

    There is no separate 'evaluation' state. A candidate either
    enters shadow testing or gets blocked. The shadow stage IS
    the evaluation: it runs in parallel without serving users.
    """

    def __init__(self, runtime_key: str):
        self.runtime_key = runtime_key
        self.state = "candidate"
        self.shadow_results = []

    def can_serve_traffic(self, allow_fallback: bool = False) -> bool:
        """Check if this runtime can handle production requests."""
        allowed = ALLOWED_WITH_FALLBACK if allow_fallback else ALLOWED_NORMAL
        return self.state in allowed

    def promote_to_shadow(self) -> bool:
        """candidate -> shadow: Begin parallel execution testing."""
        if self.state != "candidate":
            return False
        self.state = "shadow"
        return True

    def collect_shadow_result(self, output: dict, metrics: dict):
        """Record parallel execution results for comparison."""
        self.shadow_results.append({
            "output": output,
            "metrics": metrics,
        })

    def promote_to_active(self) -> bool:
        """shadow -> approved_active: Runtime is fully trusted."""
        if self.state != "shadow":
            return False
        if not self._shadow_results_acceptable():
            return False
        self.state = "approved_active"
        return True

    def demote_to_fallback(self, reason: str):
        """approved_active -> fallback_only: Still usable but not preferred."""
        if self.state == "approved_active":
            self.state = "fallback_only"

    def block(self, reason: str):
        """Any state -> blocked: Policy violation detected."""
        self.state = "blocked"
        # Governance core logs reason and removes from routing

    def deprecate(self, reason: str):
        """Any state -> deprecated: End-of-life, no new traffic."""
        self.state = "deprecated"

    def _shadow_results_acceptable(self) -> bool:
        """Check if shadow testing produced satisfactory results."""
        if len(self.shadow_results) < 3:
            return False  # Need minimum sample size
        return True  # Actual scoring logic is private
