from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument, InputMessagesFilterVideo, InputMessagesFilterMusic,InputMessagesFilterVoice
import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
import importlib.util
import subprocess

## 运行是环境检查函数
def check_package(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return False
    else:
        print(f"已提前安装{package_name}")
        return True

def install_package(package_name):
    try:
        subprocess.check_call(["pip", "install", package_name])
        print(f"成功安装 {package_name}。")
    except subprocess.CalledProcessError:
        print(f"安装 {package_name} 时出现错误。")

#需要隐士安装的模块，否则会报错无法连接代理
package_name = 'python-socks'
# 请在这里填写你的API ID和API Hash
api_id = '25270021'
api_hash = 'e27d91ad37959d54eb5c1d454d567afa'

# 你想要下载视频的Telegram群组或频道用户名
# 定义包含多个组的信息
groups_info = [
    ('ezl80231s', 'D:\\TelegramDownloads\\ELZ小叔群'),
    (-1001981879084, 'D:\\TelegramDownloads\\Rush无脑控吸资源群-1001981879084'),
    ('weiniduba1', 'D:\\TelegramDownloads\\为你独霸-weiniduba1'),
    (-1002221790497, 'D:\\TelegramDownloads\\粗口控r资源-2221790497'),
   # ('tuohuang1s', 'D:\\TelegramDownloads\\拓荒哥乐园-tuohuang1s'),
    (-1001662972970, 'D:\\TelegramDownloads\\搜同小说避难所-tuohuang1s'),
   # ('rushvideoshare', 'D:\\TelegramDownloads\\优质-控r视频分享群'),
   # (-1002379147214, 'D:\\TelegramDownloads\\控R资源分享群-1002379147214'),
    (-1002471335106, 'D:\\TelegramDownloads\\彪哥FakeM的音频-1002471335106'),
    (-1002246826599,'D:\\TelegramDownloads\\无脑傻逼贡狗母蛆-1002246826599'),
    ('kinkyboi8686','D:\\TelegramDownloads\\ChasteBoy-kinkyboi8686')
]


# 创建一个Telethon客户端
client = TelegramClient('session_name', api_id, api_hash,proxy=("socks5", '127.0.0.1', 10800))


async def download_file(semaphore,message, download_path, retry_count=300):
    """
    下载单个文件的函数
    """
    async with semaphore:
        try:
            if message.media:
                # 获取文件名，如果没有则使用消息ID
                file_name = message.file.name or f"{message.id}.mp4"
                save_path = os.path.join(download_path, file_name)
                if os.path.exists(save_path):
                    logging.info(f"文件已存在，跳过: {file_name}")
                    return

                # 获取文件大小并记录到日志
                file_size = message.file.size if message.file else 0
                if message.video:
                    file_size = message.video.size
                elif message.audio:
                    file_size = message.audio.size

                logging.info(f"++++++++正在下载文件: {file_name} 大小: {file_size / (1024 * 1024):.2f} MB")

                # 定义进度回调函数，带文件名区分
                def progress_callback(current, total):
                    percentage = (current * 100 / total) if total else 0
                    logging.info(f"文件 {file_name}:----大小：{file_size / (1024 * 1024):.2f} MB  下载进度 {percentage:.2f}%")

                await message.download_media(file=save_path,progress_callback=progress_callback)

                logging.info(f"--------下载完成: {file_name}")
        except Exception as e:
            # 记录异常信息
            logging.error(f"下载失败: {file_name}, 错误: {str(e)}")
            if retry_count > 0:
                logging.info(f"尝试重新下载: {file_name}")
                await asyncio.sleep(10)
                await download_file(semaphore, message, download_path, retry_count - 1)
            else:
                logging.error(f"重试次数用完，停止下载: {file_name}")

async def main():
    # 连接到Telegram服务器
    await client.start()

    # 遍历每个组进行下载
    for group_username, download_path in groups_info:
        # 确保保存目录存在
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        # 设置日志配置
        log_file_path = os.path.join(download_path, 'log.log')
        # 创建RotatingFileHandler，最大文件大小为50MB，最多备份3个
        handler = RotatingFileHandler(
            log_file_path, maxBytes=1*1024, backupCount=3
        )

        logging.basicConfig(
            filename=log_file_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # 获取群组或频道的实体
        group = await client.get_entity(group_username)
        print(f"{group_username} 开始下载。")
        # 获取所有文件、音频和视频消息
        messages_files = await client.get_messages(group, None, filter=InputMessagesFilterDocument)
        messages_videos = await client.get_messages(group, None, filter=InputMessagesFilterVideo)
        messages_audios = await client.get_messages(group, None, filter=InputMessagesFilterMusic)
        messages_audioMessage = await client.get_messages(group, None, filter=InputMessagesFilterVoice)

        # 将所有消息合并到一个列表中
        all_messages = messages_files + messages_videos + messages_audios + messages_audioMessage

        # 创建Semaphore，限制同时进行的任务数为2
        semaphore = asyncio.Semaphore(4)
        # 创建任务列表
        tasks = [download_file(semaphore, message, download_path,retry_count=300) for message in all_messages]

        # 并行执行所有下载任务
        await asyncio.gather(*tasks)

        logging.info(f"{group_username} 中所有文件下载完成。")

        print(f"{group_username} 中所有文件下载完成。")

# 启动事件循环并运行下载任务
if __name__ == "__main__":
    if not check_package(package_name):
        install_package(package_name)
    with client:
        client.loop.run_until_complete(main())