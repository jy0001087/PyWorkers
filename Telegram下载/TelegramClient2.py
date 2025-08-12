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
BASE_DIR = os.path.expanduser('/Volumes/壶中境/TGDown')
REGISTER_FILE = os.path.expanduser('/Users/rfs/Documents/CodingWorkSpace/PyWorkers/Telegram下载/output/file_register.json')
GROUPS = [
    'ezl80231s', #EZL群
    -1001981879084, #Rush无脑控吸资源群
    #'weiniduba1', #为你独霸-weiniduba1
    -1002221790497, #粗口控r资源
    -1001662972970, #搜同小说避难所
    -1002471335106, #彪哥FakeM的音频
    -1001971709345, #彪哥FakeM的狗窝
    -1002246826599, #无脑傻逼贡狗母蛆
    'kinkyboi8686', #ChasteBoy
    'Feiyangs_zoo', #Feiyangs_zoo
    -1002284333043, #直男崇拜
    -1001400414058, #CHASTITY
    -1002274802303, #发泄粗狗
    -1002411845483, #控r视频
    -1002434627718, #彪哥资源备份群
    -1001752547937, #全国镣铐同好
    -1002478503978, #无脑傻逼
    -1001697384627, #重度SM囚禁
    -1001677932683 #早泄阳痿
]
USE_PROXY = True
PROXY = ('socks5', '127.0.0.1', 10800)
CONCURRENCY = 4
MAX_MSG_PER_TYPE = 200
# =====================================================

MIME_MAP = {
    'image/jpeg': '.jpg',
    'video/mp4': '.mp4',
    'audio/mpeg': '.mp3',
    'application/zip': '.zip',
}

def safe_name(name: str, max_bytes=200) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.replace(' ', '_'))
    b = name.encode('utf-8')
    if len(b) > max_bytes:
        name = b[:max_bytes].decode('utf-8', errors='ignore')
    return name or 'unnamed'

def load_register(path: str) -> set:
    try:
        with open(path) as f:
            return {e['filename'] for e in json.load(f) if e.get('type') == 'file'}
    except Exception:
        return set()

def build_logger(chat_dir: str):
    logger = logging.getLogger(chat_dir)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(chat_dir, 'log.log'),
        maxBytes=50*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

async def download(sema, msg, folder, logger, registered):
    async with sema:
        # 在访问 msg.file.name 之前，先检查 msg.file 是否为 None
        if not msg.file:
            logger.info(f"[SKIP] Message {msg.id} has no file.")
            return

        fname = safe_name(msg.file.name or f"{msg.id}{MIME_MAP.get(msg.file.mime_type, '')}")
        if fname in registered or os.path.exists(os.path.join(folder, fname)):
            logger.info(f"[SKIP] {fname}")
            return

        total_size = msg.file.size
        logger.info(f"[START] {fname} (Total size: {total_size / 1024 / 1024:.2f} MB)")
        
        async def progress_callback(current, total):
            progress = int(current * 100 / total)
            print(f"[PROGRESS] {fname}: {progress}% - {current / 1024 / 1024:.2f}/{total / 1024 / 1024:.2f} MB", end='\r')
            
        await msg.download_media(file=os.path.join(folder, fname), progress_callback=progress_callback)
        print() # 换行，以便下一个日志行不会覆盖进度条
        logger.info(f"[DONE] {fname}")

async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH, proxy=PROXY if USE_PROXY else None)
    await client.start()
    registered = load_register(REGISTER_FILE)
    sema = asyncio.Semaphore(CONCURRENCY)

    for gid in GROUPS:
        try:
            chat = await client.get_entity(gid)
        except Exception as e:
            print(f"[ERROR] 无法访问 {gid}: {e}")
            continue

        folder = os.path.join(BASE_DIR, safe_name(chat.title or str(chat.id)))
        os.makedirs(folder, exist_ok=True)
        logger = build_logger(folder)

        msgs = []
        for f in (InputMessagesFilterDocument, InputMessagesFilterVideo,
                  InputMessagesFilterMusic, InputMessagesFilterVoice):
            msgs += await client.get_messages(chat, limit=MAX_MSG_PER_TYPE, filter=f)

        await asyncio.gather(*[download(sema, m, folder, logger, registered) for m in msgs])
        logger.info("=== 完成 ===")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())