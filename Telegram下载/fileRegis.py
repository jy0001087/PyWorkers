#!/usr/bin/env python3
"""
file_register_macos.py
macOS 专用：统计目标目录下的
  - 普通文件夹
  - 普通文件
  - 包（.app / .framework / .photoslibrary 等）
  - 以 ._ 开头的隐藏资源叉文件
四类信息，最后写入 fileRegister.json
Usage: python3 file_register_macos.py <target_dir>
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

PACKAGE_EXTENSIONS = {
    '.app', '.framework', '.bundle', '.plugin',
    '.kext', '.qlgenerator', '.photoslibrary',
    '.docset', '.playground', '.xcassets'
}

def human_size(b: int) -> str:
    if b == 0:
        return "0 B"
    kb = b / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.2f} MB"
    return f"{mb / 1024:.2f} GB"

def is_package(p: Path) -> bool:
    return p.is_dir() and p.suffix.lower() in PACKAGE_EXTENSIONS

def folder_size_and_count(folder: Path) -> Tuple[int, int]:
    """返回 (总字节, 内部文件数)"""
    bytes_total = 0
    files_total = 0
    for p in folder.rglob('*'):
        try:
            if p.is_file():
                bytes_total += p.lstat().st_size
                files_total += 1
            elif is_package(p):
                bytes_total += p.lstat().st_size
                files_total += 1
        except OSError:
            pass
    return bytes_total, files_total

def collect_file_info(target_dir: str) -> List[Dict[str, Any]]:
    target_path = Path(target_dir).expanduser().resolve()
    if not target_path.is_dir():
        raise ValueError(f"路径不存在或不是目录: {target_path}")

    records: List[Dict[str, Any]] = []
    index = 1

    # 类别计数器
    folders_bytes = folders_cnt = 0
    files_bytes   = files_cnt   = 0
    packages_bytes = packages_cnt = 0
    du_bytes = du_cnt = 0  # ._ 文件

    for root, dirs, filenames in os.walk(target_path, topdown=True):
        root_path = Path(root)

        # 1. 普通文件夹（不含根目录）
        if root_path != target_path:
            size, count = folder_size_and_count(root_path)
            folders_bytes += size
            folders_cnt += 1
            records.append({
                "index": index,
                "filename": root_path.name,
                "size": human_size(size),
                "extension": "<folder>",
                "relative_path": str(root_path.relative_to(target_path)),
                "file_count": count,
                "type": "folder"
            })
            index += 1

        # 2. 包（视为单个文件）
        for d in dirs[:]:
            dir_path = root_path / d
            if is_package(dir_path):
                size, _ = folder_size_and_count(dir_path)
                packages_bytes += size
                packages_cnt += 1
                records.append({
                    "index": index,
                    "filename": dir_path.name,
                    "size": human_size(size),
                    "extension": dir_path.suffix,
                    "relative_path": str(dir_path.relative_to(target_path)),
                    "type": "package"
                })
                index += 1
                dirs.remove(d)

        # 3. 普通文件 & ._
        for filename in filenames:
            if filename == '.DS_Store':
                continue
            file_path = root_path / filename
            try:
                size = file_path.lstat().st_size
            except OSError:
                continue

            if filename.startswith('._'):
                du_bytes += size
                du_cnt += 1
                continue  # 仅统计，不写入明细

            files_bytes += size
            files_cnt += 1
            records.append({
                "index": index,
                "filename": file_path.name,
                "size": human_size(size),
                "extension": file_path.suffix,
                "relative_path": str(file_path.relative_to(target_path)),
                "type": "file"
            })
            index += 1

    # 4. 最终汇总
    summary = {
        "folders":   {"count": folders_cnt,   "size": human_size(folders_bytes)},
        "files":     {"count": files_cnt,     "size": human_size(files_bytes)},
        "packages":  {"count": packages_cnt,  "size": human_size(packages_bytes)},
        "dot_underscore_files": {"count": du_cnt, "size": human_size(du_bytes)},
        "total_files": folders_cnt + files_cnt + packages_cnt + du_cnt,
        "total_size": human_size(folders_bytes + files_bytes + packages_bytes + du_bytes)
    }
    return records + [summary]

def main():
    if len(sys.argv) != 2:
        print("用法: python3 file_register_macos.py <target_dir>")
        sys.exit(1)

    target_dir = sys.argv[1]
    try:
        data = collect_file_info(target_dir)
        output_file = Path(target_dir).resolve() / "fileRegister.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已生成 {output_file}")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()