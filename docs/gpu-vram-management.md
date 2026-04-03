# GPU VRAM management for local AI

Running AI models locally means dealing with one hard constraint: GPU memory. CPU and RAM are relatively flexible. VRAM is not. If your model doesn't fit, it either crashes or falls back to CPU, which makes inference 10-50x slower.

I run everything on a single workstation: RTX 5090 with 32GB VRAM. That sounds generous until you try to load a 70B model alongside a vision encoder and a small routing model. Then you realize every gigabyte matters.

This is what I've learned about managing VRAM in production-like local setups.

## The real cost of a model

The number you see on Hugging Face ("7B parameters") doesn't directly tell you how much VRAM you need. What matters is the parameter count combined with the precision.

A rough formula:

```
VRAM (GB) = parameters (B) * bytes_per_param + overhead
```

For common quantizations:

| Format    | Bytes per param | 7B model  | 13B model | 70B model  |
|-----------|-----------------|-----------|-----------|------------|
| FP32      | 4.0             | ~28 GB    | ~52 GB    | ~280 GB    |
| FP16/BF16 | 2.0             | ~14 GB    | ~26 GB    | ~140 GB    |
| Q8        | 1.0             | ~7 GB     | ~13 GB    | ~70 GB     |
| Q4_K_M    | ~0.56           | ~4.1 GB   | ~7.5 GB   | ~40 GB     |
| Q3_K_S    | ~0.44           | ~3.2 GB   | ~5.9 GB   | ~31 GB     |

These are base weights only. You need more on top of that.

## The hidden VRAM consumers

The model weights are just the starting point. Three things eat VRAM that people forget about.

**CUDA context.** When your GPU driver initializes, it reserves memory for its own bookkeeping. On my RTX 5090 this costs about 400-600MB. On older cards it can be more. This is memory you lose before loading anything. You can check it: load no model, just initialize CUDA, and compare total vs available.

**KV cache.** During inference, the model stores key-value pairs for every token in the context window. For a 7B model at Q4 with a 4096-token context, this can add 500MB-1GB. For a 70B model with 8192 context, you're looking at 4-8GB on top of the weights. This is the thing that kills you when you think you have "just enough" memory. Your model loads fine. It processes short prompts fine. Then someone sends a long document and you OOM.

**Batch overhead.** If you're doing concurrent inference (multiple requests at once), each request needs its own KV cache allocation. Two concurrent requests on a 13B model can double the KV cache cost.

## Pre-flight checks

I don't trust mental math for VRAM. I built `gpu-memory-guard` specifically because I got tired of loading models, watching them crash, and losing 30 seconds of GPU initialization time per attempt.

The idea is simple: before you load anything, check what's actually available.

```bash
# What's my GPU status right now?
python gpu_guard.py

# Will an 18GB model fit with a 2GB safety buffer?
python gpu_guard.py --model-size 18 --buffer 2

# Machine-readable output for automation
python gpu_guard.py --model-size 13 --json
```

In code, same thing:

```python
from gpu_guard import check_vram, can_load_model

# Quick boolean check
if can_load_model(model_size_gb=7.5, buffer_gb=1.0):
    load_model("mistral-7b-q4")
else:
    load_model("mistral-7b-q3")  # smaller quantization as fallback
```

The buffer parameter matters. I use 1-2GB as a safety margin for KV cache growth and CUDA overhead. Setting buffer to zero is asking for OOM on the second request.

## Multi-model strategies

Most real AI workflows involve more than one model. A typical CastelOS pipeline might use a small model for classification, a large model for generation, and a vision model for image understanding. Running all three simultaneously on 32GB VRAM doesn't work if they're all loaded at once.

**Sequential loading.** Load one model, run it, unload it, load the next. This is the safest approach and what I default to for batch workflows. The downside: model loading takes 5-15 seconds depending on size. For interactive use, this latency is noticeable.

```
Task arrives
  --> Check VRAM
  --> Load classifier (1.5GB)
  --> Classify input
  --> Unload classifier
  --> Load generator (18GB)
  --> Generate output
  --> Unload generator
  --> Return result
```

**Concurrent with budget.** Keep the small models resident and load/unload the large model on demand. The classifier stays in VRAM permanently (1.5GB is cheap). The generator loads when needed. This works if your GPU has enough headroom for the small models plus one large model at a time.

**Tiered fallback.** Try the best model first. If it doesn't fit, fall back to a smaller quantization or a smaller model entirely. This is what CastelOS does through hardware-aware routing: the system knows what's available and picks the best model that actually fits.

```
Preferred: mixtral-8x7b-q4 (~26GB)
Fallback 1: mistral-7b-q4  (~4.1GB)
Fallback 2: phi-3-mini-q4   (~2.3GB)
```

The routing decision happens before loading, not after a crash.

## Monitoring in practice

VRAM usage is not static. It changes during inference as KV cache grows and shrinks. I monitor three things:

**Peak usage during generation.** Not average, not idle. The peak determines whether you OOM. A model that shows 14GB at idle can spike to 22GB during long-context generation.

**Fragmentation.** GPU memory can fragment over time if you repeatedly load and unload models. 8GB free doesn't mean 8GB contiguous. If your model needs a single 8GB allocation and memory is fragmented into 4GB + 3GB + 1GB chunks, it won't load. Periodic full unload-and-reload cycles help.

**Trend over time.** Some inference engines have slow memory leaks. Not dramatic, but after 500 requests you might have 200MB less available than when you started. Logging VRAM after every N requests catches this before it becomes a crash at 3 AM.

## Practical rules I follow

After a year of running local AI workloads daily, these are the rules that stuck:

1. Always check before loading. Never assume yesterday's model still fits today. Other processes might be using the GPU.

2. Keep a 10-15% VRAM buffer. On a 32GB card, that means treating 27GB as your real ceiling.

3. Use quantized models in production. FP16 is for evaluation and benchmarking. Q4_K_M is usually the best balance of quality and size for inference.

4. Unload models you're not using. Leaving a model loaded "just in case" is a waste of your most constrained resource.

5. Log every OOM. If you hit out-of-memory, record which model, what context length, what else was loaded. Pattern-match later to find the real limits of your hardware.

6. Test with maximum context. Don't benchmark with 100-token prompts and then serve 8000-token documents. The KV cache difference will surprise you.

## Tools

- [gpu-memory-guard](https://github.com/CastelDazur/gpu-memory-guard) is the pre-flight check I use. CLI and Python API.
- `nvidia-smi` is the baseline. Use `watch -n 1 nvidia-smi` during inference to see real-time VRAM changes.
- `nvtop` gives a more readable real-time view with per-process GPU memory breakdown.
