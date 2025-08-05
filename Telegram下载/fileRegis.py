#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import argparse
from webdav3.client import Client
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(description="本地与 WebDAV 文件比对并清理重复文件")
    parser.add_argument('--local', required=True, help='本地目录路径')
    parser.add_argument('--remote', required=True, help='WebDAV 地址，如 http://ubuntu:5244/dav')
    parser.add_argument('--username', required=True, help='WebDAV 用户名')
    parser.add_argument('--password', required=True, help='WebDAV 密码')
    parser.add_argument('--output', default='output', help='JSON 输出目录')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不删除任何远程文件')
    return parser.parse_args()

def format_size(size_bytes):
    if size_bytes >= 1024 ** 2:
        return f"{size_bytes / 1024 ** 2:.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"

def list_local_files(base_path):
    records = []
    index = 1
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('._')]
        for d in dirs:
            dir_path = os.path.join(root, d)
            rel_path = os.path.relpath(dir_path, base_path)
            file_count = sum([len(filenames) for _, _, filenames in os.walk(dir_path)])
            records.append({
                "index": index,
                "filename": d,
                "size": format_size(0),
                "extension": "<folder>",
                "relative_path": rel_path,
                "file_count": file_count,
                "type": "folder"
            })
            index += 1
        for f in files:
            if f.startswith('.') or f.startswith('._'):
                continue
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, base_path)
            size = os.path.getsize(file_path)
            records.append({
                "index": index,
                "filename": f,
                "size": format_size(size),
                "extension": os.path.splitext(f)[1],
                "relative_path": rel_path,
                "type": "file"
            })
            index += 1
    return records

def list_remote_files(client, base='/'):
    records = []
    queue = [base]
    index = 1
    while queue:
        current = queue.pop()
        contents = client.list(current)
        for item in contents:
            if item in (current, current.rstrip('/') + '/'):
                continue
            if item.startswith('.') or item.startswith('._'):
                continue
            full_path = os.path.join(current, item).replace("\\", "/")
            if client.check(full_path):
                try:
                    info = client.info(full_path)
                    size = int(info.get('size', 0))
                except Exception:
                    size = 0
                records.append({
                    "index": index,
                    "filename": os.path.basename(full_path),
                    "size": format_size(size),
                    "extension": os.path.splitext(full_path)[1],
                    "relative_path": full_path.lstrip('/'),
                    "type": "file"
                })
                index += 1
            else:
                queue.append(full_path)
    return records

def remove_remote_duplicates(client, local_files, remote_files, dry_run=False):
    local_set = set((f["filename"], f["size"]) for f in local_files if f["type"] == "file")
    removed = []

    for rf in tqdm(remote_files, desc="🗑️ 删除远程重复文件" if not dry_run else "🔎 模拟删除重复文件"):
        if rf["type"] != "file":
            continue
        if (rf["filename"], rf["size"]) in local_set:
            remote_path = "/" + rf["relative_path"]
            if dry_run:
                removed.append(remote_path)
            else:
                try:
                    client.clean(remote_path)
                    removed.append(remote_path)
                except Exception as e:
                    print(f"[跳过] 删除失败 {remote_path}: {e}")
    return removed

def remove_empty_dirs(client, path='/', dry_run=False):
    subitems = client.list(path)
    for item in subitems:
        full = os.path.join(path, item).replace("\\", "/")
        if full in (path, path.rstrip('/') + '/'):
            continue
        if item.startswith('.') or item.startswith('._'):
            continue
        if not client.check(full):
            remove_empty_dirs(client, full, dry_run=dry_run)
            try:
                if len(client.list(full)) == 1:
                    if dry_run:
                        print(f"🔎 模拟删除空目录：{full}")
                    else:
                        client.clean(full)
            except Exception as e:
                print(f"[跳过] 清空文件夹失败 {full}: {e}")

def write_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    args = parse_args()

    print("📂 正在遍历本地目录...")
    local_files = list_local_files(args.local)

    print("🌐 正在连接 WebDAV...")
    options = {
        'webdav_hostname': args.remote,
        'webdav_login': args.username,
        'webdav_password': args.password,
    }
    client = Client(options)

    print("📁 正在遍历远程目录...")
    remote_files = list_remote_files(client)

    print("🗑️ 正在处理重复文件...")
    removed = remove_remote_duplicates(client, local_files, remote_files, dry_run=args.dry_run)

    print("🧹 正在清理空文件夹...")
    remove_empty_dirs(client, dry_run=args.dry_run)

    print("💾 正在保存 JSON 文件...")
    os.makedirs(args.output, exist_ok=True)
    write_json(local_files, os.path.join(args.output, "local_files.json"))
    write_json(remote_files, os.path.join(args.output, "remote_files.json"))
    write_json(removed, os.path.join(args.output, "removed_files.json"))

    print("\n✅ 全部完成！结果输出至:", os.path.abspath(args.output))
    if args.dry_run:
        print("💡 本次为模拟运行，未执行任何删除操作。")

if __name__ == "__main__":
    main()
