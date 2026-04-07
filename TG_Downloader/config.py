import os
from pathlib import Path
from typing import List, Optional, Tuple, Any

# ============ 配置区域 ==========
# 1. Telegram API 认证信息
# 建议通过环境变量设置，避免代码中硬编码敏感信息
API_ID: int = 25270021
API_HASH: str = 'e27d91ad37959d54eb5c1d454d567afa'

# 会话文件名称
SESSION: str = 'session'

# 2. 网络代理配置
USE_PROXY: bool = True
# 代理格式：(type, ip, port, username, password)
# 注意：Telethon 期望的代理元组为 (type, ip, port, username, password, proxy_factory)
# 如果不需要密码，username 和 password 留空
PROXY: Optional[Tuple[str, str, int, str, str, None]] = ('socks5', '127.0.0.1', 10808, '', '')

# 3. 业务逻辑配置
# 并发下载数，建议根据服务器性能调整
CONCURRENCY: int = 4
# 单次获取消息数上限，避免 Telegram API 限制
MAX_MSG_PER_TYPE: int = 200

# 4. 文件路径配置
# 脚本根目录（相对于当前运行位置）
BASE_DIR: Path = Path('/Users/rfs/Documents/TGDownload')

# 注册表文件路径，用于记录已下载的文件名，防止重复下载
REGISTER_FILE: Path = Path('/Users/rfs/Documents/Syncthing-SyncFiles/风陵渡/非礼勿视/file_register.json')

# 5. 目标群组/频道列表
# 支持格式：整数 ID (如 -100xxx) 或 用户名/链接 (如 'username' 或 't.me/username')
GROUPS: List[Any] = [
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

# 6. 辅助函数

def get_proxy_config():
    """
    根据配置返回 Telethon 可用的代理对象
    返回：(proxy_tuple, use_proxy_bool) 或 None
    """
    if USE_PROXY and PROXY:
        # Telethon 期望的 proxy 格式是 tuple 或 ProxyType 对象
        return PROXY
    return None

# 7. 环境覆盖（可选）
# 如果你希望在本地运行时通过环境变量覆盖配置，可以在这里添加逻辑
# 例如：
# import os
# if os.getenv('TG_API_ID'):
#     API_ID = int(os.getenv('TG_API_ID'))
# if os.getenv('TG_API_HASH'):
#     API_HASH = os.getenv('TG_API_HASH')

# 8. MIME 类型映射（用于文件扩展名处理）
MIME_MAP = {
    'image/jpeg': '.jpg',
    'video/mp4': '.mp4',
    'audio/mpeg': '.mp3',
    'application/zip': '.zip',
}

# 9. 全局锁保护注册表写入（用于线程安全）
register_lock = None

# 打印配置信息（可选，用于调试）
print("[CONFIG] 加载配置文件...")
print(f"[CONFIG] API_ID: {API_ID}")
print(f"[CONFIG] SESSION: {SESSION}")
print(f"[CONFIG] USE_PROXY: {USE_PROXY}")
print(f"[CONFIG] CONCURRENCY: {CONCURRENCY}")
print(f"[CONFIG] BASE_DIR: {BASE_DIR}")
print(f"[CONFIG] REGISTER_FILE: {REGISTER_FILE}")
print(f"[CONFIG] GROUPS Count: {len(GROUPS)}")
print("[CONFIG] 配置加载完成。")
