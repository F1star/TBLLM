#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MODE="${1:-full}"
RUN_ID="${LORA_RUN_ID:-$(date +"%Y%m%d_%H%M%S")}"
OUTPUT_NAME="${LORA_OUTPUT_NAME:-qwen15_18b_chat_lora_m4max_${RUN_ID}}"

has_conda_tbllm() {
  command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "tbllm"
}

pick_python() {
  if has_conda_tbllm; then
    echo "conda run --no-capture-output -n tbllm python"
  elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    echo "${PROJECT_ROOT}/.venv/bin/python"
  elif [[ -x "${PROJECT_ROOT}/backEnd/.venv/bin/python" ]]; then
    echo "${PROJECT_ROOT}/backEnd/.venv/bin/python"
  else
    echo "python3"
  fi
}

PYTHON_CMD="$(pick_python)"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Warning: this script is tuned for macOS Apple Silicon MPS."
fi

export PYTHONUNBUFFERED="1"
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
export PYTORCH_MPS_HIGH_WATERMARK_RATIO="${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-1.70}"
export PYTORCH_MPS_LOW_WATERMARK_RATIO="${PYTORCH_MPS_LOW_WATERMARK_RATIO:-1.40}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export TRANSFORMERS_NO_TF="${TRANSFORMERS_NO_TF:-1}"
export HF_HOME="${HF_HOME:-${PROJECT_ROOT}/.cache/huggingface}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-${HF_HOME}/transformers}"

export LORA_OUTPUT_PATH="${LORA_OUTPUT_PATH:-${PROJECT_ROOT}/lora_weights_${OUTPUT_NAME}}"
export LORA_CHECKPOINT_DIR="${LORA_CHECKPOINT_DIR:-${PROJECT_ROOT}/lora_checkpoints_${OUTPUT_NAME}}"
export LORA_OUTPUT_MODEL_PATH="${LORA_OUTPUT_MODEL_PATH:-${PROJECT_ROOT}/models/${OUTPUT_NAME}}"

mkdir -p "${TRANSFORMERS_CACHE}" "${LORA_CHECKPOINT_DIR}" "${LORA_OUTPUT_PATH}" "${LORA_OUTPUT_MODEL_PATH}"

export TBLLM_DEVICE="mps"
export LORA_DEVICE="mps"
export LORA_MODEL_DTYPE="${LORA_MODEL_DTYPE:-float16}"
export LORA_TRAINER_FP16="0"
export LORA_TRAINER_BF16="0"
export LORA_USE_4BIT="0"

# M4 / 24GB unified memory max-quality profile for Qwen1.5-1.8B-Chat LoRA.
export LORA_R="${LORA_R:-32}"
export LORA_ALPHA="${LORA_ALPHA:-64}"
export LORA_DROPOUT="${LORA_DROPOUT:-0.05}"
export LORA_TRAIN_BATCH_SIZE="${LORA_TRAIN_BATCH_SIZE:-2}"
export LORA_EVAL_BATCH_SIZE="${LORA_EVAL_BATCH_SIZE:-1}"
export LORA_GRAD_ACCUM_STEPS="${LORA_GRAD_ACCUM_STEPS:-8}"
export LORA_MAX_SEQ_LENGTH="${LORA_MAX_SEQ_LENGTH:-2048}"
export LORA_NUM_TRAIN_EPOCHS="${LORA_NUM_TRAIN_EPOCHS:-3}"
export LORA_LEARNING_RATE="${LORA_LEARNING_RATE:-8e-5}"
export LORA_WARMUP_STEPS="${LORA_WARMUP_STEPS:-100}"
export LORA_LOGGING_STEPS="${LORA_LOGGING_STEPS:-10}"
export LORA_SAVE_STEPS="${LORA_SAVE_STEPS:-200}"
export LORA_EVAL_STEPS="${LORA_EVAL_STEPS:-200}"
export LORA_SAVE_TOTAL_LIMIT="${LORA_SAVE_TOTAL_LIMIT:-2}"
export LORA_WEIGHT_DECAY="${LORA_WEIGHT_DECAY:-0.01}"
export LORA_GRADIENT_CHECKPOINTING="${LORA_GRADIENT_CHECKPOINTING:-1}"
export LORA_OPTIM="${LORA_OPTIM:-adamw_torch}"

case "${MODE}" in
  quick|--quick)
    export LORA_TEST_MODE="1"
    export LORA_TRAIN_BATCH_SIZE="${LORA_QUICK_TRAIN_BATCH_SIZE:-1}"
    export LORA_MAX_SEQ_LENGTH="${LORA_QUICK_MAX_SEQ_LENGTH:-1024}"
    export LORA_MAX_STEPS="${LORA_MAX_STEPS:-20}"
    export LORA_SAVE_STEPS="${LORA_QUICK_SAVE_STEPS:-20}"
    export LORA_EVAL_STEPS="${LORA_QUICK_EVAL_STEPS:-20}"
    export LORA_LOGGING_STEPS="${LORA_QUICK_LOGGING_STEPS:-5}"
    echo "Running quick LoRA smoke test for macOS MPS..."
    ;;
  full|--full)
    export LORA_TEST_MODE="0"
    export LORA_MAX_STEPS="${LORA_MAX_STEPS:-}"
    echo "Running full LoRA training for macOS MPS..."
    ;;
  *)
    echo "Usage: $0 [full|quick]"
    exit 2
    ;;
esac

if [[ ! -f "${PROJECT_ROOT}/models/Qwen1.5-1.8B-Chat/config.json" ]]; then
  echo "Error: base model not found at ${PROJECT_ROOT}/models/Qwen1.5-1.8B-Chat"
  exit 1
fi

if [[ ! -f "${PROJECT_ROOT}/datasets/questionnaire_dialogue_train.json" || ! -f "${PROJECT_ROOT}/datasets/questionnaire_dialogue_val.json" ]]; then
  if [[ -f "${PROJECT_ROOT}/datasets/questionnaire_finetuning_full.jsonl" ]]; then
    echo "Dialogue dataset is missing; converting questionnaire_finetuning_full.jsonl first..."
    (cd "${PROJECT_ROOT}" && ${PYTHON_CMD} "${SCRIPT_DIR}/convert_questionnaire_to_dialogue.py")
  else
    echo "Error: training dataset not found under ${PROJECT_ROOT}/datasets"
    exit 1
  fi
fi

echo "Python command: ${PYTHON_CMD}"
${PYTHON_CMD} - <<'PY'
import sys
import torch

print(f"PyTorch: {torch.__version__}")
print(f"MPS available: {torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False}")
if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
    print("Error: MPS is not available. Install macOS PyTorch dependencies from backEnd/requirements-mac-mps.txt.", file=sys.stderr)
    sys.exit(1)
PY

echo
echo "Effective LoRA profile:"
echo "  run_id=${RUN_ID}"
echo "  device=${LORA_DEVICE}, dtype=${LORA_MODEL_DTYPE}, use_4bit=${LORA_USE_4BIT}"
echo "  r=${LORA_R}, alpha=${LORA_ALPHA}, dropout=${LORA_DROPOUT}"
echo "  batch=${LORA_TRAIN_BATCH_SIZE}, grad_accum=${LORA_GRAD_ACCUM_STEPS}, max_seq=${LORA_MAX_SEQ_LENGTH}"
echo "  epochs=${LORA_NUM_TRAIN_EPOCHS}, lr=${LORA_LEARNING_RATE}, max_steps=${LORA_MAX_STEPS:-none}"
echo "  output=${LORA_OUTPUT_PATH}"
echo "  checkpoints=${LORA_CHECKPOINT_DIR}"
echo

(cd "${PROJECT_ROOT}" && ${PYTHON_CMD} "${SCRIPT_DIR}/finetune_lora.py")

echo
echo "LoRA adapter written to:"
echo "  ${LORA_OUTPUT_PATH}"
echo
echo "To use this adapter when starting the backend:"
echo "  TBLLM_FINETUNED_MODEL_PATH=\"${LORA_OUTPUT_PATH}\" ./start_mac.sh"
