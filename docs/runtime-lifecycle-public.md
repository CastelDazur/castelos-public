# Runtime lifecycle (public-safe)

CastelOS manages model changes through a governed pipeline. No silent upgrades. Every runtime transition is logged, tested, and reversible.

## Why this matters

Most AI tools auto-update models without telling you. Your workflow works on Monday, breaks on Wednesday, and you have no idea why because the model changed underneath you.

I learned this firsthand. I swapped a model once without testing it properly. Same family, slightly different quantization. Outputs changed just enough to break a downstream task that depended on consistent formatting. Took two days to debug because I didn't know the model had changed behavior.

That's why every runtime change in CastelOS now goes through stages.

## The five stages

```
Candidate --> Eval --> Shadow --> Approved --> (Rollback if needed)
```

**Candidate.** Found a new model or a new version. Added it to the list. Not loaded, not tested yet. This is just identification: "there's something worth evaluating."

**Eval.** Load it in isolation. Run it against a set of known tasks. Compare latency, VRAM usage, output format, consistency. Does it actually perform better, or just benchmark better? Eval catches the obvious problems: wrong output format, unacceptable latency, excessive memory use.

**Shadow.** This is the most useful stage. Real requests flow through both the current model and the candidate. Candidate outputs are logged but never served to users. Shadow catches issues that synthetic tests miss: how the model handles long context, ambiguous instructions, or edge cases in your specific domain.

**Approved.** Passed shadow testing, now active in production. The switch is logged: which model, when, why, what shadow metrics looked like. If something breaks later, you can trace it back to the exact transition.

**Rollback.** Revert to the previous approved model. Not a panic button, just part of the process. The old model's state is preserved. Rollback is immediate because the previous runtime is never deleted until its replacement is fully proven.

## How transitions work

```
candidate --> shadow    (begin parallel execution)
shadow    --> approved   (shadow results acceptable)
approved  --> fallback   (still usable, not preferred)
any state --> blocked    (policy violation detected)
any state --> deprecated (end-of-life, no new traffic)
```

Only one state allows normal execution: `approved`. Everything else is either a testing stage or a restriction. The system defaults to safety: if a runtime's state is ambiguous, it cannot serve production traffic.

## What shadow testing actually reveals

Synthetic benchmarks tell you speed and perplexity. Shadow testing tells you whether the model works with your specific tasks, context windows, and output expectations.

In practice, shadow is where I catch:
- Format drift: outputs that are technically correct but structured differently enough to break parsing
- Latency spikes on specific input patterns that don't appear in benchmarks
- Inconsistent behavior with long context windows
- Edge cases in domain-specific reasoning

A model can ace synthetic benchmarks and still behave differently on real requests with messy context windows.

## Code example

See [`docs/examples/runtime-lifecycle.py`](examples/runtime-lifecycle.py) for a reference implementation of the state machine.

## What this document doesn't cover

The specific eval criteria, passing thresholds, scoring algorithms, and how shadow comparisons work internally. That's implementation detail and stays private.

The pattern itself is the valuable part. If you're building any system that depends on AI model outputs, you need a promotion pipeline. "Just upgrade" is not a strategy.
