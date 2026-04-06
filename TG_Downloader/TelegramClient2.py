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
    InputMessagesFilterVoice,
    Channel
)
from telethon.tl.functions.channels import GetForumTopicsRequest

# ======================== 配置 ========================
API_ID = 25270021
API_HASH = 'e27d91ad37959d54eb5c1d454d567afa'
SESSION = 'session'
BASE_DIR = os.path.expanduser('/Users/rfs/Documents/TGDownload')
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

# Telegram 下载/TelegramClient2.py

async def get_channel_folders(client):
    """
    获取用户的频道文件夹分类（Telegram Folders）
    注意：这需要 Telegram API 支持，且可能因权限限制无法获取
    """
    try:
        from telethon.tl.functions.messages import GetDialogsRequest
        from telethon.tl.types import Folder
        
        # 获取所有对话文件夹
        dialogs = await client.get_dialogs()
        folders = await client.get_folders() if hasattr(client, 'get_folders') else []
        
        print(f"[INFO] 获取到 {len(folders)} 个文件夹分类")
        return folders
    except Exception as e:
        print(f"[ERROR] 获取文件夹分类失败: {e}")
        return []


async def analyze_message_categories(client, chat, messages=None):
    """
    基于消息内容分析频道的内部分类
    通过关键词、媒体类型等对消息进行自动分类
    """
    try:
        # 如果未提供消息列表，则获取最近的消息
        if messages is None:
            messages = await client.get_messages(chat, limit=500)
        
        if not messages:
            print(f"[INFO] 没有消息可以分析")
            return {}
        
        # 定义分类规则
        categories = {
            '视频': 0,
            '音频': 0,
            '文档': 0,
            '图片': 0,
            '语音': 0,
            '普通消息': 0,
            '链接': 0,
            '其他': 0
        }
        
        for msg in messages:
            if msg.file:
                mime_type = msg.file.mime_type or ''
                if 'video' in mime_type:
                    categories['视频'] += 1
                elif 'audio' in mime_type:
                    categories['音频'] += 1
                elif 'image' in mime_type:
                    categories['图片'] += 1
                elif 'voice' in mime_type:
                    categories['语音'] += 1
                elif 'pdf' in mime_type or 'document' in mime_type:
                    categories['文档'] += 1
                else:
                    categories['其他'] += 1
            elif msg.text:
                text = msg.text.lower()
                if any(link in text for link in ['http://', 'https://', 'tg://']):
                    categories['链接'] += 1
                else:
                    categories['普通消息'] += 1
            else:
                categories['其他'] += 1
        
        total = len(messages)
        print(f"[INFO] 频道内容分析 (共 {total} 条消息):")
        for category, count in categories.items():
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  - {category}: {count} ({percentage:.1f}%)")
        
        return categories
        
    except Exception as e:
        print(f"[ERROR] 分析消息分类失败: {e}")
        return {}

def safe_name(name: str, max_bytes=200) -> str:
    """安全的文件名处理"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.replace(' ', '_'))
    b = name.encode('utf-8')
    if len(b) > max_bytes:
        name = b[:max_bytes].decode('utf-8', errors='ignore')
    return name or 'unnamed'

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


def _tme_chat_id_from_entity(entity):
    """
    频道链接在 t.me/c/ 下的 ID 计算：
    Telethon entity.id 可能是 -1003764726480
    t.me/c/: 3764726480 (去掉 -100 前缀)
    """
    cid = getattr(entity, 'id', None)
    if cid is None:
        return None
    s = str(abs(int(cid)))
    if s.startswith('100'):
        # Telethon 超级群/频道 id 前缀 100
        return s[3:]
    return s


async def get_channel_topics(client, chat, sample_limit=200, thread_message_limit=5):
    """
    1) 获取 channel entity
    2) 如果是论坛频道，先尝试获取论坛 topics 列表
    3) 取 sample_messages 的 message_thread_id
    4) 统计每个 thread 的消息数，生成 t.me/c 链接
    """
    print(f"[DEBUG] 开始获取 {chat} 的 topics")
    entity = await client.get_entity(chat)
    print(f"[DEBUG] Entity 类型: {type(entity).__name__}, ID: {getattr(entity, 'id', None)}, Title: {getattr(entity, 'title', None)}")
    if not isinstance(entity, Channel):
        print(f"[DEBUG] 非 Channel 类型，跳过 topics 获取")
        return []

    # 检查是否是论坛频道
    is_forum = getattr(entity, 'forum', False)
    print(f"[DEBUG] is_forum: {is_forum}")

    topics = []

    if is_forum:
        print(f"[DEBUG] 是论坛频道，尝试获取论坛 topics 列表")
        try:
            # 使用 GetForumTopicsRequest 获取论坛 topics
            result = await client(GetForumTopicsRequest(
                channel=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100  # 获取前100个topics
            ))
            forum_topics = result.topics
            print(f"[DEBUG] 获取到论坛 topics: {len(forum_topics) if forum_topics else 0}")
            if forum_topics:
                tme_chat_id = _tme_chat_id_from_entity(entity)
                for topic in forum_topics:
                    topic_id = getattr(topic, 'id', None)
                    if topic_id:
                        topic_link = f"https://t.me/c/{tme_chat_id}/{topic_id}" if tme_chat_id else None
                        topics.append({
                            'topic_id': topic_id,
                            'topic_title': getattr(topic, 'title', ''),
                            'topic_link': topic_link,
                            'message_count': getattr(topic, 'count', 0),
                        })
                print(f"[DEBUG] 从论坛 topics 列表获取到 {len(topics)} 个 topics")
        except Exception as e:
            print(f"[DEBUG] 获取论坛 topics 列表失败: {e}")

    # 如果没有从论坛 topics 列表获取到，尝试从消息中提取 thread_id
    if not topics:
        print(f"[DEBUG] 从论坛 topics 列表未获取到，尝试从消息中提取 thread_id")
        # 取所有 message，thread_id 做话题分类
        print(f"[DEBUG] 获取 sample_messages, limit={sample_limit}")
        sample_messages = await client.get_messages(chat, limit=sample_limit)
        print(f"[DEBUG] 获取到 {len(sample_messages)} 条消息")
        
        thread_ids = [m.message_thread_id for m in sample_messages if getattr(m, 'message_thread_id', None)]
        print(f"[DEBUG] 找到的 thread_ids: {thread_ids}")
        topic_ids = sorted(set(thread_ids))
        print(f"[DEBUG] 去重后的 topic_ids: {topic_ids}")

        if topic_ids:
            # 生成基础 t.me 链接 ID
            tme_chat_id = _tme_chat_id_from_entity(entity)
            print(f"[DEBUG] 计算的 t.me chat_id: {tme_chat_id}")

            for tpid in topic_ids:
                print(f"[DEBUG] 处理 topic_id: {tpid}")
                # 可选：每个 thread 做一个快速 count
                count = 0
                if tpid:
                    try:
                        msgs = await client.get_messages(chat, limit=1, message_thread_id=tpid)
                        print(f"[DEBUG] topic {tpid} 的消息: {len(msgs) if msgs else 0}")
                        # Telethon 会返回当前 thread 的最新消息，若有则算作存在
                        if msgs:
                            # 为了避免额外耗时，只返回 thread 中存在即认为 >0
                            count = await client.get_messages(chat, limit=1, message_thread_id=tpid).total if hasattr(msgs, 'total') else 0
                    except Exception as e:
                        print(f"[DEBUG] 获取 topic {tpid} 消息失败: {e}")
                        pass

                topic_link = None
                if tme_chat_id:
                    topic_link = f"https://t.me/c/{tme_chat_id}/{tpid}"
                    print(f"[DEBUG] 生成 topic_link: {topic_link}")

                topics.append({
                    'topic_id': tpid,
                    'topic_link': topic_link,
                    'message_count': count,
                })

    if not topics:
        print(f"[DEBUG] 没有找到任何 topics")

    print(f"[DEBUG] 返回 topics: {topics}")
    return topics


async def get_group_structure_info(client, chat):
    """
    重新设计的结构获取：
    - 先判断 group 类型 (Channel, Chat 等)
    - 根据类型获取相应分类信息 (topics, folders 等)
    - 生成可直接点开的 t.me/c 链接
    - 附加类别统计、文件夹结构
    """
    print(f"[DEBUG] 开始获取 {chat} 的结构信息")
    try:
        entity = await client.get_entity(chat)
        print(f"[DEBUG] 获取到 entity: {type(entity).__name__}")
        structure_info = {
            'chat_id': getattr(entity, 'id', None),
            'chat_title': getattr(entity, 'title', None),
            'chat_type': type(entity).__name__,
            'is_channel': isinstance(entity, Channel),
            'is_forum': getattr(entity, 'forum', False),
            'has_restricted_content': getattr(entity, 'has_restricted_content', False),
            'has_family': getattr(entity, 'has_geo', False),  # 只是继续记录，不做话题判定
            'has_topics': False,
            'topics': [],
            'topic_count': 0,
            'content_categories': {},
            'folder_groups': [],
            'raw_entity': {},  # 方便 Debug
        }

        # 记录 entity 的重要字段，方便调试版本差异
        try:
            structure_info['raw_entity'] = {k: getattr(entity, k, None) for k in ['id', 'title', 'username', 'broadcast', 'megagroup', 'has_geo', 'has_forum', 'is_forum', 'has_restricted_content']}
            print(f"[DEBUG] raw_entity: {structure_info['raw_entity']}")
        except Exception:
            structure_info['raw_entity'] = {}

        # 根据类型获取分类信息
        if isinstance(entity, Channel):
            print(f"[DEBUG] 是 Channel 类型，开始获取 topics 和 folders")
            # 对于频道，检查 topics 和 folders
            topics = await get_channel_topics(client, chat)
            print(f"[DEBUG] 获取到 topics: {len(topics) if topics else 0}")
            if topics:
                structure_info['has_topics'] = True
                structure_info['topic_count'] = len(topics)
                structure_info['topics'] = topics
            # 频道文件夹分组（如果客户端支持）
            structure_info['folder_groups'] = await get_channel_folders(client) or []
            print(f"[DEBUG] 获取到 folder_groups: {len(structure_info['folder_groups'])}")
        else:
            print(f"[DEBUG] 非 Channel 类型，跳过 topics 获取")
            # 对于其他类型（如 Chat），可能没有 topics，但可以检查其他分类
            structure_info['has_topics'] = False
            structure_info['topics'] = []
            structure_info['topic_count'] = 0
            # 可以添加其他分类逻辑，如消息类型等

        # 内容类型统计（适用于所有类型）
        print(f"[DEBUG] 开始获取内容分类")
        structure_info['content_categories'] = await analyze_message_categories(client, chat) or {}
        print(f"[DEBUG] 内容分类: {structure_info['content_categories']}")

        print(f"[DEBUG] 结构信息获取完成")
        return structure_info

    except Exception as e:
        print(f"[ERROR] get_group_structure_info 失败: {e}")
        return {
            'error': str(e),
            'chat': str(chat),
        }

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
        
        # 生成新文件名
        if msg_text:
            msg_text_safe = safe_name(msg_text[:100])
            fname = safe_name(f"{msg_text_safe}-{orig_fname}")
        else:
            fname = old_fname
        
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

async def get_all_messages(client, chat, filters, thread_id=None):
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
                    reverse=False,
                    reply_to=thread_id
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

        msg_text_safe = safe_name(msg_text[:100])
        new_fname = safe_name(f"{msg_text_safe}-{orig_fname}")
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

        # 获取 group 详细信息和分类情况
        print(f"\n=== 获取 {gid} 的详细信息 ===")
        structure_info = await get_group_structure_info(client, chat)
        print(f"Group 详细信息: {json.dumps(structure_info, ensure_ascii=False, indent=2)}")

        folder = os.path.join(BASE_DIR, safe_name(chat.title or str(chat.id)))
        os.makedirs(folder, exist_ok=True)
        logger = build_logger(folder)

        # 如果有topics，遍历每个topic进行下载
        if structure_info.get('has_topics') and structure_info.get('topics'):
            for topic in structure_info['topics']:
                topic_id = topic['topic_id']
                topic_title = topic['topic_title']
                print(f"\n=== 处理 Topic: {topic_title} (ID: {topic_id}) ===")
                
                topic_folder = os.path.join(folder, safe_name(topic_title))
                os.makedirs(topic_folder, exist_ok=True)
                topic_logger = build_logger(topic_folder)

                # 获取该topic的消息
                topic_logger.info(f"=== 开始获取 Topic {topic_title} 的消息 ===")
                all_messages = await get_all_messages(
                    client,
                    chat,
                    (InputMessagesFilterDocument, InputMessagesFilterVideo,
                     InputMessagesFilterMusic, InputMessagesFilterVoice),
                    thread_id=topic_id
                )
                topic_logger.info(f"获取到 {len(all_messages)} 条消息")

                if not all_messages:
                    topic_logger.warning(f"Topic {topic_title} 未获取到任何消息")
                    continue

                # 先重命名已存在的旧文件
                topic_logger.info("=== 开始重命名已下载文件 ===")
                await rename_existing_files_fast(all_messages, topic_folder, topic_logger, registered)

                # 再下载新文件
                topic_logger.info("=== 开始下载新文件 ===")
                msgs = []
                for msg in all_messages:
                    msg_key = (gid, topic_id, msg.id)
                    if msg_key not in seen_ids:
                        msgs.append(msg)
                        seen_ids.add(msg_key)

                if msgs:
                    await asyncio.gather(*[download(sema, m, topic_folder, topic_logger, registered) for m in msgs])
                else:
                    topic_logger.info("无新文件需要下载")
                
                topic_logger.info("=== Topic 完成 ===")
        else:
            # 如果没有topics，按原逻辑处理整个频道
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