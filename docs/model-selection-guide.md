# Model Selection Guide for Local AI Workloads

> Practical decision framework for choosing LLM models based on your hardware, task requirements, and quality expectations.

This guide helps you pick the right model for your local setup. No benchmarks marketing — just real-world observations from running models on consumer GPUs.

## Quick Decision Table

| VRAM Budget | Recommended Models | Quantization | Use Case |
|---|---|---|---|
| 8 GB | Llama 3.1 8B, Mistral 7B, Gemma 2 9B | Q4_K_M | Chat, simple coding, summarization |
| 12 GB | Llama 3.1 8B, Qwen 2.5 14B | Q4_K_M / Q5_K_M | Code generation, multi-turn reasoning |
| 16 GB | Qwen 2.5 14B, Phi-4 14B, DeepSeek-R1 14B | Q5_K_M / Q6_K | Complex reasoning, longer context |
| 24 GB | Llama 3.1 70B, Qwen 2.5 32B, Mixtral 8x7B | Q4_K_M | Production-quality tasks, agents |
| 32 GB | Llama 3.1 70B, DeepSeek-R1 70B, Qwen 2.5 72B | Q5_K_M / Q6_K | Near-API quality, multi-step agents |
| 48 GB+ | Llama 3.1 70B (full precision), 100B+ models | Q8_0 / FP16 | Maximum quality, research |

## VRAM Estimation Formula

For GGUF models, estimate VRAM usage with:

```
VRAM (GB) = (model_params_B * bits_per_weight / 8) + context_overhead
```

Where context overhead is approximately:
- 4K context: ~0.5 GB
- 8K context: ~1.0 GB
- 16K context: ~2.0 GB
- 32K context: ~4.0 GB

**Example**: Llama 3.1 70B at Q4_K_M
```
VRAM = (70 * 4.5 / 8) + 1.0 = ~40.4 GB
```

Use [gpu-memory-guard](https://github.com/CastelDazur/gpu-memory-guard) to check available VRAM before loading.

## Quantization Quality Ranking

From highest to lowest quality loss:

| Quantization | Bits/Weight | Quality Impact | When to Use |
|---|---|---|---|
| FP16 | 16.0 | None | You have enough VRAM and want zero compromise |
| Q8_0 | 8.0 | Negligible | Good VRAM headroom, want near-original quality |
| Q6_K | 6.5 | Minimal | Sweet spot for quality-conscious users |
| Q5_K_M | 5.5 | Small | Balanced quality and VRAM usage |
| Q4_K_M | 4.5 | Moderate | Best ratio of quality to VRAM savings |
| Q3_K_M | 3.5 | Noticeable | VRAM-constrained, acceptable for simple tasks |
| Q2_K | 2.5 | Significant | Last resort, quality drops noticeably |

**Rule of thumb**: Q4_K_M is the sweet spot for most users. Go higher if VRAM allows, avoid going below Q3_K_M.

## Task-Specific Model Recommendations

### Code Generation

Best models for local code generation ranked by quality:
1. **DeepSeek-Coder-V2** (16B / 236B) — strongest open coding model
2. **Qwen 2.5 Coder** (7B / 14B / 32B) — excellent for its size class
3. **CodeLlama 34B** — mature, well-tested for code tasks
4. **Phi-4 14B** — strong reasoning helps with code logic

### Multi-Turn Chat & Assistants

1. **Llama 3.1** (8B / 70B) — best general-purpose instruction following
2. **Qwen 2.5** (14B / 32B / 72B) — strong multilingual support
3. **Mistral** (7B) / **Mixtral** (8x7B) — fast, good for simple chat

### Reasoning & Analysis

1. **DeepSeek-R1** (14B / 70B) — explicit chain-of-thought reasoning
2. **Qwen 2.5** (32B / 72B) — strong analytical capabilities
3. **Llama 3.1 70B** — reliable for complex multi-step reasoning

### Creative Writing

1. **Llama 3.1 70B** — diverse, natural writing style
2. **Mistral Nemo 12B** — good creative output for its size
3. **Qwen 2.5 32B** — capable multilingual creative writing

## CastelOS Integration

CastelOS uses these principles for automatic model routing:

1. **Task classification** — incoming request is categorized (code, chat, reasoning, creative)
2. **VRAM check** — gpu-memory-guard verifies available memory
3. **Model selection** — picks the largest model that fits the task + VRAM budget
4. **Fallback chain** — if preferred model doesn't fit, downgrades gracefully

```
Task: code_generation
  → Try: deepseek-coder-v2-236b-q4
  → Fallback: qwen2.5-coder-32b-q5
  → Fallback: qwen2.5-coder-14b-q6
  → Minimum: qwen2.5-coder-7b-q8
```

## Multi-GPU Considerations

If you have multiple GPUs, model splitting across devices is possible but comes with trade-offs:

- **Tensor parallelism** (vLLM, TensorRT-LLM) — splits layers across GPUs, fastest inference
- **Pipeline parallelism** (llama.cpp) — sequential layer processing, simpler setup
- **Offloading** (llama.cpp `--n-gpu-layers`) — partial GPU acceleration with CPU fallback

**Recommendation**: Use a single GPU for models that fit. Split only when the quality gain from a larger model justifies the overhead.

## Practical Tips

1. **Start with the smallest model that works** for your task, then scale up if quality is insufficient
2. **Context length matters more than model size** for RAG and document QA tasks
3. **Batch size 1 is fine** for personal use — optimizing throughput only matters for multi-user serving
4. **Monitor actual VRAM** during inference — reported requirements often underestimate real usage by 10-15%
5. **Keep a buffer** of 1-2 GB free VRAM for system overhead and KV cache growth

## Hardware Reference

Based on real-world testing with consumer GPUs:

| GPU | VRAM | Best Model Class | Tokens/sec (Q4_K_M) |
|---|---|---|---|
| RTX 4060 Ti | 8 GB | 7-8B models | 40-60 t/s |
| RTX 4070 Ti Super | 16 GB | 14B models | 30-50 t/s |
| RTX 4090 | 24 GB | 32-70B (Q3-Q4) | 25-40 t/s |
| RTX 5090 | 32 GB | 70B models (Q5) | 35-55 t/s |
| 2x RTX 4090 | 48 GB | 70B+ models (Q6-Q8) | 20-35 t/s |

*Token rates are approximate for generation (not prompt processing) with 4K context.*

---

*Part of the [CastelOS](https://github.com/CastelDazur/castelos-public) build-in-public series. Updated April 2026.*
