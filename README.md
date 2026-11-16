# Quantum-Simulated LLM with Agentic Workflows

**A hybrid quantum-classical language model with adaptive qubit routing and agentic workflows.**

Research proof-of-concept exploring whether quantum circuits can meaningfully enhance transformer attention. Not a production model — a working experiment with end-to-end trainability through quantum circuits.

[![License: Proprietary](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![PennyLane](https://img.shields.io/badge/PennyLane-0.44.1-purple.svg)](https://pennylane.ai/)

---

## What This Is

A hybrid transformer where key components run through parameterized quantum circuits on simulated qubits:

| Component | Classical | Quantum |
|-----------|-----------|---------|
| **Token Embedding** | Lookup table | + Quantum feature map (amplitude encoding) |
| **Positional Encoding** | Sinusoidal | + Quantum angle encoding per position |
| **Attention** | Scaled dot-product | + Adaptive qubit MoE (6/9/12 qubit experts with trainable router) |
| **Activation** | GELU | + Quantum activation circuit |
| **Reasoning** | — | Quantum decision circuit + pattern matcher |
| **Memory** | — | Quantum associative recall |
| **Agent** | Tool-use loop | Quantum-enhanced tool selection + multi-agent coordination |

Built on PennyLane + NumPy. Zero PyTorch dependency. Includes a fast numpy quantum simulator for small circuits (informational speedup vs PennyLane QNode; no speedup assertion).

## Architecture

```
Input Text
    │
    ▼
┌─────────────────────────────────────┐
│  Character Tokenizer                │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Hybrid Embedding Layer             │
│  ├── Classical token lookup         │
│  ├── Quantum feature map (4-8 qub) │
│  └── Quantum positional enc        │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Hybrid Transformer Block (×N)      │
│  ├── LayerNorm                      │
│  ├── Quantum Multi-Head Attention   │
│  │   ├── Classical heads (3)        │
│  │   └── MoE Quantum head           │
│  │       └── Router → 6/9/12 qubits │
│  ├── LayerNorm                      │
│  └── Hybrid Feed-Forward            │
│      └── GELU / Quantum Activation  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Language Model Head → Logits       │
└─────────────────────────────────────┘
```

## Quick Start

```bash
# Clone pinned release v0.1.0 (full clone so tag + commit objects are present)
git clone -q --branch v0.1.0 https://github.com/saikrishnajava/quantum-llm-agent.git
cd quantum-llm-agent
EXPECTED_SHA=1587497de77d33942a045b091aaded1ef45b5785
git rev-parse HEAD \
  && git verify-tag v0.1.0 \
  && git verify-commit HEAD \
  && [ "$(git rev-parse HEAD)" = "$EXPECTED_SHA" ] || exit 1
# Tag-trust: e161aed0 is the tag object SHA; 1587497de77d33942a045b091aaded1ef45b5785 is the commit SHA it points to. Single pinned full SHA; verify-tag/verify-commit confirm authenticity.

# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install --require-hashes -r requirements.lock

# Run the 12-qubit proof of concept
python examples/demos/poc_12qubit.py

# Run training on Shakespeare
python examples/demos/train_gpu.py

# Run MoE training (adaptive qubit routing)
python examples/demos/train_moe.py

# Run tests
python -m pytest tests/ -v
```

## Training

The model trains with real gradient descent through quantum circuits:

```python
from hybrid.interfaces.model import HybridQuantumLLM
from classical.optimizers.trainer import HybridQuantumTrainer
from classical.tokenizer import CharTokenizer

tokenizer = CharTokenizer.from_text("your training text here")
model = HybridQuantumLLM.from_config("proof_of_concept")
trainer = HybridQuantumTrainer(model, learning_rate=1e-3)

# Each step computes gradients through quantum circuits
result = trainer.training_step(input_ids, labels)
print(f"loss={result['loss']:.4f}, grad_norm={result['grad_norm']:.4f}")
```

Training speed depends on backend and model:

| Backend | Hardware | Speed | Notes |
|---------|----------|-------|-------|
| Fast numpy simulator | Linux CPU | ~2482ms Run 1 | Default for ≤12 qubits |
| Fast numpy simulator (tuned) | Linux CPU | ~1050ms Run 3 | More than halved vs Run 1 |
| Adaptive qubit MoE | Linux CPU | ~3276ms | 6/9/12-qubit experts |

GPU note: on this small scale the Colab T4 GPU (~4362ms per step) is slower than Linux CPU (~2450ms per step) — transfer overhead outweighs parallelization.

## Project Structure

```
quantum-llm-agent/
├── quantum/              # Quantum circuit components
│   ├── circuits/core.py  #   Feature map, attention, activation, positional circuits
│   ├── simulator/        #   Fast numpy statevector simulator (autograd-compatible)
│   ├── moe/              #   Adaptive qubit router + mixture-of-experts
│   ├── encodings/        #   Amplitude, angle, basis, variational encoders
│   ├── gates/layers.py   #   Reusable gate patterns
│   └── backends/         #   Device management + resource tracking
├── classical/            # Classical ML components
│   ├── nn.py             #   Module, Linear, Embedding, LayerNorm, GELU, AdamW, etc.
│   ├── tokenizer.py      #   Character-level tokenizer
│   ├── data.py           #   Dataset + DataLoader
│   └── optimizers/       #   Hybrid quantum-classical trainer
├── hybrid/               # Quantum-classical integration
│   ├── attention/        #   Quantum multi-head attention + MoE attention
│   ├── embeddings/       #   Hybrid embedding layer
│   ├── feedforward/      #   Hybrid FFN with quantum activation
│   └── interfaces/       #   Full model, caching, profiling
├── agents/               # Agentic workflows
│   ├── reasoning/        #   Quantum decision + pattern matching
│   ├── memory/           #   Quantum associative memory
│   └── coordination/     #   Agent loop + multi-agent coordinator
├── tests/                # 51 tests (unit, integration, gradient flow, MoE, benchmarks)
├── config/               # YAML configs for backends, models, training
└── examples/demos/       # Runnable demos
```

## Key Results

| Metric | Value |
|--------|-------|
| Quantum circuit types | 6 (feature map, positional, attention, activation, decision, pattern) |
| Adaptive qubit MoE | Trainable router over 6/9/12 qubit experts |
| Training | End-to-end gradient flow through quantum circuits |
| Fast simulator | numpy tensor ops; informational speedup only |
| Tests | 51 passing |
| Dependencies | PennyLane + NumPy + SciPy + PyYAML (+ pennylane-lightning) |
| Quantum advantage at capacity/20 epochs | None — all models at chance (48–50%), Winner = Tie (N=3 exploratory) |
| Defensible claim | Param-efficiency only: quantum / moe_6_9 reach chance accuracy with fewer quantum params |

**Current scale:** ~11K params, character-level, trained on Shakespeare. Output is not coherent — this is a proof-of-concept for the architecture, not a production language model.

See `docs/parity-efficiency-pivot.md` for the parity/efficiency pivot (Spec P,F6-docs): no advantage at capacity/20 epochs, param-efficiency only, both at chance 48–50%, N=3 exploratory (not N=5), moe_6_9 naming.

## Requirements

- Python 3.10+
- PennyLane >= 0.39.0, <0.45
- NumPy >= 1.24.0, <2
- SciPy >= 1.11.0, <2
- PyYAML >= 6.0, <7
(Upper bounds mirror pyproject.toml:14-18.)

Optional for GPU acceleration:
- NVIDIA GPU with CUDA (compute capability 7.0+ / Volta or newer)
- `pennylane-lightning[gpu]`
- Note: Pascal GPUs (P2200, GTX 1080, etc.) are not supported by lightning.gpu — they fall back to lightning.qubit (C++ CPU) automatically

## GPU Setup (NVIDIA)

```bash
bash setup_gpu.sh
python examples/demos/train_gpu.py
```

The training script auto-detects the fastest available backend.

## Citation

If you use this work in your research, please cite:

```
@software{garikipati2026quantum_llm,
  author = {Garikipati, Saikrishna},
  title = {Quantum-Simulated LLM with Agentic Workflows},
  year = {2026},
  url = {https://github.com/saikrishnajava/quantum-llm-agent}
}
```

## License

Copyright (c) 2026 Saikrishna Garikipati. **All Rights Reserved.**

This software is proprietary. No permission is granted to copy, modify, distribute, or use this software without the prior written consent of the author. See [LICENSE](LICENSE) for full terms.

For licensing inquiries, research collaboration, or commercial use, contact Saikrishna Garikipati.

## Author

**Saikrishna Garikipati**

---

*This is a research proof-of-concept. It demonstrates that quantum circuits can be integrated into a transformer architecture with end-to-end trainability and adaptive qubit allocation. It does not produce coherent text at current scale — that requires more data, larger models, and more compute. The architecture is designed to be hardware-ready for future quantum computers.*
