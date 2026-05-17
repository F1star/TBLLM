#!/usr/bin/env python3
"""Download/export the sentence-transformers embedding model for offline local use."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backEnd"
DEFAULT_TARGET = PROJECT_ROOT / "models" / "embedding" / "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_SOURCE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_CACHE = PROJECT_ROOT / ".cache" / "huggingface"

sys.path.insert(0, str(BACKEND_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare the local embedding model used by TBLLM vector retrieval.",
    )
    parser.add_argument(
        "--source",
        default=os.environ.get("TBLLM_EMBEDDING_SOURCE", DEFAULT_SOURCE),
        help="Hugging Face model id or existing local sentence-transformers directory.",
    )
    parser.add_argument(
        "--target",
        default=os.environ.get("TBLLM_EMBEDDING_MODEL", str(DEFAULT_TARGET)),
        help="Target local directory for the exported embedding model.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target directory if it already exists.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Use only local Hugging Face cache; do not contact the network.",
    )
    return parser.parse_args()


def target_is_ready(target: Path) -> bool:
    return (
        (target / "modules.json").exists()
        and (target / "config_sentence_transformers.json").exists()
    )


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()

    if target_is_ready(target) and not args.force:
        print(f"[OK] 本地嵌入模型已存在: {target}")
        return 0

    if target.exists() and args.force:
        shutil.rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(DEFAULT_CACHE))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(DEFAULT_CACHE / "transformers"))

    from sentence_transformers import SentenceTransformer

    print(f"加载嵌入模型来源: {args.source}")
    print(f"Hugging Face缓存: {os.environ.get('HF_HOME')}")
    model = SentenceTransformer(
        args.source,
        cache_folder=os.environ.get("HF_HOME"),
        local_files_only=args.local_files_only,
    )

    print(f"导出到本地目录: {target}")
    model.save(str(target))

    if not target_is_ready(target):
        print(f"[FAILED] 本地模型导出不完整: {target}")
        return 1

    print("[SUCCESS] 本地嵌入模型准备完成")
    print(f"TBLLM_EMBEDDING_MODEL={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
