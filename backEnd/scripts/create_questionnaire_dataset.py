#!/usr/bin/env python3
"""
创建SSES问卷数据的微调数据集
将问卷问题、学生回答和技能评分对应起来，生成用于Qwen1.5-1.8B-Chat微调的中文数据集
"""

import json
import pandas as pd
import pyreadstat
import numpy as np
from pathlib import Path
import logging
import sys
from typing import Dict, List, Any, Optional, Tuple

# 配置日志 - 使用UTF-8编码避免Windows中文乱码
class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # 确保使用UTF-8编码写入
            if isinstance(msg, str):
                msg = msg.encode('utf-8', errors='replace').decode('utf-8')
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# 清除现有处理器
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 添加UTF-8处理器
handler = UTF8StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

class QuestionnaireDatasetCreator:
    def __init__(self, questionnaire_path: str, sav_path: str, score_guide_path: str):
        """
        初始化数据集创建器

        Args:
            questionnaire_path: 问卷JSON文件路径
            sav_path: SPSS SAV数据文件路径
            score_guide_path: 评分细则文件路径
        """
        self.questionnaire_path = questionnaire_path
        self.sav_path = sav_path
        self.score_guide_path = score_guide_path

        # 加载数据
        self.load_data()

        # 构建映射
        self.build_mappings()

    def load_data(self):
        """加载所有必要数据"""
        logger.info("加载问卷数据...")
        with open(self.questionnaire_path, 'r', encoding='utf-8') as f:
            self.questionnaire = json.load(f)

        logger.info("加载SAV数据...")
        self.df, self.meta = pyreadstat.read_sav(self.sav_path)
        logger.info(f"数据形状: {self.df.shape}")

        logger.info("加载评分细则...")
        with open(self.score_guide_path, 'r', encoding='utf-8') as f:
            self.score_guide = f.read()

        # 技能缩写映射（根据score.md）
        self.skill_mapping = {
            'ASS': '自信/主张',
            'COO': '合作',
            'CRE': '创造力',
            'CUR': '好奇心',
            'EFF': '自我效能',
            'EMO': '情绪控制',
            'EMP': '同理心',
            'ENE': '活力',
            'MOT': '成就动机',
            'OPT': '乐观',
            'PER': '坚持',
            'RES': '责任感',
            'SEL': '自我控制',
            'SOC': '社交能力',
            'STR': '抗压能力',
            'TOL': '包容',
            'TRU': '信任'
        }

    def build_mappings(self):
        """构建变量到问题信息的映射"""
        logger.info("构建变量映射...")
        self.var_to_info = {}

        for section in self.questionnaire['sections']:
            if 'questions' not in section:
                continue

            for q in section['questions']:
                q_type = q.get('type', '')
                q_text_zh = q.get('text_zh', q.get('text', ''))
                q_number = q.get('question_number', '')
                options = q.get('options', [])

                # 构建选项代码到标签的映射（针对选择题）
                option_map = {}
                if options and isinstance(options, list):
                    for i, opt in enumerate(options):
                        # 通常代码从1开始
                        code = i + 1
                        label = opt.get('label_zh', opt.get('label', str(code)))
                        option_map[code] = label
                        option_map[str(code)] = label
                        # 也允许浮点数代码
                        option_map[float(code)] = label

                # 处理单个变量
                if 'variable' in q:
                    var = q['variable']
                    self.var_to_info[var] = {
                        'question_text': q_text_zh,
                        'type': q_type,
                        'options': option_map,
                        'question_number': q_number,
                        'unit': q.get('unit', ''),
                        'original_question': q
                    }

                # 处理多个变量（矩阵问题）
                if 'variables' in q:
                    sub_items = q.get('sub_items', [])
                    rows = q.get('rows', [])

                    for i, var in enumerate(q['variables']):
                        # 尝试获取子项或行的特定文本
                        specific_text = q_text_zh
                        if i < len(sub_items):
                            prompt = sub_items[i].get('prompt_zh', sub_items[i].get('prompt', ''))
                            if prompt:
                                specific_text = f"{q_text_zh} {prompt}"
                        elif i < len(rows):
                            row = rows[i]
                            row_label = row.get('label_zh', row.get('label', ''))
                            if row_label:
                                specific_text = f"{q_text_zh} - {row_label}"

                        self.var_to_info[var] = {
                            'question_text': specific_text,
                            'type': q_type,
                            'options': option_map,
                            'question_number': q_number,
                            'unit': q.get('unit', ''),
                            'original_question': q
                        }

        logger.info(f"映射了 {len(self.var_to_info)} 个变量")

        # 检查哪些变量在数据集中存在
        self.available_vars = [var for var in self.var_to_info.keys() if var in self.df.columns]
        logger.info(f"数据集中可用的变量: {len(self.available_vars)}/{len(self.var_to_info)}")

        # 识别技能评分变量
        self.skill_vars = [col for col in self.df.columns if '_WLE_ADJ' in col]
        logger.info(f"找到 {len(self.skill_vars)} 个技能评分变量")

        # 检查缺失的变量
        missing_vars = set(self.var_to_info.keys()) - set(self.available_vars)
        if missing_vars:
            logger.warning(f"缺失 {len(missing_vars)} 个变量，例如: {list(missing_vars)[:10]}")

    def convert_response(self, var: str, value: Any) -> str:
        """
        将原始响应值转换为可读文本

        Args:
            var: 变量名
            value: 原始值

        Returns:
            转换后的文本响应
        """
        if pd.isna(value):
            return "未回答"

        info = self.var_to_info.get(var)
        if not info:
            return str(value)

        q_type = info['type']
        options = info['options']

        # 尝试转换为整数代码（用于选项匹配）
        try:
            # 如果是浮点数，尝试转换为整数
            if isinstance(value, float) and value.is_integer():
                code = int(value)
            else:
                code = value
        except:
            code = value

        # 根据问题类型转换
        if q_type in ['single_choice', 'matrix_single_choice']:
            # 选择题：使用选项映射
            if code in options:
                return options[code]
            elif str(code) in options:
                return options[str(code)]
            else:
                # 尝试查找最接近的代码
                for k in options.keys():
                    try:
                        if float(k) == float(code):
                            return options[k]
                    except:
                        pass
                return str(value)

        elif q_type == 'numeric_input':
            unit = info.get('unit', '')
            if unit:
                return f"{value} {unit}"
            else:
                return str(value)

        elif q_type == 'scale_0_10':
            # 0-10量表
            try:
                score = float(value)
                return f"{score}/10"
            except:
                return str(value)

        elif q_type == 'month_year_input':
            # 月份年份输入
            return str(value)

        elif q_type == 'open_ended':
            # 开放性问题
            return str(value)

        else:
            return str(value)

    def convert_skill_score(self, raw_score: float) -> Tuple[float, str]:
        """
        将原始WLE_ADJ分数转换为百分制分数和分类

        Args:
            raw_score: 原始WLE_ADJ分数

        Returns:
            (百分制分数, 分类描述)
        """
        if pd.isna(raw_score):
            return np.nan, "无数据"

        # 使用场景B转换：均值500 -> 50分，标准差100 -> 20分
        # Score_100 = 50 + (WLE_Adj - 500) / 5
        score_100 = 50 + (raw_score - 500) / 5

        # 分类
        if score_100 < 40:
            category = "较低"
        elif score_100 < 60:
            category = "中等"
        elif score_100 < 80:
            category = "较高"
        else:
            category = "很高"

        return round(score_100, 1), category

    def get_skill_assessment_text(self, skill_scores: Dict[str, float]) -> str:
        """
        根据技能分数生成评估文本

        Args:
            skill_scores: 技能名到百分制分数的映射

        Returns:
            评估文本
        """
        if not skill_scores:
            return "无技能评分数据"

        # 按分数排序
        sorted_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建文本
        lines = ["技能评估结果（百分制）："]
        for skill_name, score in sorted_skills:
            # 分类
            if score < 40:
                category = "较低"
            elif score < 60:
                category = "中等"
            elif score < 80:
                category = "较高"
            else:
                category = "很高"
            lines.append(f"- {skill_name}: {score}分（{category}）")

        # 添加综合评价
        lines.append("\n综合评价：")

        # 找出最高分和最低分技能
        if len(sorted_skills) >= 2:
            top_skill, top_score = sorted_skills[0]
            bottom_skill, bottom_score = sorted_skills[-1]

            if top_score >= 70:
                lines.append(f"该学生在{top_skill}方面表现突出，显示出较强的相关能力。")
            elif top_score >= 60:
                lines.append(f"该学生在{top_skill}方面表现良好。")

            if bottom_score < 40:
                lines.append(f"在{bottom_skill}方面相对较弱，有较大提升空间。")
            elif bottom_score < 50:
                lines.append(f"在{bottom_skill}方面有提升空间。")

        # 通用建议
        lines.append("建议根据具体技能评分，结合学生的个人背景和发展需求，制定个性化的培养计划。")

        return "\n".join(lines)

    def create_student_record(self, idx: int, max_responses: int = 50) -> Optional[Dict[str, Any]]:
        """
        为单个学生创建记录

        Args:
            idx: 学生索引（DataFrame行索引）
            max_responses: 最大回答数量（避免过长的输入）

        Returns:
            学生记录字典，如果数据不完整则返回None
        """
        row = self.df.iloc[idx]

        # 检查必要的技能评分是否完整
        skill_scores_raw = {}
        missing_skills = 0
        for skill_var in self.skill_vars:
            score = row[skill_var]
            if pd.isna(score):
                missing_skills += 1
                # 如果缺失太多技能分数，跳过该学生
                if missing_skills > 3:  # 允许缺失少量技能
                    return None
            else:
                skill_scores_raw[skill_var] = score

        # 收集背景信息（部分关键变量）
        background_vars = ['STQM00101', 'STQM00201', 'STQM00401', 'STQM00501', 'STQM00601']
        background_info = []
        for var in background_vars:
            if var in row:
                value = row[var]
                if pd.isna(value):
                    continue
                info = self.var_to_info.get(var)
                if info:
                    question = info['question_text']
                    answer = self.convert_response(var, value)
                    background_info.append(f"Assistant: {question} teenager: {answer}")

        # 收集问卷回答（选择可用的变量）
        response_vars = [v for v in self.available_vars if v not in background_vars]
        # 限制回答数量以避免过长的上下文
        if len(response_vars) > max_responses:
            # 优先选择有回答的变量
            non_null_vars = []
            for var in response_vars:
                if not pd.isna(row[var]):
                    non_null_vars.append(var)

            if len(non_null_vars) > max_responses:
                selected_vars = non_null_vars[:max_responses]
            else:
                selected_vars = non_null_vars + [v for v in response_vars if v not in non_null_vars][:max_responses - len(non_null_vars)]
        else:
            selected_vars = response_vars

        responses = []
        for var in selected_vars:
            value = row[var]
            if pd.isna(value):
                continue
            info = self.var_to_info.get(var)
            if info:
                question = info['question_text']
                # 简化问题文本（避免过长）
                if len(question) > 80:
                    question = question[:77] + "..."
                answer = self.convert_response(var, value)
                responses.append({
                    'question': question,
                    'answer': answer,
                    'variable': var
                })

        # 如果回答太少，跳过该学生
        if len(responses) < 10:
            return None

        # 转换技能评分
        skill_scores_100 = {}
        skill_categories = {}
        for skill_var, raw_score in skill_scores_raw.items():
            # 提取技能缩写
            skill_abbr = skill_var.split('_')[0]
            skill_name = self.skill_mapping.get(skill_abbr, skill_abbr)
            score_100, category = self.convert_skill_score(raw_score)
            if not pd.isna(score_100):
                skill_scores_100[skill_name] = float(score_100)
                skill_categories[skill_name] = category

        # 如果技能评分太少，跳过该学生
        if len(skill_scores_100) < 10:
            return None

        # 生成评估文本
        assessment_text = self.get_skill_assessment_text(skill_scores_100)

        # 构建记录
        record = {
            'id': str(row.get('FullID', f'student_{idx}')),
            'instruction': '根据以下学生的背景信息和问卷回答，评估其社会与情感技能：',
            'input': self._format_input(background_info, responses),
            'output': assessment_text,
            'metadata': {
                'student_index': idx,
                'background_vars_count': len(background_info),
                'response_vars_count': len(responses),
                'skill_scores': skill_scores_100,
                'skill_categories': skill_categories,
                'total_responses': len(background_info) + len(responses)
            }
        }

        # 转换numpy类型为Python原生类型
        record = self._convert_numpy_types(record)
        return record

    def _convert_numpy_types(self, obj):
        """递归转换numpy类型为Python原生类型"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_numpy_types(item) for item in obj)
        elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def _format_input(self, background_info: List[str], responses: List[Dict]) -> str:
        """格式化输入文本"""
        lines = ["学生背景信息："]
        if background_info:
            lines.extend([f"- {info}" for info in background_info])
        else:
            lines.append("- 无背景信息")

        lines.append("\n问卷回答：")
        if responses:
            for i, resp in enumerate(responses, 1):
                lines.append(f"{i}. Assistant: {resp['question']} teenager: {resp['answer']}")
        else:
            lines.append("- 无回答数据")

        return "\n".join(lines)

    def create_dataset(self, n_students: int = 1000, output_path: str = None) -> List[Dict[str, Any]]:
        """
        创建完整数据集

        Args:
            n_students: 包含的学生数量
            output_path: 输出文件路径

        Returns:
            记录列表
        """
        if output_path is None:
            output_path = f"questionnaire_finetuning_{n_students}.jsonl"

        logger.info(f"开始创建数据集，目标包含 {n_students} 名学生...")

        records = []
        skipped = 0
        processed = 0

        # 随机选择学生，但确保可重复性
        np.random.seed(42)
        total_students = len(self.df)

        # 预计算哪些学生有完整的技能评分且是中国学生
        valid_indices = []
        chinese_count = 0
        for idx in range(total_students):
            row = self.df.iloc[idx]
            # 检查是否为中国学生
            if str(row['LANG']).strip() != 'CHI':
                continue
            chinese_count += 1
            # 检查技能评分是否基本完整
            missing_skills = sum(1 for skill_var in self.skill_vars if pd.isna(row[skill_var]))
            if missing_skills <= 3:  # 允许缺失最多3个技能
                valid_indices.append(idx)

        logger.info(f"数据集中有 {chinese_count} 名中国学生（LANG='CHI'）")
        logger.info(f"其中 {len(valid_indices)} 名学生具有基本完整的技能评分")

        # 随机选择
        if len(valid_indices) > n_students:
            selected_indices = np.random.choice(valid_indices, n_students, replace=False)
        else:
            selected_indices = valid_indices
            logger.warning(f"只有 {len(valid_indices)} 名学生符合条件，将使用所有符合条件的学生")

        for idx in selected_indices:
            processed += 1
            record = self.create_student_record(idx)
            if record:
                records.append(record)
            else:
                skipped += 1

        logger.info(f"处理了 {processed} 名学生，创建了 {len(records)} 条记录，跳过了 {skipped} 条")

        # 保存为JSONL
        logger.info(f"保存数据集到 {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        # 保存样本用于检查
        sample_path = output_path.replace('.jsonl', '_sample.json')
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(records[:5], f, ensure_ascii=False, indent=2)

        logger.info(f"数据集创建完成。样本已保存到 {sample_path}")

        return records

def main():
    """主函数"""
    questionnaire_path = r"D:\TBLLM\docs\rag\questionary.json"
    sav_path = r"D:\TBLLM\docs\rag\INT_01_ST_(2021.04.14)_Public.sav"
    score_guide_path = r"D:\TBLLM\docs\rag\score.md"

    # 创建数据集
    creator = QuestionnaireDatasetCreator(questionnaire_path, sav_path, score_guide_path)

    # 创建小型测试数据集（仅中国学生）
    # logger.info("创建测试数据集（50名中国学生）...")
    # test_records = creator.create_dataset(n_students=50, output_path="questionnaire_finetuning_test.jsonl")

    # 创建中等规模数据集（可选）
    # logger.info("创建中等规模数据集（2000名学生）...")
    # medium_records = creator.create_dataset(n_students=2000, output_path="questionnaire_finetuning_medium.jsonl")

    # 创建完整数据集（可选）
    logger.info("创建完整数据集（10000名学生）...")
    full_records = creator.create_dataset(n_students=10000, output_path="dataset/questionnaire_finetuning_full.jsonl")

if __name__ == "__main__":
    main()