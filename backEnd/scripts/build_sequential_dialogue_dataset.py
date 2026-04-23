#!/usr/bin/env python3
"""
构建逐题问答对话数据集
基于问卷顺序文件和学生回答数据，为每个学生构建逐题问答对话序列，
并在对话末尾添加技能评估总结。

输入：
1. question_order_elderly.json, question_order_younger.json (问题顺序)
2. 数据库中的学生回答 (StudentResponse)
3. SPSS文件中的技能评分 (WLE_Adj分数)

输出：
逐题问答对话数据集，格式为：
{
  "id": "student_[FullID]_[cohort]",
  "conversations": [
    {"from": "system", "value": "开场白..."},
    {"from": "assistant", "value": "问题1文本"},
    {"from": "human", "value": "回答1文本"},
    {"from": "system", "value": "问题2文本"},
    {"from": "human", "value": "回答2文本"},
    ...
    {"from": "system", "value": "技能评估总结..."}
  ],
  "metadata": {
    "student_id": "FullID",
    "cohort": "younger/elderly",
    "num_questions": 50,
    "skill_scores": {"ASS": 75.5, "COO": 62.3, ...}
  }
}
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import pyreadstat
from pathlib import Path
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# 项目根目录 (backEnd/scripts/../../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 添加项目根目录和backEnd目录到路径
sys.path.insert(0, str(PROJECT_ROOT / "backEnd"))
sys.path.insert(0, str(PROJECT_ROOT))

# 避免Flask应用依赖，直接使用sqlite3连接
import sqlite3

# 数据库文件路径
db_path = str(PROJECT_ROOT / "backEnd" / "instance" / "users.db")

# 创建数据库连接
def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 返回字典样式的行
    return conn

# 配置文件路径
# 项目根目录已在前面定义为 PROJECT_ROOT
SPSS_FILE = PROJECT_ROOT / "docs" / "rag" / "INT_01_ST_(2021.04.14)_Public.sav"
QUESTION_ORDER_DIR = PROJECT_ROOT / "backEnd" / "finetuning_data"

# 技能代码到中文名称映射（基于score.md）
SKILL_MAPPING = {
    'ASS': '自信/主张',
    'COO': '合作',
    'CRE': '创造力',
    'CUR': '好奇心',
    'EMO': '情绪控制',
    'EMP': '同理心',
    'ENE': '活力',
    'OPT': '乐观',
    'PER': '坚持',
    'RES': '责任感',
    'SEL': '自我控制',
    'SOC': '社交能力',
    'STR': '抗压能力',
    'TOL': '包容',
    'TRU': '信任',
    # 复合技能（可能没有WLE_Adj分数）
    'EFF': '自我效能',
    'MOT': '成就动机'
}

# 翻译函数
# 加载本地选项映射
def load_option_mappings():
    """加载问题选项映射文件"""
    option_mapping_path = PROJECT_ROOT / "question_options.json"
    if not option_mapping_path.exists():
        print(f"警告: 选项映射文件不存在: {option_mapping_path}")
        return {}

    try:
        with open(option_mapping_path, 'r', encoding='utf-8') as f:
            option_mappings = json.load(f)
        print(f"加载选项映射: {len(option_mappings)} 个问题")
        return option_mappings
    except Exception as e:
        print(f"警告: 加载选项映射文件失败: {e}")
        return {}

# 本地选项映射缓存
_option_mappings = None

def get_option_mappings():
    """获取选项映射（单例）"""
    global _option_mappings
    if _option_mappings is None:
        _option_mappings = load_option_mappings()
    return _option_mappings

# 常见英文短语到中文的内置映射
COMMON_TRANSLATIONS = {
    # 通用术语
    'yes': '是',
    'no': '否',
    'true': '真',
    'false': '假',
    'male': '男',
    'female': '女',
    'other': '其他',
    'not applicable': '不适用',
    'missing': '缺失',
    'omitted': '省略',
    'n/a': '不适用',
    'none': '无',
    'unknown': '未知',
    'don\'t know': '不知道',
    'prefer not to say': '不愿回答',
    # 问卷常见选项
    'strongly disagree': '非常不同意',
    'disagree': '不同意',
    'agree': '同意',
    'strongly agree': '非常同意',
    'never': '从不',
    'rarely': '很少',
    'sometimes': '有时',
    'often': '经常',
    'always': '总是',
    'very poor': '非常差',
    'poor': '差',
    'fair': '一般',
    'good': '好',
    'very good': '非常好',
    'excellent': '优秀',
    # 数字选项
    'zero': '零',
    'one': '一',
    'two': '二',
    'three': '三',
    'four': '四',
    'five': '五',
    'six': '六',
    'seven': '七',
    'eight': '八',
    'nine': '九',
    'ten': '十',
    # 从数据库中提取的常见回答
    'one': '一',
    'three or more': '三个或更多',
    'assessment language': '评估语言',
    'most of the time': '大部分时间',
    'some of the time': '有时',
    'all of the time': '所有时间',
    'more than half of the time': '超过一半时间',
    'excellent': '优秀',
    'very safe': '非常安全',
    'i have never heard of this': '我从未听说过这个',
    'i know something about it': '我对此有所了解',
    'i know a lot about this': '我对此很了解',
    'i know little about this': '我对此知之甚少',
    'very close': '非常亲近',
    'almost always or always true': '几乎总是或总是如此',
    'often true': '经常如此',
    'sometimes true': '有时如此',
    # 常见问卷问题开头
    'how do you feel about': '你对...感觉如何',
    'how often do you': '你多久...一次',
    'how many': '多少',
    'how much': '多少',
    'what is your': '你的...是什么',
    'in the past year': '在过去的一年里',
    'at school': '在学校',
    'with friends': '与朋友一起',
    'with family': '与家人一起',
    # 技能相关术语
    'confidence': '自信',
    'cooperation': '合作',
    'creativity': '创造力',
    'curiosity': '好奇心',
    'emotional control': '情绪控制',
    'empathy': '同理心',
    'energy': '活力',
    'optimism': '乐观',
    'persistence': '坚持',
    'responsibility': '责任感',
    'self-control': '自我控制',
    'social skills': '社交能力',
    'stress tolerance': '抗压能力',
    'tolerance': '包容',
    'trust': '信任',
    'self-efficacy': '自我效能',
    'achievement motivation': '成就动机',
}

# 翻译缓存
TRANSLATION_CACHE_FILE = PROJECT_ROOT / "backEnd" / "finetuning_data" / "translation_cache.json"
_translation_cache = {}

def load_translation_cache():
    """加载翻译缓存"""
    global _translation_cache
    if TRANSLATION_CACHE_FILE.exists():
        try:
            with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                _translation_cache = json.load(f)
            print(f"加载翻译缓存: {len(_translation_cache)} 条记录")
        except Exception as e:
            print(f"警告: 加载翻译缓存失败: {e}")
            _translation_cache = {}
    else:
        _translation_cache = {}

def save_translation_cache():
    """保存翻译缓存"""
    try:
        # 确保目录存在
        TRANSLATION_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRANSLATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_translation_cache, f, ensure_ascii=False, indent=2)
        if DEBUG_TRANSLATION:
            print(f"保存翻译缓存: {len(_translation_cache)} 条记录")
    except Exception as e:
        print(f"警告: 保存翻译缓存失败: {e}")

def get_cache_key(text, question_id=None):
    """生成缓存键"""
    if question_id:
        return f"{question_id}:{text.strip().lower()}"
    return text.strip().lower()

def cache_translation(text, translation, question_id=None):
    """缓存翻译结果"""
    key = get_cache_key(text, question_id)
    _translation_cache[key] = translation
    # 定期保存缓存（每100条保存一次）
    if len(_translation_cache) % 100 == 0:
        save_translation_cache()

def get_cached_translation(text, question_id=None):
    """获取缓存的翻译结果"""
    key = get_cache_key(text, question_id)
    return _translation_cache.get(key)

def translate_to_chinese(text, question_id=None):
    """
    将英文文本翻译成中文，优先使用国内可用的翻译服务

    翻译服务优先级：
    1. 检查缓存
    2. 本地选项映射（如果有对应question_id和选项值）
    3. 内置常见术语映射
    4. translators库的国内服务（baidu, youdao, caiyun等）
    5. 原始文本（如果都不可用）
    """
    if not text or not isinstance(text, str):
        return text

    # 去除首尾空格
    text = text.strip()
    if not text:
        return text

    if DEBUG_TRANSLATION:
        print(f"翻译调试: 开始翻译文本 '{text}' (question_id: {question_id})")

    # 初始化缓存
    global _translation_cache
    if not _translation_cache:
        load_translation_cache()

    # 检查缓存
    cached = get_cached_translation(text, question_id)
    if cached is not None:
        if DEBUG_TRANSLATION:
            print(f"翻译调试: 缓存命中 '{text}' -> '{cached}'")
        return cached

    # 如果已经是中文，直接返回并缓存
    if any('\u4e00' <= ch <= '\u9fff' for ch in text):
        cache_translation(text, text, question_id)
        return text

    # 检查是否是纯数字（包括浮点数）
    try:
        float(text)
        cache_translation(text, text, question_id)  # 缓存数字
        return text  # 数字直接返回
    except ValueError:
        pass

    # 第一步：尝试使用本地选项映射
    if question_id:
        option_mappings = get_option_mappings()
        if question_id in option_mappings:
            # 尝试精确匹配（如 "1", "2" 等）
            if text in option_mappings[question_id]:
                translation = option_mappings[question_id][text]
                if DEBUG_TRANSLATION:
                    print(f"翻译调试: 选项映射匹配 {question_id}[{text}] -> {translation}")
                cache_translation(text, translation, question_id)
                return translation

            # 尝试处理浮点数（如 "1.0"）
            try:
                float_val = float(text)
                int_val = int(float_val)
                if str(int_val) in option_mappings[question_id]:
                    translation = option_mappings[question_id][str(int_val)]
                    if DEBUG_TRANSLATION:
                        print(f"翻译调试: 浮点数选项映射 {question_id}[{text}] -> {translation}")
                    cache_translation(text, translation, question_id)
                    return translation
            except (ValueError, TypeError):
                pass

    # 第二步：尝试内置常见术语映射
    lower_text = text.lower()
    if lower_text in COMMON_TRANSLATIONS:
        translation = COMMON_TRANSLATIONS[lower_text]
        if DEBUG_TRANSLATION:
            print(f"翻译调试: 内置映射匹配 '{text}' -> '{translation}'")
        cache_translation(text, translation, question_id)
        return translation

    # 第三步：尝试使用translators库的国内服务
    if DEBUG_TRANSLATION:
        print(f"翻译调试: 尝试在线翻译 '{text}'")
    try:
        import translators as ts

        # 国内可用的翻译服务列表（按优先级排序）
        translators_to_try = [
            'baidu',      # 百度翻译，国内可用
            'youdao',     # 有道翻译，国内可用
            'caiyun',     # 彩云小译，国内可用
            'alibaba',    # 阿里翻译，国内可用
            'tencent',    # 腾讯翻译，国内可用
            'bing',       # 必应翻译（可能被墙）
            'google',     # 谷歌翻译（通常被墙）
        ]

        # 尝试每个翻译服务
        for translator_name in translators_to_try:
            try:
                # 设置超时避免长时间等待
                translated = ts.translate_text(
                    text,
                    translator=translator_name,
                    from_language='en',
                    to_language='zh',
                    timeout=5.0  # 5秒超时
                )
                if translated and translated != text:
                    if DEBUG_TRANSLATION:
                        print(f"翻译调试: 使用 {translator_name} 翻译成功 '{text}' -> '{translated}'")
                    cache_translation(text, translated, question_id)
                    return translated
            except Exception:
                # 当前服务失败，尝试下一个
                continue

        # 所有服务都失败，返回原始文本
        if DEBUG_TRANSLATION:
            print(f"翻译调试: 所有在线翻译服务都失败，返回原始文本 '{text}'")
        cache_translation(text, text, question_id)
        return text

    except ImportError:
        # translators库未安装
        cache_translation(text, text, question_id)
        return text
    except Exception:
        # 其他错误
        cache_translation(text, text, question_id)
        return text

# 常量
SITE_ID_CHINA = '11'  # 苏州，中国
COHORT_MAPPING = {
    '1': 'younger',
    '2': 'elderly'
}

# 是否启用翻译（将英文问题和回答翻译成中文）
ENABLE_TRANSLATION = True
# 测试模式：限制处理的学生数量，0表示无限制
MAX_STUDENTS = 0  # 测试时设为0，实际运行时设为0（处理所有学生）
# 调试模式：打印翻译详细信息
DEBUG_TRANSLATION = False

# 开场白
OPENING_MESSAGE = """你好！我是社会与情感能力研究（SSES）的问卷系统。请回答以下问题，所有信息将严格保密。"""

def normalize_score_linear(wle_adj):
    """
    将WLE_ADJ分数转换为百分制（场景A）
    公式: score = (WLE_ADJ - 300) / 4
    参考：score.md中的线性变换公式
    """
    if pd.isna(wle_adj):
        return None
    score = (wle_adj - 300) / 4
    # 限制在0-100范围内（理论上应该在这个范围内）
    score = max(0.0, min(100.0, score))
    return round(score, 2)

def load_question_order(cohort):
    """
    加载问题顺序文件

    参数：
        cohort: 'elderly' 或 'younger'

    返回：
        list: 问题列表，每个元素包含 question_id, question_text, question_type
    """
    file_path = QUESTION_ORDER_DIR / f"question_order_{cohort}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"问题顺序文件不存在: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"加载 {cohort} 组问题顺序: {len(questions)} 个问题")
    return questions

def load_spss_data():
    """加载SPSS数据"""
    print(f"加载SPSS文件: {SPSS_FILE}")
    df, meta = pyreadstat.read_sav(str(SPSS_FILE), apply_value_formats=False)
    print(f"数据形状: {df.shape} (行×列)")
    return df, meta

def filter_chinese_students(df):
    """筛选中国学生"""
    if 'SiteID' not in df.columns:
        raise ValueError("数据集中未找到SiteID列")

    chinese_df = df[df['SiteID'] == SITE_ID_CHINA].copy()
    print(f"中国学生数量: {len(chinese_df)} (总共 {len(df)} 名学生)")
    return chinese_df

def extract_skill_scores(student_row):
    """
    提取学生的技能评分（以_WLE_ADJ结尾的列）
    返回字典：{技能代码: 百分制分数}
    """
    skill_scores = {}
    for col in student_row.index:
        if '_WLE_ADJ' in col:
            # 提取技能代码：假设格式为"技能代码_WLE_ADJ"
            skill_code = col.split('_WLE_ADJ')[0]
            if skill_code in SKILL_MAPPING:
                raw_score = student_row[col]
                if not pd.isna(raw_score):
                    normalized = normalize_score_linear(raw_score)
                    if normalized is not None:
                        skill_scores[skill_code] = normalized
    return skill_scores

def get_student_cohort(student_row):
    """从学生数据行获取cohort"""
    if 'CohortID' in student_row:
        cohort_id = str(student_row['CohortID'])
        return COHORT_MAPPING.get(cohort_id, 'unknown')
    return 'unknown'

def get_student_responses(student_id, cohort, question_order):
    """
    从数据库获取学生的所有回答，并按照问题顺序排序

    参数：
        student_id: 学生的原始ID (FullID)
        cohort: 学生所属组别 ('elderly' 或 'younger')
        question_order: 该组别的问题顺序列表

    返回：
        list: 按问题顺序排列的回答列表，每个元素包含:
            - question_id: 问题ID
            - question_text: 问题文本
            - answer_text: 回答文本
            - question_type: 问题类型
    """
    conn = get_db_connection()

    try:
        # 获取虚拟学生
        cursor = conn.execute(
            "SELECT id, cohort FROM virtual_student WHERE original_student_id = ?",
            (str(student_id),)
        )
        student = cursor.fetchone()

        if not student:
            # 尝试在student表中查找（旧版本可能使用student表）
            cursor = conn.execute(
                "SELECT id FROM student WHERE original_id = ?",
                (str(student_id),)
            )
            student = cursor.fetchone()

        if not student:
            print(f"警告: 找不到虚拟学生 {student_id}")
            return []

        student_id_db = student['id']

        # 获取该学生的所有回答
        cursor = conn.execute(
            "SELECT question_id, answer_text, raw_value FROM student_response WHERE virtual_student_id = ?",
            (student_id_db,)
        )
        responses = cursor.fetchall()

        # 转换为字典以便快速查找
        response_dict = {resp['question_id']: resp for resp in responses}

        # 按问题顺序构建回答列表
        ordered_responses = []

        for question in question_order:
            question_id = question['question_id']

            if question_id in response_dict:
                resp = response_dict[question_id]

                # 获取问题定义（用于问题文本）
                cursor = conn.execute(
                    "SELECT question_text FROM questionnaire_question WHERE question_id = ?",
                    (question_id,)
                )
                question_def = cursor.fetchone()

                question_text = question['question_text']
                # 如果数据库中有中文问题文本，则使用它；否则保持使用问题顺序文件中的中文文本
                if question_def and question_def['question_text']:
                    db_text = question_def['question_text']
                    # 简单检测是否包含中文字符
                    if any('\u4e00' <= ch <= '\u9fff' for ch in db_text):
                        question_text = db_text
                    else:
                        # 数据库文本是英文的，如果启用翻译则翻译
                        if ENABLE_TRANSLATION:
                            translated = translate_to_chinese(db_text, question_id)
                            if translated != db_text:  # 翻译成功
                                question_text = translated
                # 如果启用翻译，对问题文本进行翻译（确保是中文）
                if ENABLE_TRANSLATION:
                    question_text = translate_to_chinese(question_text, question_id)

                # 使用回答文本，如果没有则使用原始值
                answer_text = resp['answer_text']
                if not answer_text and resp['raw_value'] is not None:
                    answer_text = str(resp['raw_value'])

                # 如果启用翻译，对回答文本进行翻译
                if ENABLE_TRANSLATION:
                    answer_text = translate_to_chinese(answer_text, question_id)

                ordered_responses.append({
                    'question_id': question_id,
                    'question_text': question_text,
                    'question_type': question['question_type'],
                    'answer_text': answer_text,
                    'raw_value': resp['raw_value']
                })
            else:
                # 学生没有回答该问题，跳过
                continue

        return ordered_responses

    finally:
        conn.close()

def format_skill_summary(skill_scores):
    """
    格式化技能评估总结

    返回：
        str: 技能评估总结文本
    """
    if not skill_scores:
        return "问卷完成。暂时无法提供技能评估。"

    summary_lines = ["问卷完成。根据你的回答，你的技能评估如下："]

    for skill_code, score in skill_scores.items():
        skill_name = SKILL_MAPPING.get(skill_code, skill_code)
        summary_lines.append(f"- {skill_name}: {score:.1f}/100分")

    return "\n".join(summary_lines)

def build_student_dialogue(student_id, student_row, question_order_map):
    """
    构建单个学生的逐题问答对话

    参数：
        student_id: 学生原始ID (FullID)
        student_row: 学生数据行
        question_order_map: 字典，cohort -> 问题顺序列表

    返回：
        dict: 对话样本，包含conversations和metadata
    """
    # 获取学生cohort
    cohort = get_student_cohort(student_row)
    if cohort not in question_order_map:
        # 如果cohort未知，尝试从FullID推断或使用默认
        if cohort == 'unknown':
            # 尝试从数据库获取cohort
            conn = get_db_connection()
            try:
                cursor = conn.execute(
                    "SELECT cohort FROM virtual_student WHERE original_student_id = ?",
                    (str(student_id),)
                )
                student = cursor.fetchone()
                if student and student['cohort']:
                    cohort = student['cohort']
                else:
                    # 默认使用年轻组（因为两组问题大部分相同）
                    cohort = 'younger'
            finally:
                conn.close()
        else:
            # 如果cohort不在映射中，使用年轻组
            cohort = 'younger'

    # 获取该cohort的问题顺序
    question_order = question_order_map.get(cohort, question_order_map.get('younger', []))
    if not question_order:
        raise ValueError(f"没有找到 {cohort} 组的问题顺序")

    # 获取学生回答
    responses = get_student_responses(student_id, cohort, question_order)
    if not responses:
        # 学生没有回答任何问题
        return None

    # 提取技能评分
    skill_scores = extract_skill_scores(student_row)

    # 构建对话序列
    conversations = []

    # 添加开场白
    conversations.append({"from": "system", "value": OPENING_MESSAGE})

    # 添加逐题问答
    for i, resp in enumerate(responses):
        # 系统提问
        conversations.append({"from": "assistant", "value": resp['question_text']})
        # 学生回答
        conversations.append({"from": "human", "value": resp['answer_text']})

    # 添加技能评估总结
    skill_summary = format_skill_summary(skill_scores)
    conversations.append({"from": "system", "value": skill_summary})

    # 构建样本
    sample = {
        "id": f"student_{student_id}_{cohort}",
        "conversations": conversations,
        "metadata": {
            "student_id": str(student_id),
            "cohort": cohort,
            "num_questions": len(responses),
            "num_total_questions": len(question_order),
            "skill_scores": skill_scores,
            "has_skill_scores": bool(skill_scores)
        }
    }

    return sample

def create_dataset(chinese_df, question_order_map):
    """创建逐题问答对话数据集"""
    dataset = []

    total_students = len(chinese_df)
    print(f"\n处理 {total_students} 个学生...")

    for idx, (_, student_row) in enumerate(chinese_df.iterrows()):
        # 检查MAX_STUDENTS限制
        if MAX_STUDENTS > 0 and idx >= MAX_STUDENTS:
            print(f"  达到最大学生数量限制 ({MAX_STUDENTS})，停止处理")
            break

        if (idx + 1) % 100 == 0:
            print(f"  已处理 {idx + 1}/{total_students} 个学生")

        student_id = student_row['FullID']

        try:
            sample = build_student_dialogue(student_id, student_row, question_order_map)
            if sample:
                dataset.append(sample)
        except Exception as e:
            print(f"警告: 处理学生 {student_id} 时出错: {e}")
            continue

    print(f"\n总共生成 {len(dataset)} 条样本")
    return dataset

def split_dataset_by_student(dataset, test_size=0.15, val_size=0.15, random_state=42):
    """按学生划分数据集，避免数据泄露"""
    # 获取唯一学生ID
    student_ids = list(set([d['metadata']['student_id'] for d in dataset]))
    print(f"唯一学生ID数量: {len(student_ids)}")

    # 处理样本数量不足的情况
    n_students = len(student_ids)
    if n_students < 4:
        # 样本太少，全部作为训练集
        print(f"警告: 学生数量 ({n_students}) 太少，无法进行标准划分。将所有数据作为训练集。")
        train_data = dataset
        val_data = []
        test_data = []
        print(f"划分结果: 训练集 {len(train_data)} 条样本, 验证集 0 条样本, 测试集 0 条样本")
        return train_data, val_data, test_data
    elif n_students < 10:
        # 样本较少，使用较小的测试比例
        print(f"提示: 学生数量 ({n_students}) 较少，使用较小的划分比例。")
        test_size = max(0.1, test_size)  # 最小10%测试集
        val_size = max(0.1, val_size)    # 最小10%验证集

    # 第一次分割：训练+验证 vs 测试
    train_val_ids, test_ids = train_test_split(
        student_ids, test_size=test_size, random_state=random_state
    )

    # 第二次分割：训练 vs 验证
    # 调整验证集比例，使其占总体比例
    val_relative_size = val_size / (1 - test_size)
    train_ids, val_ids = train_test_split(
        train_val_ids, test_size=val_relative_size, random_state=random_state
    )

    print(f"划分结果: 训练集 {len(train_ids)} 名学生, 验证集 {len(val_ids)} 名学生, 测试集 {len(test_ids)} 名学生")

    def filter_by_student(dataset, id_set):
        return [d for d in dataset if d['metadata']['student_id'] in id_set]

    train_data = filter_by_student(dataset, set(train_ids))
    val_data = filter_by_student(dataset, set(val_ids))
    test_data = filter_by_student(dataset, set(test_ids))

    print(f"\n训练集: {len(train_data)} 条样本")
    print(f"验证集: {len(val_data)} 条样本")
    print(f"测试集: {len(test_data)} 条样本")

    return train_data, val_data, test_data

def save_datasets(train_data, val_data, test_data, output_dir):
    """保存数据集"""
    os.makedirs(output_dir, exist_ok=True)

    # 保存完整数据集
    full_data = train_data + val_data + test_data
    full_path = os.path.join(output_dir, 'sequential_dialogue_full.json')
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print(f"完整数据集已保存: {full_path}")

    # 保存划分后的数据集
    train_path = os.path.join(output_dir, 'sequential_dialogue_train.json')
    val_path = os.path.join(output_dir, 'sequential_dialogue_val.json')
    test_path = os.path.join(output_dir, 'sequential_dialogue_test.json')

    with open(train_path, 'w', encoding='utf-8') as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    print(f"训练集已保存: {train_path}")

    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_data, f, ensure_ascii=False, indent=2)
    print(f"验证集已保存: {val_path}")

    with open(test_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"测试集已保存: {test_path}")

    # 统计信息
    stats = {
        'total_samples': len(full_data),
        'train_samples': len(train_data),
        'val_samples': len(val_data),
        'test_samples': len(test_data),
        'num_students': len(set([d['metadata']['student_id'] for d in full_data])),
        'avg_questions_per_student': np.mean([d['metadata']['num_questions'] for d in full_data]) if full_data else 0,
        'cohort_distribution': {
            'elderly': len([d for d in full_data if d['metadata']['cohort'] == 'elderly']),
            'younger': len([d for d in full_data if d['metadata']['cohort'] == 'younger']),
            'unknown': len([d for d in full_data if d['metadata']['cohort'] not in ['elderly', 'younger']])
        },
        'skill_coverage': {skill: len([d for d in full_data if skill in d['metadata']['skill_scores']])
                          for skill in SKILL_MAPPING.keys() if skill not in ['EFF', 'MOT']}
    }

    stats_path = os.path.join(output_dir, 'sequential_dialogue_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"数据集统计已保存: {stats_path}")

    return train_path, val_path, test_path

def main():
    print("=" * 60)
    print("逐题问答对话数据集构建脚本")
    print("=" * 60)

    # 输出目录
    output_dir = PROJECT_ROOT / "backEnd" / "finetuning_data" / "sequential_dialogue"

    try:
        # 1. 加载问题顺序
        print("加载问题顺序文件...")
        question_order_elderly = load_question_order('elderly')
        question_order_younger = load_question_order('younger')

        question_order_map = {
            'elderly': question_order_elderly,
            'younger': question_order_younger
        }

        # 2. 加载SPSS数据
        df, meta = load_spss_data()

        # 3. 筛选中国学生
        chinese_df = filter_chinese_students(df)

        if len(chinese_df) == 0:
            print("错误: 未找到中国学生数据")
            return 1

        # 4. 创建数据集
        dataset = create_dataset(chinese_df, question_order_map)

        if len(dataset) == 0:
            print("错误: 未能创建任何数据集样本")
            return 1

        # 5. 划分数据集
        train_data, val_data, test_data = split_dataset_by_student(dataset)

        # 6. 保存数据集
        save_datasets(train_data, val_data, test_data, output_dir)

        print("\n" + "=" * 60)
        print("数据集创建完成!")
        print("=" * 60)

        # 显示样本示例
        print("\n样本示例:")
        if dataset:
            sample = dataset[0]
            print(f"ID: {sample['id']}")
            print(f"学生ID: {sample['metadata']['student_id']}")
            print(f"组别: {sample['metadata']['cohort']}")
            print(f"问题数量: {sample['metadata']['num_questions']}")
            print(f"技能评分数量: {len(sample['metadata']['skill_scores'])}")
            print("\n对话序列 (前3个问答):")
            for i, conv in enumerate(sample['conversations'][:7]):  # 开场白 + 3个问答
                role = conv['from']
                text_preview = conv['value'][:80] + "..." if len(conv['value']) > 80 else conv['value']
                print(f"  {role}: {text_preview}")

        # 保存翻译缓存
        save_translation_cache()
        print(f"翻译缓存已保存: {len(_translation_cache)} 条记录")

        return 0

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())