#!/usr/bin/env python3
"""
file_register_macos.py
macOS 专用目录资产统计/去重工具
Usage:
    # 新建/覆盖
    python3 file_register_macos.py ~/Pictures

    # 追加并删除重复
    python3 file_register_macos.py -a -f ~/Pictures
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **k: x  # noqa: E731

# ---------- 配置 ----------
PACKAGE_EXTENSIONS = {
    ".app",
    ".framework",
    ".bundle",
    ".plugin",
    ".kext",
    ".qlgenerator",
    ".photoslibrary",
    ".docset",
    ".playground",
    ".xcassets",
}
DEFAULT_JSON = "fileRegister.json"
logging.basicConfig(level=logging.INFO, format="%(message)s")

# ---------- 工具 ----------
def human_size(b: int) -> str:
    if b == 0:
        return "0 B"
    for unit in ("KB", "MB", "GB"):
        b /= 1024.0
        if b < 1024:
            return f"{b:.2f} {unit}"
    return f"{b/1024:.2f} TB"

def is_package(p: Path) -> bool:
    return p.is_dir() and p.suffix.lower() in PACKAGE_EXTENSIONS

def safe_stat(p: Path) -> Optional[os.stat_result]:
    try:
        return p.lstat()
    except OSError as e:
        logging.warning("无法访问 %s : %s", p, e)
        return None

# ---------- 核心采集 ----------
def collect(target: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    folders_cnt = folders_bytes = 0
    files_cnt = files_bytes = 0
    packages_cnt = packages_bytes = 0
    du_cnt = du_bytes = 0

    records: List[Dict[str, Any]] = []

    # 进度条仅在有 tqdm 时生效
    for path in tqdm(list(target.rglob("*")), desc="扫描"):
        st = safe_stat(path)
        if not st:
            continue
        size = st.st_size

        rp = str(path.relative_to(target))

        if path.name.startswith("._"):
            du_bytes += size
            du_cnt += 1
            continue

        if path.name == ".DS_Store":
            continue

        if is_package(path):
            packages_cnt += 1
            packages_bytes += size
            records.append(
                {
                    "filename": path.name,
                    "size": human_size(size),
                    "extension": path.suffix,
                    "relative_path": rp,
                    "type": "package",
                }
            )
            continue

        if path.is_dir():
            # 统计文件夹内部文件/大小
            dir_size = dir_files = 0
            for sub in path.rglob("*"):
                sst = safe_stat(sub)
                if sst and sst.st_size:
                    dir_size += sst.st_size
                    dir_files += 1
            folders_cnt += 1
            folders_bytes += dir_size
            records.append(
                {
                    "filename": path.name,
                    "size": human_size(dir_size),
                    "extension": "<folder>",
                    "relative_path": rp,
                    "file_count": dir_files,
                    "type": "folder",
                }
            )
            continue

        if path.is_file():
            files_cnt += 1
            files_bytes += size
            records.append(
                {
                    "filename": path.name,
                    "size": human_size(size),
                    "extension": path.suffix,
                    "relative_path": rp,
                    "type": "file",
                }
            )

    summary: Dict[str, Any] = {
        "folders": {"count": folders_cnt, "size": human_size(folders_bytes)},
        "files": {"count": files_cnt, "size": human_size(files_bytes)},
        "packages": {"count": packages_cnt, "size": human_size(packages_bytes)},
        "dot_underscore_files": {"count": du_cnt, "size": human_size(du_bytes)},
        "total_files": folders_cnt + files_cnt + packages_cnt + du_cnt,
        "total_size": human_size(
            folders_bytes + files_bytes + packages_bytes + du_bytes
        ),
    }
    return records, summary

# ---------- 主流程 ----------
def safe_delete(p: Path) -> None:
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)
    except Exception as e:
        logging.error("删除失败 %s : %s", p, e)

def main(target: Path, add: bool, force: bool, out: Optional[Path]) -> None:
    out_path = out or (target / DEFAULT_JSON)

    # 读取旧数据
    old_records: List[Dict[str, Any]] = []
    if add and out_path.exists():
        try:
            old_records = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception as e:
            logging.error("读取旧 json 失败: %s", e)
            sys.exit(2)
        # 剔除旧 summary
        old_records = [r for r in old_records if "total_files" not in r]

    # 采集新数据
    new_records, summary = collect(target)

    # 旧记录中已有 basename 的集合
    existing_basename = {r["filename"] for r in old_records}

    # 删除旧记录中已存在的同名文件/目录/包
    to_delete = [
        target / r["relative_path"]
        for r in new_records
        if r["filename"] in existing_basename
    ]
    if to_delete:
        if not force:
            ans = input(
                f"检测到 {len(to_delete)} 个已存在条目将被删除，确认? [y/N] "
            )
            if ans.lower() != "y":
                logging.info("用户取消")
                sys.exit(0)
        for p in to_delete:
            safe_delete(p)

    # 过滤被删除的条目（同名且已存在直接丢弃）
    new_records = [
        r for r in new_records
        if (target / r["relative_path"]).exists()
           and r["filename"] not in existing_basename
    ]

    # 合并并重新编号
    combined = old_records + new_records
    for idx, record in enumerate(combined, 1):
        record["index"] = idx
    combined.append(summary)

    # 写回
    try:
        out_path.write_text(
            json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logging.info("已写入 %s", out_path)
    except Exception as e:
        logging.error("写入失败: %s", e)
        sys.exit(2)

def cli() -> None:
    parser = argparse.ArgumentParser(description="macOS 目录资产统计/去重工具")
    parser.add_argument("target", help="目标目录")
    parser.add_argument(
        "-a", "--add", action="store_true", help="追加模式（去重+删除）"
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="删除前不确认"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="自定义 json 输出路径"
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        logging.error("目录不存在: %s", args.target)
        sys.exit(1)

    main(target, args.add, args.force, args.output)

if __name__ == "__main__":
    cli()