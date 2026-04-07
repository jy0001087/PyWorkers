# scan_existing_files.py
import os
import json
import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from config import BASE_DIR, REGISTER_FILE
from telegram_logger import get_main_logger

# 获取主日志记录器
main_logger = get_main_logger()

def calculate_file_hash(file_path, chunk_size=8192):
    """
    计算文件的MD5 hash值
    
    Args:
        file_path (str): 文件路径
        chunk_size (int): 读取块大小
    
    Returns:
        str: 文件的MD5 hash值
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        main_logger.error(f"计算文件 {file_path} 的hash值时出错: {e}")
        return None

def is_media_file(file_path):
    """
    判断是否为媒体文件（视频/音频）
    """
    ext = os.path.splitext(file_path)[1].lower()
    media_ext = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.ts', '.m4v',
                 '.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
    return ext in media_ext

def check_media_integrity(file_path):
    """
    使用 ffprobe 检查媒体文件完整性
    
    Returns:
        bool: True 表示文件完整可播放，False 表示损坏
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
        main_logger.warning(f"媒体文件不完整: {file_path}")
        return False
    except subprocess.TimeoutExpired:
        main_logger.error(f"ffprobe 超时: {file_path}")
        return False
    except FileNotFoundError:
        main_logger.warning("ffprobe 未安装，跳过媒体完整性检查")
        return True
    except Exception as e:
        main_logger.error(f"检查媒体完整性失败 {file_path}: {e}")
        return False

def remove_file_from_register(existing_data, file_name, group_name, topic_name):
    """
    从注册数据中移除指定文件
    """
    if group_name not in existing_data:
        return False
    
    removed = False
    if topic_name and topic_name in existing_data[group_name]:
        original_len = len(existing_data[group_name][topic_name])
        existing_data[group_name][topic_name] = [
            f for f in existing_data[group_name][topic_name]
            if f.get('file_name') != file_name
        ]
        if len(existing_data[group_name][topic_name]) < original_len:
            removed = True
    else:
        for topic_key in list(existing_data[group_name].keys()):
            original_len = len(existing_data[group_name][topic_key])
            existing_data[group_name][topic_key] = [
                f for f in existing_data[group_name][topic_key]
                if f.get('file_name') != file_name
            ]
            if len(existing_data[group_name][topic_key]) < original_len:
                removed = True
    
    if not existing_data[group_name].get(topic_name or '') and topic_name in existing_data[group_name]:
        del existing_data[group_name][topic_name]
    
    return removed

def get_group_and_topic_from_path(file_path, base_path):
    """
    从文件路径中提取群组名称和话题名称
    
    Args:
        file_path (str): 文件完整路径
        base_path (str): 基础路径
    
    Returns:
        tuple: (group_name, topic_name) 或 (None, None)
    """
    try:
        relative_path = os.path.relpath(file_path, base_path)
        path_parts = relative_path.split(os.sep)
        
        if len(path_parts) >= 2:
            group_name = path_parts[0]
            topic_name = path_parts[1] if len(path_parts) >= 3 else None
            return group_name, topic_name
        else:
            return None, None
    except Exception as e:
        main_logger.error(f"解析路径 {file_path} 时出错: {e}")
        return None, None

def scan_existing_files():
    """
    递归扫描存量文件路径，收集文件信息并更新regist_file.json
    
    Returns:
        int: 成功处理的文件数量
    """
    main_logger.info("开始扫描存量文件...")
    
    # 读取现有的注册文件
    existing_data = {}
    if os.path.exists(REGISTER_FILE):
        try:
            with open(REGISTER_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            main_logger.error(f"读取现有注册文件失败: {e}")
            existing_data = {}
    
    # 确保基础目录存在
    if not os.path.exists(BASE_DIR):
        main_logger.error(f"基础目录不存在: {BASE_DIR}")
        return 0
    
    # 先统计总文件数以显示进度
    total_files = 0
    for root, dirs, files in os.walk(BASE_DIR):
        total_files += len(files)
    
    main_logger.info(f"总共需要扫描 {total_files} 个文件")
    
    # 统一转为字符串用于比较（Path 与 str 比较永远为 False）
    register_file_str = str(REGISTER_FILE)
    base_dir_str = str(BASE_DIR)
    
    main_logger.info(f"注册文件路径: {register_file_str}")
    main_logger.info(f"注册文件已存在: {os.path.exists(register_file_str)}")
    main_logger.info(f"现有注册数据群组数: {len(existing_data)}")
    
    file_count = 0
    new_file_count = 0
    removed_count = 0
    processed_count = 0
    skipped_exists = 0
    last_saved_new_count = 0
    
    def save_register():
        nonlocal last_saved_new_count
        try:
            os.makedirs(os.path.dirname(register_file_str), exist_ok=True)
            with open(register_file_str, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            main_logger.info(f"注册文件已保存，累计新增 {new_file_count} 个，移除 {removed_count} 个")
            last_saved_new_count = new_file_count
        except Exception as e:
            main_logger.error(f"保存注册文件失败: {e}")
    
    # 统一转为字符串用于比较（Path 与 str 比较永远为 False）
    register_file_str = str(REGISTER_FILE)
    base_dir_str = str(BASE_DIR)
    
    # 递归扫描所有文件
    for root, dirs, files in os.walk(base_dir_str):
        # 过滤掉隐藏目录（如 .Spotlight-V100, .Trash 等）
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        # 跳过注册文件本身
        if root == base_dir_str and os.path.basename(register_file_str) in files:
            continue
            
        for file in files:
            # 忽略 macOS 自动生成的隐藏文件（如 .DS_Store, ._filename）
            if file.startswith('.'):
                continue
            
            file_path = os.path.join(root, file)
            
            # 跳过注册文件
            if file_path == register_file_str:
                continue
            
            # 提取群组和话题信息
            group_name, topic_name = get_group_and_topic_from_path(file_path, BASE_DIR)
            
            if not group_name:
                main_logger.warning(f"无法解析文件路径 {file_path} 的群组信息")
                continue
            
            # 对媒体文件进行完整性检查
            if is_media_file(file_path):
                if not check_media_integrity(file_path):
                    try:
                        file_size = os.path.getsize(file_path)
                        file_hash = None
                        # 尝试从现有记录中获取 hash
                        if group_name in existing_data:
                            for t_files in existing_data[group_name].values():
                                for f_info in t_files:
                                    if f_info.get('file_name') == file:
                                        file_hash = f_info.get('file_hash')
                                        break
                                if file_hash:
                                    break
                        
                        main_logger.warning(f"检测到疑似损坏的媒体文件: {file_path}")
                        main_logger.warning(f"  文件名: {file}")
                        main_logger.warning(f"  群组: {group_name}, 话题: {topic_name}")
                        main_logger.warning(f"  大小: {file_size} bytes")
                        main_logger.warning(f"  Hash: {file_hash}")
                        
                        # 移入隔离区
                        corrupted_dir = os.path.join(BASE_DIR, '_corrupted')
                        os.makedirs(corrupted_dir, exist_ok=True)
                        
                        dest_path = os.path.join(corrupted_dir, f"{group_name}_{file}")
                        if os.path.exists(dest_path):
                            dest_path = f"{dest_path}_{os.getpid()}"
                            
                        shutil.move(file_path, dest_path)
                        remove_file_from_register(existing_data, file, group_name, topic_name)
                        removed_count += 1
                        main_logger.info(f"已移动损坏文件: {file_path} -> {dest_path}")
                    except Exception as e:
                        main_logger.error(f"移动损坏文件失败 {file_path}: {e}")
                    processed_count += 1
                    continue
            
            # 检查是否已存在相同文件（基于组名、话题名、文件名）
            exists = False
            if group_name in existing_data:
                if topic_name in existing_data[group_name]:
                    for existing_file in existing_data[group_name][topic_name]:
                        if existing_file.get('file_name') == file:
                            exists = True
                            break
                else:
                    # 检查是否在该群组的任何话题中存在同名文件
                    for topic_key, topic_files in existing_data[group_name].items():
                        for existing_file in topic_files:
                            if existing_file.get('file_name') == file:
                                exists = True
                                break
                        if exists:
                            break
            
            # 如果文件已存在，则跳过计算hash值
            if exists:
                file_count += 1
                skipped_exists += 1
                main_logger.debug(f"文件已存在，跳过处理: {file_path}")
            else:
                # 计算文件hash值
                file_hash = calculate_file_hash(file_path)
                if not file_hash:
                    continue
                
                # 构建文件信息
                file_info = {
                    'file_name': file,
                    'group_name': group_name,
                    'topic_name': topic_name,
                    'file_hash': file_hash,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path)
                }
                
                # 添加到注册数据中
                if group_name not in existing_data:
                    existing_data[group_name] = {}
                
                if topic_name not in existing_data[group_name]:
                    existing_data[group_name][topic_name] = []
                
                existing_data[group_name][topic_name].append(file_info)
                file_count += 1
                new_file_count += 1
            
            processed_count += 1
            if processed_count % 10 == 0:
                main_logger.info(f"已处理 {processed_count}/{total_files} 个文件")
            
            if new_file_count - last_saved_new_count >= 100:
                save_register()
    
    # 扫描完成后最终写入
    main_logger.info(f"扫描统计: 总处理 {file_count}, 新增 {new_file_count}, 已存在跳过 {skipped_exists}, 损坏移除 {removed_count}")
    if new_file_count > last_saved_new_count or removed_count > 0:
        save_register()
    else:
        main_logger.info(f"无新增或损坏文件，跳过写入注册文件，共扫描 {file_count} 个文件")
    
    return file_count

def check_file_exists(file_name=None, group_name=None, topic_name=None, file_hash=None):
    """
    检查文件是否存在
    
    Args:
        file_name (str): 文件名
        group_name (str): 群组名称
        topic_name (str): 话题名称
        file_hash (str): 文件hash值
    
    Returns:
        bool: 文件是否存在
    """
    # 读取现有的注册文件
    existing_data = {}
    if not os.path.exists(REGISTER_FILE):
        return False
    
    try:
        with open(REGISTER_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except Exception as e:
        main_logger.error(f"读取注册文件失败: {e}")
        return False
    
    # 如果提供了hash值，直接通过hash值查找
    if file_hash:
        for group_key, group_data in existing_data.items():
            for topic_key, topic_files in group_data.items():
                for file_info in topic_files:
                    if file_info.get('file_hash') == file_hash:
                        return True
        return False
    
    # 如果提供了文件名和群组信息，进行组合查找
    if file_name and group_name:
        if group_name in existing_data:
            if topic_name:
                # 指定话题
                if topic_name in existing_data[group_name]:
                    for file_info in existing_data[group_name][topic_name]:
                        if file_info.get('file_name') == file_name:
                            return True
            else:
                # 不指定话题，遍历所有话题
                for topic_key, topic_files in existing_data[group_name].items():
                    for file_info in topic_files:
                        if file_info.get('file_name') == file_name:
                            return True
        return False
    
    return False

def get_file_info(file_name=None, group_name=None, topic_name=None, file_hash=None):
    """
    获取文件信息
    
    Args:
        file_name (str): 文件名
        group_name (str): 群组名称
        topic_name (str): 话题名称
        file_hash (str): 文件hash值
    
    Returns:
        dict: 文件信息，如果未找到返回None
    """
    # 读取现有的注册文件
    existing_data = {}
    if not os.path.exists(REGISTER_FILE):
        return None
    
    try:
        with open(REGISTER_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except Exception as e:
        main_logger.error(f"读取注册文件失败: {e}")
        return None
    
    # 如果提供了hash值，直接通过hash值查找
    if file_hash:
        for group_key, group_data in existing_data.items():
            for topic_key, topic_files in group_data.items():
                for file_info in topic_files:
                    if file_info.get('file_hash') == file_hash:
                        return file_info
        return None
    
    # 如果提供了文件名和群组/话题信息，进行组合查找
    if file_name and group_name:
        if group_name in existing_data:
            if topic_name:
                # 指定话题
                if topic_name in existing_data[group_name]:
                    for file_info in existing_data[group_name][topic_name]:
                        if file_info.get('file_name') == file_name:
                            return file_info
            else:
                # 不指定话题，遍历所有话题
                for topic_key, topic_files in existing_data[group_name].items():
                    for file_info in topic_files:
                        if file_info.get('file_name') == file_name:
                            return file_info
    return None

def main():
    """主函数"""
    main_logger.info("存量文件扫描程序启动")
    try:
        count = scan_existing_files()
        main_logger.info(f"存量文件扫描完成，共处理 {count} 个文件")
        return 0
    except Exception as e:
        main_logger.error(f"扫描过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())