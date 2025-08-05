import os
import argparse
import json
import logging
from webdav3.client import Client
from urllib.parse import urlparse
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fileRegis.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_file_info(base_path, root, file, is_folder):
    rel_path = os.path.relpath(os.path.join(root, file), base_path)
    full_path = os.path.join(root, file)
    size = os.path.getsize(full_path) if not is_folder else sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, dn, filenames in os.walk(full_path)
        for f in filenames
    )
    return {
        "filename": file,
        "size": f"{size / 1024:.2f} KB",
        "extension": "<folder>" if is_folder else os.path.splitext(file)[1],
        "relative_path": rel_path,
        "type": "folder" if is_folder else "file",
        "absolute_path": full_path  # 便于后续输出重复结果
    }

def scan_local_directory(path):
    folders, files = [], []
    for root, dirs, filenames in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('._')]
        filenames = [f for f in filenames if not f.startswith('.') and not f.startswith('._')]
        for d in dirs:
            folders.append(get_file_info(path, root, d, is_folder=True))
        for f in filenames:
            files.append(get_file_info(path, root, f, is_folder=False))
    return folders, files

def compare_and_filter(local_files, target_files):
    unique_files = []
    duplicate_files = []
    local_map = {f['filename']: f for f in local_files}
    for tf in target_files:
        lf = local_map.get(tf['filename'])
        if lf and lf['size'] == tf['size']:
            tf['duplicate_of'] = lf['absolute_path']
            duplicate_files.append(tf)
        else:
            unique_files.append(tf)
    return unique_files, duplicate_files

def delete_remote_file(client, path, dry_run):
    if dry_run:
        logging.info(f"[DRY-RUN] 清除重复文件: {path}")
    else:
        logging.info(f"正在删除重复文件: {path}")
        client.clean(path)

def delete_empty_folders(path, dry_run):
    for root, dirs, files in os.walk(path, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                if dry_run:
                    logging.info(f"[DRY-RUN] 清除空文件夹: {dir_path}")
                else:
                    os.rmdir(dir_path)
                    logging.info(f"删除空文件夹: {dir_path}")

def save_json(folders, files, path):
    folder_index, file_index = 1, 1
    for f in folders:
        f['folder_index'] = folder_index
        folder_index += 1
    for f in files:
        f['file_index'] = file_index
        file_index += 1
    all_items = folders + files
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)
    logging.info(f"文件注册已保存: {path}")

def main():
    parser = argparse.ArgumentParser(description="比对相同文件并删除重复")
    parser.add_argument('--local', required=True, help="本地目录")
    parser.add_argument('--remote', help="WebDAV 路径")
    parser.add_argument('--localtarget', help="用于比对的本地目标目录")
    parser.add_argument('--username', help="WebDAV 用户名")
    parser.add_argument('--password', help="WebDAV 密码")
    parser.add_argument('--output', required=True, help="输出目录")
    parser.add_argument('--dry-run', action='store_true', help="模拟操作")
    args = parser.parse_args()

    local_folders, local_files = scan_local_directory(args.local)
    logging.info(f"本地文件夹扫描完成: {args.local}, 文件数: {len(local_files)}, 文件夹数: {len(local_folders)}")

    if args.localtarget:
        folders_target, files_target = scan_local_directory(args.localtarget)
        logging.info(f"比对目标文件夹扫描完成: {args.localtarget}, 文件数: {len(files_target)}, 文件夹数: {len(folders_target)}")
        unique_files, duplicate_files = compare_and_filter(local_files, files_target)

        # 将 local 和 unique 合并写入 json
        save_json(local_folders + folders_target, local_files + unique_files, os.path.join(args.output, "file_register.json"))

        # 写入 duplicate 文件
        with open(os.path.join(args.output, "duplicate.json"), 'w', encoding='utf-8') as f:
            json.dump(duplicate_files, f, indent=2, ensure_ascii=False)
        logging.info(f"重复文件数: {len(duplicate_files)}")

        # 删除目标目录中的重复文件
        for dup in duplicate_files:
            delete_remote_file(None, dup['absolute_path'], args.dry_run)

        # 删除目标目录中空文件夹
        delete_empty_folders(args.localtarget, args.dry_run)

    elif args.remote:
        options = {
            'webdav_hostname': args.remote,
            'webdav_login': args.username,
            'webdav_password': args.password
        }
        client = Client(options)
        client.verify = False
        # TODO: 读取 WebDAV 内容，类似扫描本地同样处理
        logging.warning("WebDAV 利用部分未完成")
    else:
        logging.error("请指定 --remote 或 --localtarget")

if __name__ == '__main__':
    main()
