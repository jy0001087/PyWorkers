import os
import json
import asyncio
from config import BASE_DIR, REGISTER_FILE
from file_indexer import calculate_file_hash, check_file_exists
from telegram_logger import get_main_logger

main_logger = get_main_logger()

# 异步锁，防止并发写入注册文件冲突
_register_lock = asyncio.Lock()

async def download_and_register(client, msg, folder, file_name, group_name, topic_name):
    """
    下载媒体文件并自动更新注册表
    
    Args:
        client: TelegramClient 实例
        msg: Telethon Message 对象
        folder: 目标文件夹路径
        file_name: 文件名（由调用方生成，确保一致性）
        group_name: 群组名称
        topic_name: 话题名称 (可选)
    """
    if not msg.file:
        return

    save_path = os.path.join(folder, file_name)

    # 1. 检查物理文件是否存在
    if os.path.exists(save_path):
        main_logger.debug(f"文件已存在，跳过: {file_name}")
        return

    # 2. 检查注册表 (防重复下载)
    if check_file_exists(file_name=file_name, group_name=group_name, topic_name=topic_name):
        main_logger.debug(f"文件已注册，跳过: {file_name}")
        return

    # 3. 执行下载
    try:
        main_logger.info(f"正在下载: {file_name}")
        
        start_time = asyncio.get_event_loop().time()

        async def progress_callback(current, total):
            nonlocal start_time
            elapsed = asyncio.get_event_loop().time() - start_time
            speed = (current / 1024 / 1024) / elapsed if elapsed > 0 else 0
            
            percent = (current / total * 100) if total > 0 else 0
            current_mb = current / 1024 / 1024
            total_mb = total / 1024 / 1024
            
            print(f"\r下载进度 [{file_name}]: {percent:.2f}% - {current_mb:.2f}/{total_mb:.2f} MB ({speed:.2f} MB/s)", end='', flush=True)

        # Telethon 自动处理断点续传
        await client.download_media(msg, file=save_path, progress_callback=progress_callback)
        print() # 换行
        main_logger.info(f"下载成功: {file_name}")

    except Exception as e:
        main_logger.error(f"下载失败 {file_name}: {e}")
        # 清理可能的损坏文件
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except:
                pass
        return

    # 4. 计算 Hash 并注册
    try:
        file_hash = calculate_file_hash(save_path)
        if not file_hash:
            main_logger.warning(f"计算 Hash 失败，无法注册: {file_name}")
            return
        
        file_info = {
            'file_name': file_name,
            'group_name': group_name,
            'topic_name': topic_name,
            'file_hash': file_hash,
            'file_path': save_path,
            'file_size': os.path.getsize(save_path)
        }

        await _update_register(file_info)
        main_logger.info(f"已注册: {file_name}")
        
    except Exception as e:
        main_logger.error(f"注册文件失败 {file_name}: {e}")

async def _update_register(file_info):
    """
    线程安全地更新注册文件
    """
    async with _register_lock:
        data = {}
        if os.path.exists(REGISTER_FILE):
            try:
                with open(REGISTER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}

        group = file_info['group_name']
        topic = file_info['topic_name']

        if group not in data:
            data[group] = {}
        if topic not in data[group]:
            data[group][topic] = []

        # 再次检查防重
        if not any(f.get('file_name') == file_info['file_name'] for f in data[group][topic]):
            data[group][topic].append(file_info)

        # 确保目录存在
        os.makedirs(os.path.dirname(REGISTER_FILE), exist_ok=True)
        
        with open(REGISTER_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
