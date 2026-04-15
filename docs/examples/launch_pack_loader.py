"""
launch_pack_loader.py

Minimal illustration of how a studio (historically called a "launch pack")
declares its task types and how the runtime dispatches work to them.

This is a public example, not the production loader. The real studio configs,
task type registry, and lane mapping stay private.

Usage:
    python launch_pack_loader.py

The point is to show the shape of the idea:
    1. A studio owns a namespace and a registry of task types.
    2. The runtime loads any number of studios at startup.
    3. A request names a task type; the runtime looks up the studio and dispatches.
    4. Adding a new class of work inside a studio is a registry update, not new infra.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
import json
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class TaskType:
    """One unit of work a studio can accept.

    `id` is namespaced, e.g. "text.summary.short" or "text.social.linkedin_post".
    `lane` tells the runtime which compute pool to route the call to.
    `handler` is the callable that does the actual work.
    """
    id: str
    lane: str
    handler: Callable[[dict], dict]


@dataclass
class Studio:
    """A scoped product surface for one domain.

    Each studio owns a namespace prefix and a registry of task types.
    The studio decides what work it accepts. The runtime decides how it runs.
    """
    name: str
    namespace: str
    task_types: dict[str, TaskType] = field(default_factory=dict)

    def register(self, task_type: TaskType) -> None:
        if not task_type.id.startswith(f"{self.namespace}."):
            raise ValueError(
                f"task type {task_type.id} does not belong to studio "
                f"{self.name} (namespace {self.namespace})"
            )
        self.task_types[task_type.id] = task_type

    def register_class(self, class_prefix: str, types: list[TaskType]) -> None:
        """Register a whole class of related task types in one go.

        Mirrors how a new class (e.g. text.social.*) gets added to an existing
        studio without touching the runtime or any other studio.
        """
        for t in types:
            if not t.id.startswith(f"{self.namespace}.{class_prefix}."):
                raise ValueError(
                    f"task type {t.id} not under class {class_prefix}"
                )
            self.register(t)


@dataclass
class Runtime:
    """Loads studios and dispatches work by task type id."""
    studios: dict[str, Studio] = field(default_factory=dict)
    log: list[dict] = field(default_factory=list)

    def load(self, studio: Studio) -> None:
        if studio.namespace in self.studios:
            raise ValueError(f"namespace {studio.namespace} already loaded")
        self.studios[studio.namespace] = studio

    def known_task_types(self) -> list[str]:
        out: list[str] = []
        for s in self.studios.values():
            out.extend(s.task_types.keys())
        return sorted(out)

    def dispatch(self, task_type_id: str, payload: dict) -> dict:
        namespace = task_type_id.split(".", 1)[0]
        studio = self.studios.get(namespace)
        if studio is None:
            raise KeyError(f"no studio loaded for namespace {namespace}")
        task = studio.task_types.get(task_type_id)
        if task is None:
            raise KeyError(f"task type {task_type_id} not registered")

        result = task.handler(payload)
        entry = {
            "call_id": _new_id("call"),
            "task_type": task_type_id,
            "studio": studio.name,
            "lane": task.lane,
            "timestamp": _now(),
            "result_keys": sorted(result.keys()),
        }
        self.log.append(entry)
        return result


# ---------------------------------------------------------------------------
# Demo handlers (toy implementations; real ones live elsewhere).
# ---------------------------------------------------------------------------

def _summary_short(payload: dict) -> dict:
    text = payload.get("text", "")
    return {"summary": text[:80] + ("..." if len(text) > 80 else "")}


def _summary_long(payload: dict) -> dict:
    return {"summary": payload.get("text", "")[:280]}


def _linkedin_post(payload: dict) -> dict:
    return {"draft": f"[LinkedIn draft] {payload.get('topic', '')}"}


def _x_post(payload: dict) -> dict:
    return {"draft": f"[X draft] {payload.get('topic', '')[:240]}"}


def _reddit_post(payload: dict) -> dict:
    return {"draft": f"[Reddit draft] {payload.get('topic', '')}"}


# ---------------------------------------------------------------------------
# Demo: build a Text Studio with old summary class, add new social class.
# ---------------------------------------------------------------------------

def build_text_studio() -> Studio:
    """Existing class: summary work the studio has carried for a while."""
    s = Studio(name="Text Studio", namespace="text")
    s.register_class("summary", [
        TaskType(id="text.summary.short", lane="llm.fast.local",
                 handler=_summary_short),
        TaskType(id="text.summary.long",  lane="llm.default.local",
                 handler=_summary_long),
    ])
    return s


def add_social_class(studio: Studio) -> None:
    """New class slotted into the existing studio.

    No new studio, no new runtime, no new approval surface. The runtime
    just sees more task types under the same namespace.
    """
    studio.register_class("social", [
        TaskType(id="text.social.linkedin_post", lane="llm.default.local",
                 handler=_linkedin_post),
        TaskType(id="text.social.x_post",        lane="llm.fast.local",
                 handler=_x_post),
        TaskType(id="text.social.reddit_post",   lane="llm.default.local",
                 handler=_reddit_post),
    ])


def _demo() -> None:
    runtime = Runtime()

    text = build_text_studio()
    runtime.load(text)
    print("After loading Text Studio with summary class:")
    print("  task types:", runtime.known_task_types())

    add_social_class(text)
    print("After adding social class to the same studio:")
    print("  task types:", runtime.known_task_types())

    # Dispatch one of each class through the same runtime entry point.
    runtime.dispatch("text.summary.short", {"text": "Studios grew from 12 to 15 this week."})
    runtime.dispatch("text.social.linkedin_post", {"topic": "studio depth not width"})

    print("\nDispatch log:")
    print(json.dumps(runtime.log, indent=2))


if __name__ == "__main__":
    _demo()
