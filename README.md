# CastelOS — Public Artifacts

> Principles, architecture insights, and build-in-public content from the CastelOS project.

## What is CastelOS

CastelOS is a **local-first AI execution system** designed to run on real hardware and turn one powerful workstation into a controlled engine for business workflows.

Instead of scattered SaaS tools and random AI wrappers, CastelOS provides:

- **Governed runtimes** — every task runs with structure, evidence, and audit trails
- **Hardware-aware routing** — capabilities matched to GPU / RAM / CPU resources
- **Knowledge automation** — structured flows instead of manual copy-paste
- **Domain packs** — installable workflow profiles for specific business scenarios

## What you'll find here

This repository contains public artifacts from the CastelOS build-in-public journey:

- Architecture principles and design decisions
- System thinking notes and execution frameworks
- Weekly insights from building a local-first AI OS

## System architecture

CastelOS operates as three integrated layers:

<div align="center">
  <img src="./assets/castelos-architecture-overview.svg" width="840" alt="CastelOS Architecture Overview" />
</div>

### 1. Workstation

The hardware foundation where the system runs. Local-first design means the workstation is not just a client — it is the operating base. Hardware decisions shape runtime behavior, memory strategy, and latency expectations.

### 2. Core

The governed execution engine.

- Manages runtime lifecycle (candidate → eval → shadow → approved → active)
- Enforces approval gates for important outputs
- Maintains task state and artifact history
- Handles runtime upgrades safely and reversibly

### 3. Packs

Installable execution bundles.

- Each pack encodes a task, a workflow, or a domain capability
- Packs execute against the core's governed runtimes
- Outputs are structured, queryable, and preservable
- Packs can be replaced, audited, or rolled back without cascading failures

### Why this structure matters

This three-layer design separates concerns:

- **Hardware** stays under local control
- **Runtime** stays governed and measurable
- **Execution** stays modular and reversible

No layer depends on external defaults or SaaS-only choices. The operator makes the call.

## Runtime governance

Models in CastelOS don't auto-update. New versions go through eval and shadow testing before they replace anything.

The lifecycle: candidate (identified), eval (tested in isolation), shadow (tested on real workloads without affecting output), approved (active), rollback (revert if needed).

I learned this the hard way after swapping a model that looked better on benchmarks but behaved differently on actual tasks. The formatting changed just enough to break a downstream pack. Now every model change has a paper trail and a rollback path.

Shadow testing is the most useful stage. Synthetic benchmarks tell you speed and perplexity. Shadow tells you if the model actually works with your specific tasks and context windows.

See [docs/runtime-lifecycle-public.md](docs/runtime-lifecycle-public.md) for the full governance guide and [assets/runtime-lifecycle-flow.mermaid](assets/runtime-lifecycle-flow.mermaid) for the visual pipeline diagram.

Internal eval configs and transition rules are not in this repo.

## Philosophy

- **System over model** — the value is in orchestration, not in any single LLM
- **Execution over chat** — real outputs with artifacts, not just conversations
- **Governance over hype** — controlled, repeatable, auditable workflows
- **Local-first** — privacy, speed, and ownership by design

## Trust and approvals

Not every AI output should be used without checking it first.

CastelOS classifies outputs by risk level. Low-risk tasks (structured extraction with known templates) pass through automatically but still get logged. Higher-risk outputs (new task types, anything shared externally) require human review before they're used.

I added this after a model produced a plausible-looking but wrong number in a summary. Caught it by accident. Now anything that leaves the system or goes to someone else hits a review gate first.

The approval log records who approved what and when. If an output causes problems later, you can trace it back to the approval decision.

Internal approval rules and risk classifications are not part of this public repo.
