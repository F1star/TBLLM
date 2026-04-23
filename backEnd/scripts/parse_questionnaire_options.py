#!/usr/bin/env python3
"""
从问卷Markdown文件中解析问题选项
"""

import re
import json
import sys
import os
from collections import defaultdict

def parse_markdown_file(file_path, cohort_type):
    """
    解析问卷Markdown文件，提取问题ID和选项

    参数：
        file_path: Markdown文件路径
        cohort_type: 'younger' 或 'elderly'

    返回：
        question_options: 字典 {question_id: {1: "选项1", 2: "选项2", ...}}
    """
    print(f"解析文件: {file_path} (组别: {cohort_type})")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    question_options = {}

    # 分割章节（如果有）
    sections = content.split('---')

    for section in sections:
        # 查找问题模式：**问题文本** 后跟问题ID
        lines = section.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 查找以**开头的问题文本行
            if line.startswith('**') and '**' in line[2:]:
                # 提取问题文本
                question_text = line.strip('*').strip()

                # 下一行可能是问题ID
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()

                    # 问题ID行：如 "COGM00101" 或 "STQM00101"
                    if re.match(r'^(STQM|COGM)\d+[A-Z]?S?$', next_line):
                        question_id = next_line

                        # 收集选项
                        options = {}
                        option_num = 1

                        j = i + 2
                        while j < len(lines):
                            option_line = lines[j].strip()

                            # 选项以"○ "开头
                            if option_line.startswith('○ '):
                                option_text = option_line[2:].strip()
                                options[option_num] = option_text
                                option_num += 1
                                j += 1
                            else:
                                # 不是选项行，结束选项收集
                                break

                        if options:
                            question_options[question_id] = options
                            print(f"  找到问题: {question_id} - {len(options)} 个选项")

                        i = j  # 跳过已处理的行
                        continue
            i += 1

    print(f"总共找到 {len(question_options)} 个问题的选项")

    # 显示一些示例
    print("\n选项示例:")
    for i, (qid, opts) in enumerate(list(question_options.items())[:5]):
        print(f"  {qid}:")
        for val, text in list(opts.items())[:3]:
            print(f"    {val}: {text}")
        if len(opts) > 3:
            print(f"    ... 共 {len(opts)} 个选项")

    return question_options

def combine_options_from_both_files():
    """从两个问卷文件中合并选项"""

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    docs_dir = os.path.join(base_dir, 'docs', 'rag')

    younger_file = os.path.join(docs_dir, 'query_younger.md')
    elderly_file = os.path.join(docs_dir, 'query_elderly.md')

    younger_options = parse_markdown_file(younger_file, 'younger')
    elderly_options = parse_markdown_file(elderly_file, 'elderly')

    # 合并选项（年长组可能包含年轻组没有的问题）
    all_options = younger_options.copy()
    all_options.update(elderly_options)  # 年长组覆盖相同问题ID

    print(f"\n合并后总问题数: {len(all_options)}")

    # 检查COGM系列问题
    cogm_questions = {qid: opts for qid, opts in all_options.items() if qid.startswith('COGM')}
    print(f"COGM问题数: {len(cogm_questions)}")

    # 检查STQM系列问题
    stqm_questions = {qid: opts for qid, opts in all_options.items() if qid.startswith('STQM')}
    print(f"STQM问题数: {len(stqm_questions)}")

    return all_options

def check_database_questions(all_options):
    """检查数据库中的问题，查看哪些有选项缺失"""

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backEnd'))

    from config.settings import app, db
    from db_models import QuestionnaireQuestion

    with app.app_context():
        # 获取所有问题
        all_questions = QuestionnaireQuestion.query.all()
        print(f"\n数据库中的问题总数: {len(all_questions)}")

        # 检查哪些问题有完整选项，哪些只有特殊值
        questions_with_full_options = []
        questions_with_only_special = []
        questions_no_options = []

        for q in all_questions:
            qid = q.question_id

            # 解析当前options_json
            current_options = {}
            if q.options_json:
                try:
                    current_options = json.loads(q.options_json)
                except json.JSONDecodeError:
                    current_options = {}

            # 检查是否只有特殊值
            special_keys = [str(k) for k in [97.0, 98.0, 99.0, '97.0', '98.0', '99.0']]
            has_special_only = all(str(k) in special_keys for k in current_options.keys())

            # 从Markdown文件中获取的选项
            markdown_options = all_options.get(qid, {})

            if markdown_options:
                if has_special_only and len(current_options) <= 3:
                    questions_with_only_special.append((qid, current_options, markdown_options))
                else:
                    questions_with_full_options.append((qid, current_options, markdown_options))
            else:
                questions_no_options.append(qid)

        print(f"\n选项分析:")
        print(f"  有完整选项的问题: {len(questions_with_full_options)}")
        print(f"  只有特殊值选项的问题: {len(questions_with_only_special)}")
        print(f"  Markdown中无对应选项的问题: {len(questions_no_options)}")

        # 显示一些示例
        if questions_with_only_special:
            print(f"\n只有特殊值选项的问题示例 (前5个):")
            for qid, current_opts, markdown_opts in questions_with_only_special[:5]:
                print(f"  {qid}:")
                print(f"    当前选项: {current_opts}")
                print(f"    Markdown选项数: {len(markdown_opts)}")
                print(f"    前3个选项: {dict(list(markdown_opts.items())[:3])}")

        if questions_no_options:
            print(f"\nMarkdown中无对应选项的问题示例 (前10个):")
            print(questions_no_options[:10])

        return questions_with_only_special, questions_with_full_options, questions_no_options

def main():
    """主函数"""
    print("=" * 60)
    print("问卷选项解析工具")
    print("=" * 60)

    # 步骤1: 从Markdown文件中解析选项
    all_options = combine_options_from_both_files()

    # 保存到JSON文件供参考
    output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'question_options.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_options, f, ensure_ascii=False, indent=2)
    print(f"\n选项已保存到: {output_file}")

    # 步骤2: 检查数据库中的问题
    questions_with_only_special, questions_with_full_options, questions_no_options = check_database_questions(all_options)

    print("\n" + "=" * 60)
    print("解析完成!")
    print("=" * 60)

    # 建议下一步操作
    if questions_with_only_special:
        print(f"\n建议: 需要更新 {len(questions_with_only_special)} 个问题的选项")
        print("      这些问题的options_json只包含特殊值，需要添加实际选项")

    return all_options

if __name__ == '__main__':
    main()