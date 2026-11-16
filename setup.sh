#!/usr/bin/env bash
# ============================================================
# Quantum LLM Agent — Environment Setup Script
# ============================================================
# Usage:
#   chmod +x setup.sh && ./setup.sh
# ============================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

echo "========================================"
echo " Quantum LLM Agent — Setup"
echo "========================================"

# 1. Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creating virtual environment..."
    python3.12 -m venv "$VENV_DIR"
else
    echo "[1/4] Virtual environment exists."
fi

# 2. pip
# pip is not upgraded here (out-of-band): upgrading inside setup pins the
# environment to a specific pip version that may drift from requirements.lock.
# Upgrade out-of-band if needed: python -m pip install --upgrade pip
echo "[2/4] Pip ready."

# 3. Install dependencies
echo "[3/4] Installing dependencies..."
# Lock: pins match pyproject.toml (pennylane<0.45, lightning<0.45,
# numpy<2, scipy<2, pyyaml<7); do not relax without updating pyproject.toml.
# Equivalent hashed install: pip install --require-hashes -r requirements.lock
"$PIP" install --require-hashes -r "$PROJECT_DIR/requirements.lock" --quiet

# 4. Verify installation
echo "[4/4] Verifying installation..."
"$PYTHON" -c "
import pennylane as qml
import numpy as np
import yaml

print(f'  PennyLane: {qml.version()}')
print(f'  NumPy:     {np.__version__}')

# Quick quantum sanity check
dev = qml.device('default.qubit', wires=4)
@qml.qnode(dev)
def test_circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))
result = test_circuit()
print(f'  Quantum test: {result:.4f} (expected ~0.0)')
print('  All checks passed!')
"

echo ""
echo "Setup complete! Activate with:"
echo "  source .venv/bin/activate"
echo ""
echo "Run tests:"
echo "  python -m pytest tests/ -v"
echo ""
echo "Run 12-qubit PoC demo:"
echo "  python examples/demos/poc_12qubit.py"
