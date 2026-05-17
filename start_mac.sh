#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export TBLLM_DEVICE="mps"
export PYTORCH_ENABLE_MPS_FALLBACK="1"
export TRANSFORMERS_NO_TF="1"
export TF_ENABLE_ONEDNN_OPTS="0"
export TOKENIZERS_PARALLELISM="false"
export HF_HOME="${ROOT_DIR}/.cache/huggingface"
export TRANSFORMERS_CACHE="${HF_HOME}/transformers"
export TBLLM_EMBEDDING_MODEL="${ROOT_DIR}/models/embedding/paraphrase-multilingual-MiniLM-L12-v2"
export TBLLM_EMBEDDING_LOCAL_ONLY="1"

mkdir -p "${TRANSFORMERS_CACHE}"

BACKEND_PID=""
FRONTEND_PID=""
BACKEND_PORT="5050"
FRONTEND_PORT="5173"
export TBLLM_BACKEND_PORT="${BACKEND_PORT}"

has_conda_tbllm() {
  command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "tbllm"
}

port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

print_port_users() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN || true
}

if ! command -v npm >/dev/null 2>&1 && ! has_conda_tbllm; then
  echo "Error: npm was not found. Install Node.js or run: conda install -n tbllm nodejs"
  exit 1
fi

if [[ ! -f "${TBLLM_EMBEDDING_MODEL}/modules.json" ]]; then
  echo "Warning: local embedding model not found at ${TBLLM_EMBEDDING_MODEL}"
  echo "Run this once before vector retrieval: cd backEnd && python scripts/prepare_embedding_model.py"
fi

if port_in_use "${BACKEND_PORT}"; then
  echo "Error: backend port ${BACKEND_PORT} is already in use."
  print_port_users "${BACKEND_PORT}"
  echo
  echo "Stop the old backend process first, then rerun ./start_mac.sh."
  exit 1
fi

if port_in_use "${FRONTEND_PORT}"; then
  echo "Error: frontend port ${FRONTEND_PORT} is already in use."
  print_port_users "${FRONTEND_PORT}"
  echo
  echo "Stop the old frontend process first, then rerun ./start_mac.sh."
  exit 1
fi

cleanup() {
  if [[ -n "${BACKEND_PID}" ]]; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID}" ]]; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting backend with PyTorch MPS: http://127.0.0.1:${BACKEND_PORT}"
(
  cd "${ROOT_DIR}/backEnd"
  if has_conda_tbllm; then
    conda run --no-capture-output -n tbllm python app.py
  elif [[ -f ".venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
    python app.py
  elif [[ -f "../.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "../.venv/bin/activate"
    python app.py
  else
    python3 app.py
  fi
) &
BACKEND_PID=$!

echo "Starting frontend: http://localhost:${FRONTEND_PORT}"
(
  cd "${ROOT_DIR}/frontEnd"
  if command -v npm >/dev/null 2>&1; then
    npm run dev -- --host 127.0.0.1
  else
    conda run --no-capture-output -n tbllm npm run dev -- --host 127.0.0.1
  fi
) &
FRONTEND_PID=$!

echo
echo "TBLLM is starting."
echo "Backend PID: ${BACKEND_PID}"
echo "Frontend PID: ${FRONTEND_PID}"
echo "Press Ctrl+C to stop both services."

wait
