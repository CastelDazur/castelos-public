# Trust, approvals, and safe outputs

## What happened this week

Added docs about the approval system. How CastelOS decides what gets used immediately vs what needs a human to check it first.

## The problem

Early on I had no approval gates. Every output went straight through. Worked fine until a model hallucinated a plausible-looking number in a summary. I didn't catch it. That's when I added review steps.

## How it works now

Outputs get classified by risk level. Low risk stuff (structured extraction, known templates) goes through without blocking. Medium risk (new task types, shared outputs) gets queued for review. High risk (published content, client-facing outputs) requires explicit approval with a log entry.

The classification isn't perfect yet. I've been adjusting boundaries based on where hallucinations actually show up vs where I expected them.

## The audit trail

Every output has metadata: which model produced it, what pack was used, what approval level applied, who signed off (if anyone). You can query this later.

## What the example code shows

See `examples/approval_gate.py` for a minimal, self-contained illustration of the classification idea. It is a demo, not the production implementation. The real rules, thresholds, and risk configs stay private.

## What's not shown

The specific classification rules, risk thresholds, and internal approval configs.

## Next

Packs, outcomes, and how the execution layer is structured.
