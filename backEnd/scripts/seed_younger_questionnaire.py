#!/usr/bin/env python3
"""
将年轻组题库同步为与年长组一致的题目。

说明：
1. questionnaire_question.question_id 是全库唯一，因此年轻组复制年长组题目时，
   使用 YOUNGER_COPY__<elderly_question_id> 作为年轻组题目ID。
2. 脚本会删除当前 younger 组题目，再从 elderly 组复制一份，保证两组题干、
   题型、选项和元数据一致。
3. 该脚本只处理题库定义，不修改用户、会话和历史测评结果。
"""

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "backEnd" / "instance" / "users.db"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        elderly_rows = conn.execute(
            """
            SELECT question_id, question_text, question_type, options_json, metadata_json
            FROM questionnaire_question
            WHERE cohort = 'elderly'
            ORDER BY question_id
            """
        ).fetchall()

        if not elderly_rows:
            raise RuntimeError("未找到 elderly 组题目，无法同步 younger 组")

        conn.execute("DELETE FROM questionnaire_question WHERE cohort = 'younger'")

        for question_id, question_text, question_type, options_json, metadata_json in elderly_rows:
            conn.execute(
                """
                INSERT INTO questionnaire_question
                    (question_id, question_text, cohort, question_type, options_json, metadata_json)
                VALUES (?, ?, 'younger', ?, ?, ?)
                """,
                (
                    f"YOUNGER_COPY__{question_id}",
                    question_text,
                    question_type,
                    options_json,
                    metadata_json,
                ),
            )

        conn.commit()

        rows = conn.execute(
            "SELECT cohort, COUNT(*) FROM questionnaire_question GROUP BY cohort ORDER BY cohort"
        ).fetchall()
        print("题库数量：")
        for cohort, count in rows:
            print(f"{cohort}: {count}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
