# Workstation and local-first baseline

## What happened this week

Documented the workstation setup and why hardware config matters for CastelOS.

## The setup

Running on: RTX 5090 32GB, 96GB DDR5 CL30, Ryzen 9 9950X3D. Not a cloud VM. A workstation that sits in my office and runs everything locally.

32GB VRAM changes what's possible compared to smaller cards. Qwen2.5-32B at 4-bit quantization takes about 18-22GB, so it stays loaded as the default model. That leaves enough room for embeddings (BGE-M3) on GPU if I want faster indexing, or I can keep those on CPU and save the headroom for on-demand models.

The tricky part: when I need R1 for reasoning tasks, it also wants 18-22GB. Can't have both loaded at the same time. So the system does hot-swap, unloading Qwen32 and loading R1, then switching back. Not instant, but predictable.

## Why this matters for the system

CastelOS checks VRAM budget before loading any model. If R1 is requested but Qwen32 is still hot, the system queues the request, swaps models, runs the job, then restores the default. No OOM crashes, no silent failures.

96GB system RAM helps too. Model states and recent outputs live in RAM as a warm cache. Evicted GPU models go to RAM first, not straight to disk. With 96GB there's plenty of room for that plus the OS, browser automation, and background indexing.

## What's next

Runtime governance docs. How the system decides which model version is active and what happens when you want to upgrade.
