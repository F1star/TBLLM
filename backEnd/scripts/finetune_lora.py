#!/usr/bin/env python3
"""
使用LoRA对Qwen1.5-1.8B-Chat进行微调
训练目标：根据问卷回答评估学生技能水平
"""

import os
import sys
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import Dataset
import numpy as np
from datetime import datetime
import logging

# 项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(SCRIPT_DIR, 'finetune_lora.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

GLOBAL_TOKENIZER = None
GLOBAL_MAX_LENGTH = None

def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

def _env_int(name, default):
    value = os.environ.get(name)
    return int(value) if value not in (None, "") else default

def _env_float(name, default):
    value = os.environ.get(name)
    return float(value) if value not in (None, "") else default

def _env_optional_int(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    if value.strip().lower() in {"none", "null", "-1"}:
        return None
    return int(value)

def _env_list(name, default):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return [item.strip() for item in value.split(",") if item.strip()]

def _env_path(name, default):
    value = os.environ.get(name, default)
    if os.path.isabs(value):
        return value
    return os.path.join(PROJECT_ROOT, value)

def _torch_dtype(dtype_name):
    normalized = str(dtype_name).strip().lower()
    if normalized in {"fp16", "float16", "half"}:
        return torch.float16
    if normalized in {"bf16", "bfloat16"}:
        return torch.bfloat16
    return torch.float32

def _config_snapshot(config, device):
    return {
        "device": device,
        "test_mode": config.test_mode,
        "base_model_path": config.base_model_path,
        "output_model_path": config.output_model_path,
        "checkpoint_dir": config.checkpoint_dir,
        "lora_output_path": config.lora_output_path,
        "train_data_path": config.train_data_path,
        "val_data_path": config.val_data_path,
        "model_dtype": config.model_dtype,
        "lora_r": config.lora_r,
        "lora_alpha": config.lora_alpha,
        "lora_dropout": config.lora_dropout,
        "lora_target_modules": config.lora_target_modules,
        "num_train_epochs": config.num_train_epochs,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "per_device_eval_batch_size": config.per_device_eval_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "effective_train_batch_size": config.per_device_train_batch_size * config.gradient_accumulation_steps,
        "warmup_steps": config.warmup_steps,
        "learning_rate": config.learning_rate,
        "weight_decay": config.weight_decay,
        "max_seq_length": config.max_seq_length,
        "gradient_checkpointing": config.gradient_checkpointing,
        "optim": config.optim,
        "use_4bit": config.use_4bit,
    }

# 配置参数
class Config:
    # 测试模式（快速验证）
    test_mode = _env_bool("LORA_TEST_MODE", True)  # 设置为True进行快速测试
    device = os.environ.get("LORA_DEVICE", os.environ.get("TBLLM_DEVICE", "auto")).strip().lower()
    model_dtype = os.environ.get("LORA_MODEL_DTYPE", "float16").strip().lower()

    # 模型路径
    base_model_path = _env_path("LORA_BASE_MODEL_PATH", "models/Qwen1.5-1.8B-Chat")
    output_model_path = _env_path("LORA_OUTPUT_MODEL_PATH", "models/Qwen1.5-1.8B-Chat-finetuned")
    checkpoint_dir = _env_path("LORA_CHECKPOINT_DIR", "lora_checkpoints")
    lora_output_path = _env_path("LORA_OUTPUT_PATH", "lora_weights")

    # 数据路径 - 问卷数据集
    train_data_path = _env_path("LORA_TRAIN_DATA_PATH", "datasets/questionnaire_dialogue_train.json")
    val_data_path = _env_path("LORA_VAL_DATA_PATH", "datasets/questionnaire_dialogue_val.json")

    # LoRA配置
    lora_r = _env_int("LORA_R", 16)  # LoRA秩
    lora_alpha = _env_int("LORA_ALPHA", 32)  # LoRA alpha参数
    lora_dropout = _env_float("LORA_DROPOUT", 0.1)
    lora_target_modules = _env_list(
        "LORA_TARGET_MODULES",
        ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    # 训练参数 - 根据测试模式调整
    if test_mode:
        num_train_epochs = _env_float("LORA_NUM_TRAIN_EPOCHS", 0.01)  # 非常小的epoch进行快速测试
        per_device_train_batch_size = _env_int("LORA_TRAIN_BATCH_SIZE", 1)
        per_device_eval_batch_size = _env_int("LORA_EVAL_BATCH_SIZE", 1)
        gradient_accumulation_steps = _env_int("LORA_GRAD_ACCUM_STEPS", 16)
        warmup_steps = _env_int("LORA_WARMUP_STEPS", 10)
        learning_rate = _env_float("LORA_LEARNING_RATE", 2e-4)
        logging_steps = _env_int("LORA_LOGGING_STEPS", 5)
        save_steps = _env_int("LORA_SAVE_STEPS", 20)
        eval_steps = _env_int("LORA_EVAL_STEPS", 20)
        save_total_limit = _env_int("LORA_SAVE_TOTAL_LIMIT", 1)
        max_steps = _env_optional_int("LORA_MAX_STEPS", 20)
    else:
        num_train_epochs = _env_float("LORA_NUM_TRAIN_EPOCHS", 3)
        per_device_train_batch_size = _env_int("LORA_TRAIN_BATCH_SIZE", 2)
        per_device_eval_batch_size = _env_int("LORA_EVAL_BATCH_SIZE", 2)
        gradient_accumulation_steps = _env_int("LORA_GRAD_ACCUM_STEPS", 8)
        warmup_steps = _env_int("LORA_WARMUP_STEPS", 100)
        learning_rate = _env_float("LORA_LEARNING_RATE", 2e-4)
        logging_steps = _env_int("LORA_LOGGING_STEPS", 10)
        save_steps = _env_int("LORA_SAVE_STEPS", 500)
        eval_steps = _env_int("LORA_EVAL_STEPS", 500)
        save_total_limit = _env_int("LORA_SAVE_TOTAL_LIMIT", 3)
        max_steps = _env_optional_int("LORA_MAX_STEPS", None)

    weight_decay = _env_float("LORA_WEIGHT_DECAY", 0.01)
    fp16 = _env_bool("LORA_TRAINER_FP16", True)  # CUDA AMP；macOS MPS脚本会关闭
    bf16 = _env_bool("LORA_TRAINER_BF16", False)

    # 优化器
    optim = os.environ.get("LORA_OPTIM", "adamw_torch")

    # 序列长度 - 根据问卷数据调整，降低以减少显存
    max_seq_length = _env_int("LORA_MAX_SEQ_LENGTH", 1024)

    # 其他
    gradient_checkpointing = _env_bool("LORA_GRADIENT_CHECKPOINTING", True)
    report_to = os.environ.get("LORA_REPORT_TO", "none")
    # 量化配置
    use_4bit = _env_bool("LORA_USE_4BIT", True)
    gpu_max_memory = os.environ.get("LORA_GPU_MAX_MEMORY", "3GB")
    cpu_max_memory = os.environ.get("LORA_CPU_MAX_MEMORY", "10GB")

def load_dataset(file_path):
    """加载JSON格式的数据集，支持system/human/assistant角色"""
    logger.info(f"加载数据集: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"数据集大小: {len(data)} 条样本")

    # 转换为消息列表
    messages_list = []
    for item in data:
        conversations = item['conversations']
        # 转换为标准消息格式
        messages = []
        for turn in conversations:
            role = turn['from']
            content = turn['value']

            # 映射角色名称
            if role == 'human':
                role = 'user'
            elif role == 'assistant':
                role = 'assistant'
            elif role == 'system':
                role = 'system'
            # 其他角色保持不变

            messages.append({"role": role, "content": content})

        messages_list.append(messages)

    # 创建Dataset对象
    dataset = Dataset.from_dict({"messages": messages_list})
    return dataset

def format_conversation(conversations):
    """将对话格式化为Qwen1.5的ChatML格式，支持system角色"""
    # 转换角色名称
    messages = []
    for turn in conversations:
        role = turn['from']
        content = turn['value']

        if role == 'human':
            role = 'user'
        elif role == 'assistant':
            role = 'assistant'
        elif role == 'system':
            role = 'system'

        messages.append({"role": role, "content": content})

    # 使用tokenizer的apply_chat_template方法（将在外部调用）
    # 这里只返回消息列表，让tokenizer处理格式化
    return messages

def tokenize_function(examples, tokenizer, max_length):
    """对消息进行分词"""
    # 使用apply_chat_template格式化对话
    texts = []
    for messages in examples["messages"]:
        # 应用聊天模板
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,  # 不在这里分词
            add_generation_prompt=False  # 不在末尾添加助手提示
        )
        texts.append(text)

    # 分词
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding=False,
        return_tensors=None  # 返回Python列表
    )

    # 添加labels字段（用于因果语言建模）
    tokenized["labels"] = tokenized["input_ids"].copy()

    return tokenized

def print_trainable_parameters(model):
    """打印可训练参数数量"""
    trainable_params = 0
    all_params = 0
    for _, param in model.named_parameters():
        all_params += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()

    logger.info(f"可训练参数: {trainable_params:,} / 总参数: {all_params:,} ({100 * trainable_params / all_params:.2f}%)")

def tokenize_fn(examples):
    return tokenize_function(examples, GLOBAL_TOKENIZER, GLOBAL_MAX_LENGTH)

def main():
    logger.info("=" * 60)
    logger.info("开始LoRA微调")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    config = Config()
    torch.set_float32_matmul_precision(os.environ.get("LORA_MATMUL_PRECISION", "high"))

    use_cuda = torch.cuda.is_available()
    use_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    requested_device = config.device

    if requested_device == "cuda" and not use_cuda:
        logger.error("已请求CUDA训练，但CUDA不可用")
        sys.exit(1)
    if requested_device == "mps" and not use_mps:
        logger.error("已请求MPS训练，但当前PyTorch未检测到Apple Silicon MPS")
        sys.exit(1)

    if requested_device == "cuda" or (requested_device == "auto" and use_cuda):
        device = "cuda"
    elif requested_device == "mps" or (requested_device == "auto" and use_mps):
        device = "mps"
    else:
        device = "cpu"

    logger.info(f"训练设备: {device}")
    if device == "cuda":
        logger.info(f"CUDA设备: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        logger.info(f"PYTORCH_CUDA_ALLOC_CONF={os.environ.get('PYTORCH_CUDA_ALLOC_CONF')}")
    elif device == "mps":
        logger.info("Apple Silicon MPS训练模式：禁用bitsandbytes 4-bit量化，使用统一内存")
        logger.info(f"PYTORCH_MPS_HIGH_WATERMARK_RATIO={os.environ.get('PYTORCH_MPS_HIGH_WATERMARK_RATIO', 'default')}")
        logger.info(f"PYTORCH_MPS_LOW_WATERMARK_RATIO={os.environ.get('PYTORCH_MPS_LOW_WATERMARK_RATIO', 'default')}")
    else:
        logger.warning("未检测到CUDA/MPS，将使用CPU训练，速度会很慢")

    if device != "cuda" and (config.fp16 or config.bf16):
        logger.warning("Trainer混合精度主要面向CUDA，当前设备将关闭fp16/bf16训练参数")
        config.fp16 = False
        config.bf16 = False

    logger.info(
        "训练配置: "
        f"test_mode={config.test_mode}, dtype={config.model_dtype}, "
        f"seq_len={config.max_seq_length}, batch={config.per_device_train_batch_size}, "
        f"grad_accum={config.gradient_accumulation_steps}, lr={config.learning_rate}, "
        f"epochs={config.num_train_epochs}, max_steps={config.max_steps}"
    )
    logger.info(f"LoRA输出目录: {config.lora_output_path}")
    logger.info(f"检查点目录: {config.checkpoint_dir}")

    # 步骤1: 加载分词器
    logger.info(f"加载分词器: {config.base_model_path}")
    tokenizer = AutoTokenizer.from_pretrained(
        config.base_model_path,
        trust_remote_code=True,
        padding_side="right"  # 注意：对于生成任务，padding应该在右侧
    )

    # 设置pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 步骤2: 加载模型
    logger.info(f"加载基础模型: {config.base_model_path}")

    # 配置模型加载
    model_dtype = _torch_dtype(config.model_dtype)
    model_kwargs = {
        "torch_dtype": model_dtype,
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
    }

    if device == "cuda":
        model_kwargs["device_map"] = "auto"
    elif device == "cpu":
        model_kwargs["device_map"] = "cpu"

    # 如果启用梯度检查点，需要在加载前设置
    if config.gradient_checkpointing:
        model_kwargs["use_cache"] = False

    # 量化配置以节省显存；bitsandbytes仅适用于CUDA，macOS MPS不可用。
    using_kbit = device == "cuda" and config.use_4bit
    if using_kbit:
        # 使用4位量化，显著减少显存占用
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=model_dtype,
            bnb_4bit_use_double_quant=True,  # 双重量化进一步节省内存
            bnb_4bit_quant_type="nf4",  # 4位量化类型
        )
        model_kwargs["quantization_config"] = bnb_config
        # 设置内存映射
        model_kwargs["max_memory"] = {0: config.gpu_max_memory, "cpu": config.cpu_max_memory}
        logger.info(f"已启用4位量化以节省显存，GPU内存限制: {config.gpu_max_memory}")
    else:
        logger.info("未启用4位量化，使用标准加载")

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_path,
        **model_kwargs
    )

    if device == "mps":
        model = model.to("mps")
    elif device == "cpu":
        model = model.to("cpu")

    if device == "cuda":
        torch.cuda.empty_cache()
        logger.info("已清理CUDA缓存")
    elif device == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
        torch.mps.empty_cache()
        logger.info("已清理MPS缓存")

    # 步骤3: 配置LoRA
    logger.info("配置LoRA...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.lora_target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False
    )

    if using_kbit:
        model = prepare_model_for_kbit_training(model)

    # 应用LoRA
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()
    # 打印可训练参数
    print_trainable_parameters(model)

    # 启用梯度检查点（如果配置）
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        logger.info("已启用梯度检查点")

    # 步骤4: 加载数据集
    logger.info("加载训练和验证数据集...")
    train_dataset = load_dataset(config.train_data_path)
    val_dataset = load_dataset(config.val_data_path)

    # 对数据集进行分词
    logger.info(f"对数据集进行分词，最大长度: {config.max_seq_length}")

    global GLOBAL_TOKENIZER, GLOBAL_MAX_LENGTH
    GLOBAL_TOKENIZER = tokenizer
    GLOBAL_MAX_LENGTH = config.max_seq_length

    tokenized_train = train_dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=train_dataset.column_names,
        desc="分词训练集"
    )

    tokenized_val = val_dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=val_dataset.column_names,
        desc="分词验证集"
    )

    logger.info(f"分词后训练集大小: {len(tokenized_train)}")
    logger.info(f"分词后验证集大小: {len(tokenized_val)}")

    # 步骤5: 配置数据整理器
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        pad_to_multiple_of=8 if model_dtype in {torch.float16, torch.bfloat16} else None
    )

    # 步骤6: 配置训练参数
    training_args_kwargs = {
        "output_dir": config.checkpoint_dir,
        "overwrite_output_dir": True,
        "num_train_epochs": config.num_train_epochs,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "per_device_eval_batch_size": config.per_device_eval_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "warmup_steps": config.warmup_steps,
        "learning_rate": config.learning_rate,
        "weight_decay": config.weight_decay,
        "fp16": config.fp16,
        "bf16": config.bf16,
        "optim": config.optim,
        "logging_steps": config.logging_steps,
        "save_steps": config.save_steps,
        "eval_steps": config.eval_steps,
        "eval_strategy": "steps",
        "save_strategy": "steps",
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_loss",
        "greater_is_better": False,
        "save_total_limit": config.save_total_limit,
        "gradient_checkpointing": config.gradient_checkpointing,
        "report_to": config.report_to,
        "ddp_find_unused_parameters": False,
        "remove_unused_columns": False,
        "group_by_length": False,  # 不按长度分组，因为我们的样本长度相近
        "dataloader_num_workers": 0,
        "dataloader_pin_memory": device == "cuda",
    }

    # 如果配置了max_steps，则添加
    if hasattr(config, 'max_steps') and config.max_steps is not None:
        training_args_kwargs["max_steps"] = config.max_steps

    training_args = TrainingArguments(**training_args_kwargs)

    # 步骤7: 创建Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator,
        processing_class=tokenizer,
    )

    # 步骤8: 开始训练
    logger.info("开始训练...")
    train_result = trainer.train()

    # 步骤9: 保存最终模型
    logger.info("训练完成，保存模型...")

    # 保存LoRA权重
    os.makedirs(config.lora_output_path, exist_ok=True)
    model.save_pretrained(config.lora_output_path)
    tokenizer.save_pretrained(config.lora_output_path)
    logger.info(f"LoRA权重已保存到: {config.lora_output_path}")

    # 步骤10: 记录训练统计
    logger.info("记录训练统计...")
    metrics = train_result.metrics
    metrics["train_samples"] = len(tokenized_train)
    metrics["val_samples"] = len(tokenized_val)
    metrics["train_time"] = train_result.metrics.get("train_runtime", 0)

    # 保存训练统计
    os.makedirs(config.output_model_path, exist_ok=True)
    stats_path = os.path.join(config.output_model_path, "training_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"训练统计已保存到: {stats_path}")

    profile_path = os.path.join(config.lora_output_path, "training_profile.json")
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(_config_snapshot(config, device), f, ensure_ascii=False, indent=2)
    logger.info(f"训练配置快照已保存到: {profile_path}")

    logger.info("=" * 60)
    logger.info("LoRA微调完成!")
    logger.info(f"LoRA适配器已保存到: {config.lora_output_path}")
    logger.info(f"训练统计目录: {config.output_model_path}")
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"训练过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
