---
title: 'Self-hosted LLMs in production: Ollama, quantization and hardware limits'
titleHtml: 'Self-hosted LLMs in production: Ollama, quantization and <em>hardware limits</em>'
description: 'Which model fits your server, what it costs, and when an API is actually cheaper. We do the memory math, pick a quant and serve the model over HTTP.'
pubDate: 2026-06-15
cat: ai
tags: [self-hosted ai, ollama]
minutes: 7
ctaTitle: 'Need your own AI <em>with no data leaks</em>?'
ctaText: "We'll deploy Ollama on your hardware with a ready HTTP API — data never leaves your perimeter, no token bills."
---

## How much memory you actually need

The rough formula: parameters × bytes per parameter + 1–2 GB for context. In a 4-bit quant (Q4_K_M is the sane default) an 8-billion-parameter model takes ~5 GB, a 27B one ~17 GB. That gives a simple hardware-to-model table:

```text
8 GB VRAM/RAM   → 7–8B  (llama3.1:8b, qwen2.5:7b)
16 GB           → 14B   (qwen2.5:14b)
24 GB           → 27–32B (gemma2:27b, qwen2.5:32b)
CPU only        → same models, 5–20× slower
```

Life without a GPU is possible: on an 8-core VPS an 8B model produces 5–10 tokens per second. Too slow for a chat with humans, fine for background text processing.

## Quantization: where the free lunch ends

A quant is lossy weight compression. Q4 is nearly indistinguishable from the original on typical tasks, Q3 and below gets noticeably dumber, Q8 is almost lossless but twice the size of Q4. The rule: take the biggest model that fits in Q4, not a small one in Q8 — a 14B-Q4 is consistently smarter than a 7B-Q8.

```bash
$ ollama pull qwen2.5:14b        # Q4_K_M by default
$ ollama run qwen2.5:14b "Summarize: …"
# the HTTP API is already listening:
$ curl localhost:11434/api/generate \
    -d '{"model":"qwen2.5:14b","prompt":"…"}'
```

<div class="practice"><span>FROM PRACTICE</span>By default Ollama unloads the model after 5 idle minutes — the first request after a pause "lags". For production we set <code>OLLAMA_KEEP_ALIVE=-1</code> and cap context memory via <code>num_ctx</code>.</div>

## To production: systemd, limits, access

In production Ollama runs as a systemd service or a container, listens on 127.0.0.1 only, and faces the world through a reverse proxy with a token. Do cap concurrency: two heavy requests at once on one GPU and both crawl.

```text
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_KEEP_ALIVE=-1
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

## When an API is cheaper after all

Honest arithmetic: a VPS with a 24 GB GPU costs ~$270/mo. If you run less than a couple million tokens a day, a cloud API is most likely cheaper. Self-hosting wins when data must not leave your perimeter (healthcare, legal, personal data), when volumes are large and steady, or when you need a predictable price with no vendor surprises.

<div class="checklist">
  <div>Model picked by memory: the biggest that fits in Q4</div>
  <div>OLLAMA_KEEP_ALIVE=-1 — the model stays loaded between requests</div>
  <div>API listens on 127.0.0.1; outside access via authed proxy</div>
  <div>Concurrency capped to GPU capacity</div>
  <div>Break-even point against a cloud API calculated</div>
</div>
