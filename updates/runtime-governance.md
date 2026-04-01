# Runtime governance basics

## What happened this week

Documented the runtime lifecycle. How models go from "new thing I want to try" to "actually used in production."

## The lifecycle

Five stages. Candidate means I found it and want to test it. Eval means running it against known tasks to see how it performs. Shadow means it processes real requests in parallel with the current model, but its outputs get discarded. Approved means it's the active runtime. Rollback means something went wrong and I reverted.

## Why bother

Tried the "just swap models" approach early on. Replaced a Q4_K_M 7B with a Q5_K_M version thinking it would be strictly better. It was slower, used more VRAM, and gave slightly different outputs for the same prompts. Took me a while to figure out why certain tasks started failing.

Now every model change goes through eval and shadow before anything switches over. Takes more time upfront but saves debugging sessions later.

## What's not shown

Internal eval criteria, real benchmark numbers, and the actual config files that define the lifecycle transitions. Those are product internals.

## Next

Trust and approval gates. How the system decides what's safe to use and what needs human review.
