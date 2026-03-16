import os
import re
import json
import asyncio
import logging
import logging.handlers
from telethon import TelegramClient
from telethon.tl.types import (
    InputMessagesFilterDocument,
    InputMessagesFilterVideo,
    InputMessagesFilterMusic,
    InputMessagesFilterVoice
)

# ======================== 配置 ========================
API_ID = 25270021
API_HASH = 'e27d91ad37959d54eb5c1d454d567afa'
SESSION = 'session'
BASE_DIR = os.path.expanduser('//Volumes/壶中境/TGDownload')
REGISTER_FILE = os.path.expanduser('/Users/rfs/Documents/CodingWorkSpace/PyWorkers/Telegram下载/output/file_register.json')

GROUPS = [
    -1003764726480, 
    -1001985478835,
    -1003308333812,
    -1003031629535,
    -1003488153527,
    'kunyeatm',
    -1002210091863,
    'Y762XkSZPrRkMGE9',
    -1001796027030,
    'eduojiango',
    'cukou12',
    -1001662972970,
    -1002471335106,
    -1001971709345,
    -1002284333043,
    -1002274802303,
    -1002434627718,
    -1001697384627,
    -1001693153191,
    -1001745485154,
    -1002491725238,
]

USE_PROXY = True
PROXY = ('socks5', '127.0.0.1', 10800)
CONCURRENCY = 4
MAX_MSG_PER_TYPE = 200
# =====================================================

# 全局锁保护注册表写入
register_lock = None

MIME_MAP = {
    'image/jpeg': '.jpg',
    'video/mp4': '.mp4',
    'audio/mpeg': '.mp3',
    'application/zip': '.zip',
}

def safe_name(name: str, max_bytes=200) -> str:
    """安全的文件名处理"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.replace(' ', '_'))
    b = name.encode('utf-8')
    if len(b) > max_bytes:
        name = b[:max_bytes].decode('utf-8', errors='ignore')
    return name or 'unnamed'

def build_msg_group_prefix(msg) -> str:
    """从消息中提取分组前缀（如 grouped_id）"""
    # 群组内的小分组（如相册中的同组媒体）通常用 grouped_id 表示
    grouped_id = getattr(msg, 'grouped_id', None)
    if grouped_id:
        return f"[{grouped_id}]_"
    # Telethon 有时可能在 media_group_id 或其它属性内
    media_group_id = getattr(msg, 'media_group_id', None)
    if media_group_id:
        return f"[{media_group_id}]_"
    return ''


def load_register(path: str) -> set:
    """加载已注册文件列表"""
    try:
        if not os.path.exists(path):
            return set()
        
        registered = set()
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('type') == 'file' and entry.get('filename'):
                        registered.add(entry.get('filename'))
                except json.JSONDecodeError:
                    continue
        return registered
    except Exception as e:
        print(f"[ERROR] 加载注册表失败: {e}")
        return set()

def build_logger(chat_dir: str):
    """为每个 chat 创建独立的 logger"""
    logger_name = os.path.abspath(chat_dir)
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(chat_dir, 'log.log'),
        maxBytes=50*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

async def download(sema, msg, folder, logger, registered, max_retries=3):
    """下载文件，支持重试"""
    async with sema:
        if not msg.file:
            logger.info(f"[SKIP] Message {msg.id} has no file.")
            return

        # 获取原文件名和扩展名
        orig_fname = msg.file.name or f"{msg.id}{MIME_MAP.get(msg.file.mime_type, '')}"
        
        # 旧文件名（不含 msg_text）
        old_fname = safe_name(orig_fname)
        
        # 提取消息文本内容（兼容不同消息类型）
        msg_text = ""
        if hasattr(msg, 'text') and msg.text:
            msg_text = msg.text.strip()
        elif hasattr(msg, 'message') and msg.message:
            msg_text = msg.message.strip()
        
        # 生成分组前缀
        group_prefix = build_msg_group_prefix(msg)

        # 生成新文件名
        if msg_text:
            msg_text_safe = safe_name(msg_text[:100])
            fname = safe_name(f"{group_prefix}{msg_text_safe}-{orig_fname}")
        else:
            fname = safe_name(f"{group_prefix}{orig_fname}")
        
        # 同时检查新旧文件名是否已存在或已注册
        file_path = os.path.join(folder, fname)
        old_file_path = os.path.join(folder, old_fname)
        
        if fname in registered or os.path.exists(file_path):
            logger.debug(f"[SKIP] {fname} (已注册或存在)")
            return
        
        if old_fname != fname and (old_fname in registered or os.path.exists(old_file_path)):
            logger.debug(f"[SKIP] {fname} (旧版本已存在: {old_fname})")
            return

        total_size = msg.file.size
        logger.info(f"[START] {fname} (Total size: {total_size / 1024 / 1024:.2f} MB)")
        
        async def progress_callback(current, total):
            progress = int(current * 100 / total)
            print(f"\r[PROGRESS] {fname}: {progress}% - {current / 1024 / 1024:.2f}/{total / 1024 / 1024:.2f} MB", end='', flush=True)
        
        # 重试逻辑
        for attempt in range(max_retries):
            try:
                await msg.download_media(file=file_path, progress_callback=progress_callback)
                
                # 验证文件大小
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size == total_size:
                        print()  # 换行
                        logger.info(f"[DONE] {fname}")
                        
                        # 更新注册表（线程安全）
                        registered.add(fname)
                        async with register_lock:
                            with open(REGISTER_FILE, 'a', encoding='utf-8') as f:
                                json.dump({'filename': fname, 'type': 'file'}, f, ensure_ascii=False)
                                f.write('\n')
                        return
                    else:
                        # 文件大小不匹配，删除并重试
                        try:
                            os.remove(file_path)
                        except:
                            pass
                        logger.warning(f"[RETRY] {fname} 文件大小不匹配 ({file_size}/{total_size}), 重试...")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise Exception(f"文件大小不匹配，已重试 {max_retries} 次")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print()
                logger.error(f"[ERROR] 下载失败 (尝试 {attempt + 1}/{max_retries}): {fname} - {type(e).__name__}: {e}")
                
                # 清理失败的文件
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[WAIT] {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[FAILED] {fname} 已放弃，超过最大重试次数")

async def get_all_messages(client, chat, filters):
    """获取所有指定类型的消息（分页）"""
    all_messages = []
    seen_message_ids = set()
    
    for f in filters:
        offset_id = 0
        while True:
            try:
                messages = await client.get_messages(
                    chat, 
                    limit=MAX_MSG_PER_TYPE,
                    offset_id=offset_id,
                    filter=f,
                    reverse=False
                )
                if not messages:
                    break
                
                # 过滤重复消息
                for msg in messages:
                    if msg.id not in seen_message_ids:
                        all_messages.append(msg)
                        seen_message_ids.add(msg.id)
                
                if len(messages) < MAX_MSG_PER_TYPE:
                    break
                
                offset_id = messages[-1].id
            except Exception as e:
                print(f"[ERROR] 获取消息失败: {e}")
                break
    
    return all_messages

async def update_register_file(new_fname: str, old_fname: str):
    """更新 file_register.json，替换旧文件名为新文件名"""
    async with register_lock:
        try:
            # 读取现有注册表
            lines = []
            if os.path.exists(REGISTER_FILE):
                with open(REGISTER_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            # 构建新的注册表内容
            new_lines = []
            found = False
            for line in lines:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('filename') == old_fname:
                        entry['filename'] = new_fname
                        new_lines.append(json.dumps(entry, ensure_ascii=False) + '\n')
                        found = True
                    else:
                        new_lines.append(line)
                except json.JSONDecodeError:
                    new_lines.append(line)

            # 如果未找到旧文件名，直接添加新文件名
            if not found:
                new_lines.append(json.dumps({'filename': new_fname, 'type': 'file'}, ensure_ascii=False) + '\n')

            # 写回文件
            with open(REGISTER_FILE, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"[ERROR] 更新注册表失败: {e}")

async def rename_existing_files_fast(all_messages, folder, logger, registered):
    """快速重命名文件（使用现有消息列表）"""
    if not all_messages:
        return
    
    # 构建消息字典，用 safe_name 处理后的原始文件名作为键
    msg_dict = {}
    for msg in all_messages:
        if not msg.file:
            continue
        orig_fname = msg.file.name or f"{msg.id}{MIME_MAP.get(msg.file.mime_type, '')}"
        safe_orig = safe_name(orig_fname)
        # 避免重复，用 msg.id 作为辅助键
        if safe_orig not in msg_dict:
            msg_dict[safe_orig] = (msg, orig_fname)

    # 遍历本地文件夹
    try:
        filenames = os.listdir(folder)
    except Exception as e:
        logger.error(f"[ERROR] 读取文件夹失败: {e}")
        return
    
    for filename in filenames:
        if filename.startswith('.') or filename.endswith('.log') or filename.endswith('.tmp'):
            continue
        
        file_path = os.path.join(folder, filename)
        if not os.path.isfile(file_path):
            continue
        
        # 检查文件是否已注册
        if filename in registered:
            continue

        # 查找对应消息
        if filename not in msg_dict:
            continue

        msg, orig_fname = msg_dict[filename]
        
        # 提取消息文本内容
        msg_text = ""
        if hasattr(msg, 'text') and msg.text:
            msg_text = msg.text.strip()
        elif hasattr(msg, 'message') and msg.message:
            msg_text = msg.message.strip()
        
        if not msg_text:
            continue

        group_prefix = build_msg_group_prefix(msg)
        msg_text_safe = safe_name(msg_text[:100])
        new_fname = safe_name(f"{group_prefix}{msg_text_safe}-{orig_fname}")
        new_file_path = os.path.join(folder, new_fname)

        # 如果新文件名相同，跳过
        if new_fname == filename:
            continue

        # 检查新文件名是否已存在或已注册
        if os.path.exists(new_file_path) or new_fname in registered:
            logger.debug(f"[RENAME] {new_fname} 已存在，跳过 {filename}")
            continue

        # 重命名文件
        try:
            os.rename(file_path, new_file_path)
            logger.info(f"[RENAME] {filename} -> {new_fname}")
            
            # 更新内存注册表和文件
            registered.discard(filename)
            registered.add(new_fname)
            await update_register_file(new_fname, filename)
        except Exception as e:
            logger.error(f"[RENAME] 重命名失败 {filename}: {e}")

async def main():
    global register_lock
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(REGISTER_FILE), exist_ok=True)
    
    # 初始化全局锁
    register_lock = asyncio.Lock()
    
    client = TelegramClient(SESSION, API_ID, API_HASH, proxy=PROXY if USE_PROXY else None)
    await client.start()
    registered = load_register(REGISTER_FILE)
    sema = asyncio.Semaphore(CONCURRENCY)
    
    # 全局去重
    seen_ids = set()

    for gid in GROUPS:
        try:
            chat = await client.get_entity(gid)
        except Exception as e:
            print(f"[ERROR] 无法访问 {gid}: {e}")
            continue

        folder = os.path.join(BASE_DIR, safe_name(chat.title or str(chat.id)))
        os.makedirs(folder, exist_ok=True)
        logger = build_logger(folder)

        # 获取所有消息（仅一次）
        logger.info("=== 开始获取消息 ===")
        all_messages = await get_all_messages(
            client,
            chat,
            (InputMessagesFilterDocument, InputMessagesFilterVideo,
             InputMessagesFilterMusic, InputMessagesFilterVoice)
        )
        logger.info(f"获取到 {len(all_messages)} 条消息")

        if not all_messages:
            logger.warning("未获取到任何消息")
            continue

        # 先重命名已存在的旧文件
        logger.info("=== 开始重命名已下载文件 ===")
        await rename_existing_files_fast(all_messages, folder, logger, registered)

        # 再下载新文件
        logger.info("=== 开始下载新文件 ===")
        msgs = []
        for msg in all_messages:
            msg_key = (gid, msg.id)
            if msg_key not in seen_ids:
                msgs.append(msg)
                seen_ids.add(msg_key)

        if msgs:
            await asyncio.gather(*[download(sema, m, folder, logger, registered) for m in msgs])
        else:
            logger.info("无新文件需要下载")
        
        logger.info("=== 完成 ===")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())