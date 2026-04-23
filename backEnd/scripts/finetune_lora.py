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

# 配置参数
class Config:
    # 测试模式（快速验证）
    test_mode = True  # 设置为True进行快速测试

    # 模型路径
    base_model_path = "models/Qwen1.5-1.8B-Chat"
    output_model_path = "models/Qwen1.5-1.8B-Chat-finetuned"

    # 数据路径 - 问卷数据集
    train_data_path = "datasets/questionnaire_dialogue_train.json"
    val_data_path = "datasets/questionnaire_dialogue_val.json"

    # LoRA配置
    lora_r = 16  # LoRA秩
    lora_alpha = 32  # LoRA alpha参数
    lora_dropout = 0.1
    lora_target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

    # 训练参数 - 根据测试模式调整
    if test_mode:
        num_train_epochs = 0.01  # 非常小的epoch进行快速测试
        per_device_train_batch_size = 1  # 更小的批大小以适应4GB GPU
        per_device_eval_batch_size = 1
        gradient_accumulation_steps = 16  # 有效批大小 = 1 * 16 = 16，减少显存峰值
        warmup_steps = 10
        learning_rate = 2e-4
        logging_steps = 5
        save_steps = 20
        eval_steps = 20
        save_total_limit = 1
        max_steps = 20  # 最大训练步数
    else:
        num_train_epochs = 3  # 完整训练3个epoch
        per_device_train_batch_size = 2  # 根据4GB GPU内存调整
        per_device_eval_batch_size = 2
        gradient_accumulation_steps = 8  # 有效批大小 = 2 * 8 = 16
        warmup_steps = 100
        learning_rate = 2e-4
        logging_steps = 10
        save_steps = 500
        eval_steps = 500
        save_total_limit = 3
        max_steps = None  # 不使用max_steps

    weight_decay = 0.01
    fp16 = True  # 使用半精度
    bf16 = False  # 如果GPU支持BF16可以开启

    # 优化器
    optim = "adamw_torch"

    # 序列长度 - 根据问卷数据调整，降低以减少显存
    max_seq_length = 1024

    # 其他
    gradient_checkpointing = True  # 节省显存
    report_to = "none"  # 不报告到wandb等
    # 量化配置
    use_4bit = True  # 使用4位量化
    gpu_max_memory = "3GB"  # GPU最大内存限制
    cpu_max_memory = "10GB"  # CPU最大内存限制

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

    # 检查CUDA是否可用
    if not torch.cuda.is_available():
        logger.error("CUDA不可用，请检查GPU环境")
        sys.exit(1)

    logger.info(f"CUDA可用，设备: {torch.cuda.get_device_name(0)}")
    logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

    # 设置CUDA内存分配配置以减少碎片
    import os
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    logger.info("已设置PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True")

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
    model_kwargs = {
        "dtype": torch.float16 if config.fp16 else torch.float32,
        "device_map": "auto",  # 自动设备映射，支持CPU卸载
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
    }

    # 如果启用梯度检查点，需要在加载前设置
    if config.gradient_checkpointing:
        model_kwargs["use_cache"] = False

    # 量化配置以节省显存 (仅当CUDA可用时)
    if torch.cuda.is_available() and config.use_4bit:
        # 使用4位量化，显著减少显存占用
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16 if config.fp16 else torch.float32,
            bnb_4bit_use_double_quant=True,  # 双重量化进一步节省内存
            bnb_4bit_quant_type="nf4",  # 4位量化类型
        )
        model_kwargs["quantization_config"] = bnb_config
        # 设置内存映射
        model_kwargs["max_memory"] = {0: config.gpu_max_memory, "cpu": config.cpu_max_memory}
        logger.info(f"已启用4位量化以节省显存，GPU内存限制: {config.gpu_max_memory}")
    else:
        logger.info("未启用量化，使用标准加载")

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_path,
        **model_kwargs
    )

    # 清理CUDA缓存
    torch.cuda.empty_cache()
    logger.info("已清理CUDA缓存")

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

    # 准备模型用于k-bit训练（即使不使用量化也建议调用）
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
        pad_to_multiple_of=8 if config.fp16 else None
    )

    # 步骤6: 配置训练参数
    training_args_kwargs = {
        "output_dir": "./lora_checkpoints",  # 检查点目录
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
        "dataloader_num_workers": 0,  # Windows上可能需要设为0
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
    lora_output_path = os.path.join(PROJECT_ROOT, "lora_weights")
    model.save_pretrained(lora_output_path)
    logger.info(f"LoRA权重已保存到: {lora_output_path}")

    # 步骤10: 记录训练统计
    logger.info("记录训练统计...")
    metrics = train_result.metrics
    metrics["train_samples"] = len(tokenized_train)
    metrics["val_samples"] = len(tokenized_val)
    metrics["train_time"] = train_result.metrics.get("train_runtime", 0)

    # 保存训练统计
    stats_path = os.path.join(config.output_model_path, "training_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"训练统计已保存到: {stats_path}")

    logger.info("=" * 60)
    logger.info("LoRA微调完成!")
    logger.info(f"模型已保存到: {config.output_model_path}")
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