import os
import json
import argparse
import hashlib
import mimetypes
from pathlib import Path
from collections import defaultdict
import subprocess

def get_file_hash(filepath, chunk_size=8192):
    """计算文件 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"[ERROR] 计算哈希失败 {filepath}: {e}")
        return None

def get_file_bitrate(filepath):
    """使用 ffprobe 获取音视频比特率"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=bit_rate',
             '-of', 'default=noprint_wrappers=1:nokey=1:noprint_names=1', filepath],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip():
            return int(result.stdout.strip())
    except Exception:
        pass
    return None

def get_file_info(filepath):
    """获取文件信息"""
    try:
        stat = os.stat(filepath)
        file_size = stat.st_size
        
        # 获取文件类型
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = 'unknown'
        
        # 获取文件扩展名
        _, ext = os.path.splitext(filepath)
        
        # 计算文件哈希（用于准确去重）
        file_hash = get_file_hash(filepath)
        
        # 获取比特率（仅限音视频文件）
        bitrate = None
        if mime_type and mime_type.startswith(('audio/', 'video/')):
            bitrate = get_file_bitrate(filepath)
        
        return {
            'filename': os.path.basename(filepath),
            'absolute_path': filepath,
            'file_size': file_size,
            'file_type': mime_type,
            'extension': ext,
            'file_hash': file_hash,
            'bitrate': bitrate
        }
    except Exception as e:
        print(f"[ERROR] 获取文件信息失败 {filepath}: {e}")
        return None

def scan_directory(target_dir):
    """递归扫描目录下的所有文件"""
    file_list = []
    total_files = 0
    
    print(f"[SCAN] 开始扫描目录: {target_dir}")
    
    for root, dirs, files in os.walk(target_dir):
        # 跳过隐藏文件夹和系统文件夹
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            if filename.startswith('.'):
                continue
            
            filepath = os.path.join(root, filename)
            total_files += 1
            
            # 显示进度
            if total_files % 100 == 0:
                print(f"[PROGRESS] 已扫描 {total_files} 个文件")
            
            file_info = get_file_info(filepath)
            if file_info:
                file_list.append(file_info)
    
    print(f"[DONE] 扫描完成，共 {len(file_list)} 个有效文件")
    return file_list

def find_duplicates(file_list):
    """查找重复文件"""
    # 按哈希值分组
    hash_groups = defaultdict(list)
    duplicates = {}
    
    print("[FIND] 开始查找重复文件...")
    
    for file_info in file_list:
        file_hash = file_info['file_hash']
        if file_hash:
            hash_groups[file_hash].append(file_info)
    
    # 提取重复文件
    for file_hash, files in hash_groups.items():
        if len(files) > 1:
            # 用第一个文件的文件名作为键
            key = f"{files[0]['filename']} (Hash: {file_hash[:8]})"
            
            duplicates[key] = {
                'duplicate_paths': [f['absolute_path'] for f in files],
                'file_characteristics': {
                    'filename': files[0]['filename'],
                    'file_size': files[0]['file_size'],
                    'file_type': files[0]['file_type'],
                    'extension': files[0]['extension'],
                    'file_hash': file_hash,
                    'bitrate': files[0]['bitrate'],
                    'count': len(files)
                }
            }
    
    print(f"[FOUND] 找到 {len(duplicates)} 组重复文件")
    return duplicates

def save_results(target_dir, duplicates):
    """保存结果到 JSON 文件"""
    output_path = os.path.join(target_dir, 'duplicateFile.json')
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(duplicates, f, indent=2, ensure_ascii=False)
        print(f"[SAVE] 结果已保存到: {output_path}")
        return output_path
    except Exception as e:
        print(f"[ERROR] 保存文件失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='查找重复文件')
    parser.add_argument('--target', required=True, help='目标根目录')
    args = parser.parse_args()
    
    target_dir = os.path.expanduser(args.target)
    
    # 验证目录存在
    if not os.path.isdir(target_dir):
        print(f"[ERROR] 目录不存在: {target_dir}")
        return
    
    # 扫描目录
    file_list = scan_directory(target_dir)
    
    if not file_list:
        print("[WARNING] 未找到任何文件")
        return
    
    # 查找重复文件
    duplicates = find_duplicates(file_list)
    
    # 保存结果
    if duplicates:
        save_results(target_dir, duplicates)
        print(f"\n[SUMMARY] 找到 {len(duplicates)} 组重复文件")
    else:
        print("[INFO] 未找到重复文件")

if __name__ == '__main__':
    main()