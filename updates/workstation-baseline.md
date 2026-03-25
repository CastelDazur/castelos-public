# Workstation and local-first baseline

## What happened this week

Documented the workstation setup and why hardware config matters for CastelOS.

## The setup

Running on: RTX 3060 12GB, 32GB DDR4, Ryzen 5. Not a datacenter rig. A workstation that sits in my office.

The 12GB VRAM sounds like a lot until you try to run two 7B quantized models at once. At Q4_K_M quantization, a 7B model takes about 4-5GB VRAM. So one model fits comfortably, two models need careful allocation, three is out of the question without offloading to RAM.

## Why this matters for the system

CastelOS needs to know these limits at startup. It polls GPU memory before loading models. If there's not enough VRAM for a second model, it queues the request instead of crashing.

The warm layer (RAM) holds recently used model states and task outputs. When a model gets evicted from GPU, its state goes to RAM first, not straight to disk.

## What's next

Runtime governance docs. How the system decides which model version is active and what happens when you want to upgrade.
