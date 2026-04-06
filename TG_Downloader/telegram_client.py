# Telegram下载/telegram_client.py
import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel
from telethon.tl.functions.channels import GetForumTopicsRequest
from config import API_ID, API_HASH, SESSION, USE_PROXY, PROXY

async def create_telegram_client():
    """
    创建并启动 Telegram 客户端连接
    
    Returns:
        TelegramClient: 已启动的客户端实例
    """
    print("[INFO] 正在创建 Telegram 客户端...")
    client = TelegramClient(SESSION, API_ID, API_HASH, proxy=PROXY if USE_PROXY else None)
    print("[INFO] 正在启动客户端...")
    await client.start()
    print("[INFO] 客户端启动成功")
    return client

async def get_entity_info(client, chat_id):
    """
    获取频道或群组的详细信息
    
    Args:
        client (TelegramClient): Telegram 客户端
        chat_id: 群组/频道 ID 或用户名
        
    Returns:
        Entity: 频道或群组实体信息
    """
    print(f"[INFO] 正在获取群组/频道信息: {chat_id}")
    try:
        entity = await client.get_entity(chat_id)
        print(f"[INFO] 成功获取群组/频道信息: {entity.title if hasattr(entity, 'title') else entity.id}")
        return entity
    except Exception as e:
        print(f"[ERROR] 无法访问 {chat_id}: {e}")
        return None

async def get_channel_topics(client, chat, sample_limit=200):
    """
    获取频道的论坛话题列表
    
    Args:
        client (TelegramClient): Telegram 客户端
        chat: 频道实体
        sample_limit (int): 采样消息数量
        
    Returns:
        list: 话题列表
    """
    from telethon.tl.types import Channel
    from telethon.tl.functions.channels import GetForumTopicsRequest
    
    print(f"[DEBUG] 开始获取 {chat} 的 topics")
    if not isinstance(chat, Channel):
        print(f"[DEBUG] 非 Channel 类型，跳过 topics 获取")
        return []

    # 检查是否是论坛频道
    is_forum = getattr(chat, 'forum', False)
    print(f"[DEBUG] is_forum: {is_forum}")

    topics = []

    if is_forum:
        print(f"[DEBUG] 是论坛频道，尝试获取论坛 topics 列表")
        try:
            # 使用 GetForumTopicsRequest 获取论坛 topics
            result = await client(GetForumTopicsRequest(
                channel=chat,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100  # 获取前100个topics
            ))
            forum_topics = result.topics
            print(f"[DEBUG] 获取到论坛 topics: {len(forum_topics) if forum_topics else 0}")
            if forum_topics:
                # 获取 t.me 链接 ID
                tme_chat_id = _tme_chat_id_from_entity(chat)
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

    print(f"[DEBUG] 返回 topics: {topics}")
    return topics

def _tme_chat_id_from_entity(entity):
    """
    频道链接在 t.me/c/ 下的 ID 计算：
    Telethon entity.id 可能是 -1003764726480
    t.me/c/: 3764726480 (去掉 -100 前缀)
    
    Args:
        entity: Telegram 实体
        
    Returns:
        str: t.me 链接格式的 ID
    """
    cid = getattr(entity, 'id', None)
    if cid is None:
        return None
    s = str(abs(int(cid)))
    if s.startswith('100'):
        # Telethon 超级群/频道 id 前缀 100
        return s[3:]
    return s

async def get_channel_folders(client):
    """
    获取用户的频道文件夹分类（Telegram Folders）
    
    Args:
        client (TelegramClient): Telegram 客户端
        
    Returns:
        list: 文件夹列表
    """
    print("[INFO] 正在获取频道文件夹分类...")
    try:
        from telethon.tl.functions.messages import GetDialogsRequest
        from telethon.tl.types import Folder
        
        # 获取所有对话文件夹
        folders = await client.get_folders() if hasattr(client, 'get_folders') else []
        
        print(f"[INFO] 获取到 {len(folders)} 个文件夹分类")
        return folders
    except Exception as e:
        print(f"[ERROR] 获取文件夹分类失败: {e}")
        return []

async def test_telegram_client():
    """
    测试 Telegram 客户端功能
    """
    print("=== 开始测试 Telegram 客户端 ===")
    
    try:
        # 创建客户端
        print("[TEST] 创建客户端")
        client = await create_telegram_client()
        
        # 测试获取用户信息
        print("[TEST] 获取用户信息")
        me = await client.get_me()
        print(f"[TEST] 用户信息: {me.first_name}")
        
        # 测试获取群组信息
        print("[TEST] 测试群组访问")
        from config import GROUPS
        test_groups = GROUPS[:2] if len(GROUPS) >= 2 else GROUPS  # 只测试前2个群组
        
        for gid in test_groups:
            print(f"[TEST] 测试群组: {gid}")
            entity = await get_entity_info(client, gid)
            if entity:
                print(f"[TEST] 成功获取群组信息: {entity.title}")
                print(f"[TEST] 群组类型: {type(entity).__name__}")
                
                # 测试获取话题
                topics = await get_channel_topics(client, entity)
                print(f"[TEST] 获取到 {len(topics)} 个话题")
                
                # 显示话题信息
                for topic in topics[:2]:  # 只显示前2个话题
                    print(f"[TEST] 话题: {topic.get('topic_title', '无标题')} (ID: {topic.get('topic_id')})")
            else:
                print(f"[TEST] 无法访问群组: {gid}")
        
        print("[TEST] 测试完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await client.disconnect()
            print("[INFO] 客户端连接已关闭")
        except:
            pass

async def main():
    """
    主测试函数
    """
    print("Telegram 客户端测试启动")
    print("=" * 50)
    
    success = await test_telegram_client()
    
    if success:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n❌ 测试失败！")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
