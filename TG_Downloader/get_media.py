import os
import json
import asyncio
import logging
import re
from telethon.tl.types import (
    InputMessagesFilterDocument,
    InputMessagesFilterVideo,
    InputMessagesFilterMusic,
    InputMessagesFilterVoice,
    Channel
)
from telegram_client import create_telegram_client, get_entity_info, get_channel_topics
from config import GROUPS, BASE_DIR, MAX_MSG_PER_TYPE, REGISTER_FILE
from pathlib import Path

# 导入新的日志管理模块
from telegram_logger import get_main_logger
from down_media import download_and_register

# 获取主日志记录器
main_logger = get_main_logger()

async def get_messages_with_retry(client, chat, filter_type, reply_to=None, offset_id=0):
    """
    带重试机制的消息获取函数
    
    Args:
        client (TelegramClient): Telegram 客户端实例
        chat: 群组/频道实体
        filter_type: 消息过滤器类型
        reply_to: 回复消息ID（用于话题）
        offset_id: 偏移ID
    
    Returns:
        list: 消息列表
    """
    all_messages = []
    while True:
        try:
            messages = await client.get_messages(
                chat, 
                limit=MAX_MSG_PER_TYPE,
                offset_id=offset_id,
                filter=filter_type,
                reverse=False,
                reply_to=reply_to
            )
            if not messages:
                break
            
            all_messages.extend(messages)
            
            if len(messages) < MAX_MSG_PER_TYPE:
                break
            
            offset_id = messages[-1].id
        except Exception as e:
            main_logger.error(f"获取消息失败: {e}")
            # 添加重试机制
            await asyncio.sleep(1)
            continue
    
    return all_messages

async def get_media_info_from_chat(client, chat, folder, reply_to=None, group_name=None, topic_name=None):
    """
    从群组或话题中获取媒体文件信息并下载
    
    Args:
        client (TelegramClient): Telegram 客户端实例
        chat: 群组/频道实体
        folder (str): 存储文件夹路径
        reply_to: 回复消息ID（用于话题），None表示获取整个群组的消息
        group_name: 群组名称
        topic_name: 话题名称
    """
    if reply_to is None:
        main_logger.info(f"=== 开始获取 {chat.title or str(chat.id)} 的媒体信息 ===")
    else:
        main_logger.info(f"=== 开始获取 Topic 的媒体信息 ===")
    
    # 获取所有消息（仅一次）
    filters = (
        InputMessagesFilterDocument,
        InputMessagesFilterVideo,
        InputMessagesFilterMusic,
        InputMessagesFilterVoice
    )
    
    # 使用生成器方式处理消息，避免一次性加载所有消息到内存
    total_messages = 0
    media_stats = {
        'total': 0,
        'videos': 0,
        'documents': 0,
        'audio': 0,
        'voice': 0,
        'files': []
    }
    
    # 用于去重的集合
    processed_message_ids = set()
    
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
                    reply_to=reply_to
                )
                if not messages:
                    break
                
                # 逐个处理消息，避免内存溢出
                for msg in messages:
                    # 跳过已处理的消息（去重）
                    if msg.id in processed_message_ids:
                        continue
                    
                    processed_message_ids.add(msg.id)
                    
                    if not msg.file:
                        continue
                    
                    total_messages += 1
                    
                    # 处理文件名：Telethon 对部分文件类型（如视频）可能不返回 name
                    raw_name = getattr(msg.file, 'name', None)
                    if not raw_name:
                        ext = msg.file.ext or ''
                        raw_name = f"media_{msg.id}{ext}"
                    
                    # 获取消息文本内容并清理非法文件名字符
                    msg_text = getattr(msg, 'message', '') or ''
                    if msg_text:
                        # 移除文件名非法字符，限制长度
                        clean_text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', msg_text.strip())
                        clean_text = clean_text[:50]  # 限制文本长度防止文件名过长
                        # 插入文本内容到扩展名之前
                        name_part, ext_part = os.path.splitext(raw_name)
                        raw_name = f"{name_part}_{clean_text}{ext_part}"
                    
                    file_info = {
                        'id': msg.id,
                        'file_name': raw_name,
                        'mime_type': msg.file.mime_type,
                        'size': msg.file.size,
                        'date': msg.date.isoformat() if hasattr(msg, 'date') and msg.date else None
                    }
                    
                    # 统计文件类型
                    mime_type = msg.file.mime_type or ''
                    if 'video' in mime_type:
                        media_stats['videos'] += 1
                    elif 'document' in mime_type:
                        media_stats['documents'] += 1
                    elif 'audio' in mime_type:
                        media_stats['audio'] += 1
                    elif 'voice' in mime_type:
                        media_stats['voice'] += 1
                        
                    media_stats['files'].append(file_info)
                    
                    # 下载文件
                    await download_and_register(client, msg, folder, raw_name, group_name, topic_name)
                
                if len(messages) < MAX_MSG_PER_TYPE:
                    break
                
                offset_id = messages[-1].id
            except Exception as e:
                main_logger.error(f"获取消息失败: {e}")
                # 添加重试机制
                await asyncio.sleep(1)
                continue
    
    media_stats['total'] = total_messages
    main_logger.info(f"获取到 {total_messages} 条媒体消息")
    
    main_logger.info(f"媒体统计信息:")
    main_logger.info(f"  总计: {media_stats['total']}")
    main_logger.info(f"  视频: {media_stats['videos']}")
    main_logger.info(f"  文档: {media_stats['documents']}")
    main_logger.info(f"  音频: {media_stats['audio']}")
    main_logger.info(f"  语音: {media_stats['voice']}")
    
    # 保存统计信息到文件
    stats_file = os.path.join(folder, 'media_stats.json')
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(media_stats, f, ensure_ascii=False, indent=2)
        main_logger.info(f"统计信息已保存到: {stats_file}")
    except Exception as e:
        main_logger.error(f"保存统计信息失败: {e}")
        raise
    
    return media_stats

async def get_all_media_info():
    """
    获取所有群组和话题的媒体信息
    
    Returns:
        dict: 所有媒体信息的汇总
    """
    main_logger.info("=== 开始获取所有群组和话题的媒体信息 ===")
    
    # 创建客户端
    client = None
    try:
        client = await create_telegram_client()
        
        # 存储所有媒体信息
        all_media_info = {
            'groups': []
        }
        
        total_groups = len(GROUPS)
        processed_groups = 0
        
        for gid in GROUPS:
            processed_groups += 1
            try:
                chat = await get_entity_info(client, gid)
                if not chat:
                    processed_groups -= 1
                    continue
                    
                # 获取 group 详细信息和分类情况
                main_logger.info(f"[{processed_groups}/{total_groups}] 获取 {gid} 的详细信息")
                
                # 创建群组文件夹
                group_folder = os.path.join(BASE_DIR, chat.title or str(chat.id))
                os.makedirs(group_folder, exist_ok=True)
                
                # 检查是否有话题
                topics = await get_channel_topics(client, chat)
                main_logger.info(f"群组 {chat.title or str(chat.id)} 有 {len(topics)} 个话题")
                
                group_info = {
                    'group_id': gid,
                    'group_title': chat.title,
                    'has_topics': len(topics) > 0,
                    'topics': [],
                    'media_stats': {}
                }
                
                if topics:
                    total_topics = len(topics)
                    processed_topics = 0
                    # 遍历每个话题
                    for topic in topics:
                        processed_topics += 1
                        topic_id = topic['topic_id']
                        topic_title = topic['topic_title']
                        main_logger.info(f"  [{processed_groups}/{total_groups}] 群组 -> [{processed_topics}/{total_topics}] Topic: {topic_title} (ID: {topic_id})")
                        
                        topic_folder = os.path.join(group_folder, topic_title)
                        os.makedirs(topic_folder, exist_ok=True)
                        
                        # 获取话题媒体信息
                        topic_stats = await get_media_info_from_chat(
                            client, chat, topic_folder, reply_to=topic['topic_id'],
                            group_name=chat.title or str(chat.id), topic_name=topic_title
                        )
                        
                        topic_info = {
                            'topic_id': topic_id,
                            'topic_title': topic_title,
                            'media_stats': topic_stats
                        }
                        group_info['topics'].append(topic_info)
                        
                else:
                    # 如果没有话题，获取整个群组的媒体信息
                    main_logger.info(f"  [{processed_groups}/{total_groups}] 处理群组: {chat.title or str(chat.id)}")
                    group_stats = await get_media_info_from_chat(
                        client, chat, group_folder,
                        group_name=chat.title or str(chat.id), topic_name=None
                    )
                    group_info['media_stats'] = group_stats
                
                all_media_info['groups'].append(group_info)
                
            except Exception as e:
                main_logger.error(f"处理群组 {gid} 时出错: {e}")
                # 记录错误但继续处理其他群组
                continue
        
        # 保存完整信息到文件
        output_file = os.path.join(BASE_DIR, 'all_media_info.json')
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_media_info, f, ensure_ascii=False, indent=2)
            main_logger.info(f"=== 所有媒体信息已保存到: {output_file} ===")
        except Exception as e:
            main_logger.error(f"保存完整信息失败: {e}")
            raise
        
        return all_media_info
        
    except Exception as e:
        main_logger.error(f"获取媒体信息时发生严重错误: {e}")
        raise
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception as e:
                main_logger.error(f"断开客户端连接时出错: {e}")

async def main():
    """
    主函数 - 测试获取媒体信息功能
    """
    main_logger.info("媒体信息获取测试启动")
    print("媒体信息获取测试启动")
    print("=" * 50)
    
    try:
        media_info = await get_all_media_info()
        main_logger.info("🎉 媒体信息获取完成！")
        print("\n🎉 媒体信息获取完成！")
        print(f"共处理 {len(media_info['groups'])} 个群组")
        return 0
    except Exception as e:
        main_logger.error(f"❌ 媒体信息获取失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(0)