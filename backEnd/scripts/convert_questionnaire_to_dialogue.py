#!/usr/bin/env python3
"""
将questionnaire_finetuning_full.jsonl转换为对话格式，供finetune_lora.py使用

输入格式: instruction/input/output格式
输出格式: conversations格式，包含human/assistant角色

转换逻辑:
- human角色: instruction + "\n\n" + input
- assistant角色: output
- 保留metadata信息
"""

import json
import os
import sys
from pathlib import Path
import random

def load_jsonl_file(file_path):
    """加载JSONL文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line.strip()))
    return data

def convert_to_conversations(data):
    """将instruction/input/output格式转换为conversations格式"""
    converted_data = []

    for item in data:
        # 构建conversations列表
        conversations = [
            {
                "from": "human",
                "value": f"{item['instruction']}\n\n{item['input']}"
            },
            {
                "from": "assistant",
                "value": item['output']
            }
        ]

        # 构建新条目
        new_item = {
            "id": item.get("id", ""),
            "conversations": conversations,
            "metadata": item.get("metadata", {})
        }

        converted_data.append(new_item)

    return converted_data

def split_dataset(data, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42):
    """划分数据集为训练集、验证集和测试集"""
    assert train_ratio + val_ratio + test_ratio == 1.0, "比例总和必须为1.0"

    # 打乱数据
    random.seed(seed)
    shuffled_data = data.copy()
    random.shuffle(shuffled_data)

    n = len(shuffled_data)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train_data = shuffled_data[:train_end]
    val_data = shuffled_data[train_end:val_end]
    test_data = shuffled_data[val_end:]

    return train_data, val_data, test_data

def save_json_file(data, file_path):
    """保存为JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 项目根目录
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

    # 配置路径
    input_file = PROJECT_ROOT / "datasets" / "questionnaire_finetuning_full.jsonl"
    output_dir = PROJECT_ROOT / "datasets"

    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)

    # 输出文件路径
    train_file = output_dir / "questionnaire_dialogue_train.json"
    val_file = output_dir / "questionnaire_dialogue_val.json"
    test_file = output_dir / "questionnaire_dialogue_test.json"

    print(f"加载数据集: {input_file}")

    # 加载原始数据
    try:
        raw_data = load_jsonl_file(input_file)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        print(f"当前工作目录: {os.getcwd()}")
        sys.exit(1)

    print(f"加载了 {len(raw_data)} 条样本")

    # 转换为对话格式
    print("转换为对话格式...")
    converted_data = convert_to_conversations(raw_data)

    # 检查转换结果
    if len(converted_data) == 0:
        print("错误: 转换后数据为空")
        sys.exit(1)

    # 检查第一条样本的格式
    sample = converted_data[0]
    print(f"\n第一条样本预览:")
    print(f"ID: {sample['id']}")
    print(f"对话轮数: {len(sample['conversations'])}")
    print(f"第一轮角色: {sample['conversations'][0]['from']}")
    print(f"第一轮内容长度: {len(sample['conversations'][0]['value'])} 字符")
    print(f"第二轮角色: {sample['conversations'][1]['from']}")
    print(f"第二轮内容长度: {len(sample['conversations'][1]['value'])} 字符")

    # 划分数据集
    print(f"\n划分数据集 (训练集80%, 验证集10%, 测试集10%)...")
    train_data, val_data, test_data = split_dataset(
        converted_data,
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1
    )

    print(f"训练集: {len(train_data)} 条样本")
    print(f"验证集: {len(val_data)} 条样本")
    print(f"测试集: {len(test_data)} 条样本")

    # 保存数据集
    print(f"\n保存数据集...")
    save_json_file(train_data, train_file)
    save_json_file(val_data, val_file)
    save_json_file(test_data, test_file)

    print(f"训练集已保存到: {train_file}")
    print(f"验证集已保存到: {val_file}")
    print(f"测试集已保存到: {test_file}")

    # 创建统计信息
    stats = {
        "total_samples": len(converted_data),
        "train_samples": len(train_data),
        "val_samples": len(val_data),
        "test_samples": len(test_data),
        "train_ratio": 0.8,
        "val_ratio": 0.1,
        "test_ratio": 0.1,
        "conversion_date": "2026-04-20"
    }

    stats_file = output_dir / "questionnaire_dialogue_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n统计信息已保存到: {stats_file}")
    print(f"\n转换完成!")

if __name__ == "__main__":
    main()