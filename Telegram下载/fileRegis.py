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

def read_registered_files(output_path):
    """读取已注册的文件信息，并返回一个便于查询的字典"""
    file_register_path = os.path.join(output_path, "file_register.json")
    registered_files = {}
    if os.path.exists(file_register_path):
        with open(file_register_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for item in data:
                    if item.get("type") == "file":
                        # 使用文件名和大小作为键，便于快速查找
                        key = (item.get("filename"), item.get("size"))
                        registered_files[key] = item
            except json.JSONDecodeError:
                logging.warning("file_register.json 文件损坏或为空，将重新创建。")
    return registered_files

def compare_and_filter(local_files, target_files, registered_files):
    """
    比对文件并过滤已注册的文件。
    新逻辑：如果文件已在 registered_files 中，则不进行重复判断，直接跳过。
    """
    unique_files = []
    duplicate_files = []
    local_map = {(f['filename'], f['size']): f for f in local_files}

    for tf in target_files:
        # 首先检查文件是否已在注册列表中
        key = (tf['filename'], tf['size'])
        if key in registered_files:
            logging.info(f"文件已注册，跳过处理: {tf['relative_path']}")
            continue

        lf = local_map.get(key)
        if lf:
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
        # 这里需要 WebDAV 客户端的实际删除逻辑，目前代码中client.clean(path)是伪代码
        # client.clean(path)
        os.remove(path) # 针对本地文件进行删除

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

def save_json(folders, files, path, existing_data):
    """修改后的保存函数，将新数据与旧数据合并"""
    # 增加索引以避免重复
    max_folder_index = max([item.get('folder_index', 0) for item in existing_data]) if existing_data else 0 # 修复对空列表的max调用
    max_file_index = max([item.get('file_index', 0) for item in existing_data]) if existing_data else 0 # 修复对空列表的max调用

    folder_index = max_folder_index + 1
    file_index = max_file_index + 1
    for f in folders:
        f['folder_index'] = folder_index
        folder_index += 1
    for f in files:
        f['file_index'] = file_index
        file_index += 1

    # --- 最小改动开始 ---
    # 使用集合来存储已有的文件名和大小组合，以避免重复
    existing_keys = {(item.get("filename"), item.get("size")) for item in existing_data if item.get("type") == "file"}
    new_files_to_add = [f for f in files if (f.get("filename"), f.get("size")) not in existing_keys]

    all_items = existing_data + folders + new_files_to_add
    # --- 最小改动结束 ---

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)
    logging.info(f"文件注册已更新并保存: {path}")

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

    # 确保输出目录存在
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # ------------------ 修改部分开始 ------------------
    # 1. 读取已注册文件
    registered_files = read_registered_files(args.output)
    existing_file_register_path = os.path.join(args.output, "file_register.json")
    existing_data = []
    if os.path.exists(existing_file_register_path):
        with open(existing_file_register_path, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                logging.warning("现有 file_register.json 文件损坏，将重新创建。")
                existing_data = []
    # ------------------ 修改部分结束 ------------------

    local_folders, local_files = scan_local_directory(args.local)
    logging.info(f"本地文件夹扫描完成: {args.local}, 文件数: {len(local_files)}, 文件夹数: {len(local_folders)}")

    if args.localtarget:
        folders_target, files_target = scan_local_directory(args.localtarget)
        logging.info(f"比对目标文件夹扫描完成: {args.localtarget}, 文件数: {len(files_target)}, 文件夹数: {len(folders_target)}")
        
        # ------------------ 修改部分开始 ------------------
        # 2. 调用修改后的比较函数
        unique_files, duplicate_files = compare_and_filter(local_files, files_target, registered_files)

        # 3. 将 local 和 unique 合并写入 json，并传递现有数据
        # 传递 local_files，确保它们也被写入到注册文件中
        save_json(local_folders + folders_target, local_files + unique_files, existing_file_register_path, existing_data)
        # ------------------ 修改部分结束 ------------------

        # 写入 duplicate 文件
        with open(os.path.join(args.output, "duplicate.json"), 'w', encoding='utf-8') as f:
            json.dump(duplicate_files, f, indent=2, ensure_ascii=False)
        logging.info(f"重复文件数: {len(duplicate_files)}")

        # 删除目标目录中的重复文件
        for dup in duplicate_files:
            # 修改后的逻辑，对于本地文件直接使用 os.remove
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
        # 在这里应该添加WebDAV扫描逻辑，并将结果与registered_files进行比较
        logging.warning("WebDAV 利用部分未完成")
    else:
        logging.error("请指定 --remote 或 --localtarget")

if __name__ == '__main__':
    main()