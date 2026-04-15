# Studio expansion this week

Issue #6 already covered why the system is shaped as one runtime + 15 studios.
This note logs what changed structurally this week.

## What changed

One existing studio more than doubled its task type count by adding a whole new class of work. No new repo, no new orchestrator, no new approval surface. The studio just declared the new class in its task type registry and the runtime picked it up on the next reload.

That is the cheap path. Adding a 16th studio would have meant a new domain boundary, new naming, new routing decisions. Adding a new class inside an existing studio means more useful work on a surface that already passes the upgrade gate.

## What the example shows

`docs/examples/launch_pack_loader.py` is a small runnable demo of the same shape. A studio holds a task type registry. The runtime loads it, dispatches by namespaced task type id, logs the call. Adding a new task type group is a few lines, not a new system.

Demo only. Production loader, real registry, lane mapping stay private.

## Next

How outputs from these task types get classified and presented as business surfaces.
