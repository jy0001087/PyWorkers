import os
import subprocess
import shutil
import json
import logging
from tkinter import Tk, filedialog

# 配置日志
logging.basicConfig(
    filename='sync_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 视频后缀列表
VIDEO_EXTS = ['.mp4', '.mov', '.mkv', '.avi', '.flv']
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']


def is_hidden(filepath: str) -> bool:
    """判断文件是否为隐藏文件（以.开头）"""
    return os.path.basename(filepath).startswith('.')


def get_file_info_ffprobe(file_path: str) -> dict:
    """
    使用 ffprobe 获取视频信息
    返回: dict，包含编码格式、时长（秒）、大小（字节）
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)

        format_info = info.get('format', {})
        streams = info.get('streams', [])
        video_stream = next((s for s in streams if s.get('codec_type') == 'video'), {})

        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'codec': video_stream.get('codec_name', ''),
            'duration': float(format_info.get('duration', 0)),
            'size': int(format_info.get('size', 0))
        }

    except Exception as e:
        logging.error(f"ffprobe 解析失败: {file_path}, 错误: {e}")
        return None


def select_folder(prompt: str) -> str:
    """弹出文件夹选择对话框，返回选择路径"""
    root = Tk()
    root.withdraw()
    path = filedialog.askdirectory(title=prompt)
    return path


def scan_base_folder(base_path: str) -> dict:
    """
    遍历Base文件夹，记录视频/图片信息
    返回: dict {文件名: 视频信息或图片路径}
    """
    data = {}
    for root, _, files in os.walk(base_path):
        for f in files:
            if is_hidden(f):
                continue
            full_path = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()

            if ext in VIDEO_EXTS:
                info = get_file_info_ffprobe(full_path)
                if info:
                    data[f] = info
            elif ext in IMAGE_EXTS:
                data[f] = {
                    'path': full_path,
                    'name': f,
                    'type': 'image'
                }
    return data


def process_scale_folder(scale_path: str, base_data: dict, base_root: str):
    """
    遍历Scale文件夹，与Base中的记录比对并处理
    日志记录同步处理
    """
    total = sum(len(files) for _, _, files in os.walk(scale_path))
    count = 0

    for root, _, files in os.walk(scale_path):
        for f in files:
            if is_hidden(f):
                continue

            count += 1
            progress = f"「{count}/{total}」"
            scale_path_full = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()

            if f not in base_data:
                logging.info(f"{progress} 不存在于Base中，跳过：{scale_path_full}")
                continue

            base_info = base_data[f]

            # 处理图片
            if ext in IMAGE_EXTS and base_info.get('type') == 'image':
                if os.path.getsize(scale_path_full) == os.path.getsize(base_info['path']):
                    os.remove(scale_path_full)
                    logging.info(f"{progress} 删除重复图片：{scale_path_full}")
                else:
                    logging.info(f"{progress} 图片不一致，跳过：{scale_path_full}")
                continue

            # 处理视频
            if ext in VIDEO_EXTS and 'duration' in base_info:
                scale_info = get_file_info_ffprobe(scale_path_full)
                if not scale_info:
                    continue

                # 完全一致
                if (scale_info['size'] == base_info['size'] and
                    abs(scale_info['duration'] - base_info['duration']) < 1 and
                    scale_info['codec'] == base_info['codec']):
                    os.remove(scale_path_full)
                    logging.info(f"{progress} 删除完全一致视频：{scale_path_full}")
                    continue

                # 替换条件满足
                if (scale_info['size'] >= base_info['size'] and
                    scale_info['codec'] in ['h264', 'hevc'] and
                    scale_info['duration'] >= base_info['duration']):
                    shutil.copy2(scale_path_full, base_info['path'])
                    logging.info(f"{progress} 替换Base文件：{base_info['path']} ← {scale_path_full}")
                    continue

                # 更小则删除
                if scale_info['size'] < base_info['size']:
                    os.remove(scale_path_full)
                    logging.info(f"{progress} 删除体积更小文件：{scale_path_full}")
                    continue

                logging.info(f"{progress} 未匹配替换条件，跳过：{scale_path_full}")

def remove_empty_dirs(root_dir: str):
    """
    删除指定目录下的所有空文件夹
    入参:
        root_dir: 要清理的根目录路径
    返回: None
    """
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # 跳过隐藏文件夹
        if is_hidden(os.path.basename(dirpath)):
            continue
        if not dirnames and not filenames:
            try:
                os.rmdir(dirpath)
                logging.info(f"删除空文件夹：{dirpath}")
            except Exception as e:
                logging.warning(f"无法删除空文件夹：{dirpath}，原因：{e}")

def main():
    """主函数：执行整个流程"""
    base_dir = select_folder("选择基准文件夹")
    if not base_dir:
        print("未选择基准文件夹")
        return

    scale_dir = select_folder("选择被筛选目标")
    if not scale_dir:
        print("未选择筛选文件夹")
        return

    logging.info(f"基准文件夹：{base_dir}")
    logging.info(f"筛选文件夹：{scale_dir}")

    print("扫描Base文件夹...")
    base_data = scan_base_folder(base_dir)
    print("扫描完毕，开始处理Scale文件夹...")
    process_scale_folder(scale_dir, base_data, base_dir)
    remove_empty_dirs(scale_dir)
    print("处理完成，日志已保存至 sync_log.txt")


if __name__ == "__main__":
    main()
