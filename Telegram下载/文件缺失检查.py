import os
import tkinter as tk
from tkinter import filedialog
import logging
from collections import defaultdict

def choose_directory(prompt):
    """弹出窗口选择文件夹"""
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title=prompt)

def get_all_filenames(directory):
    """递归获取目录下所有文件的文件名（不含路径）"""
    filenames = set()
    for dirpath, _, files in os.walk(directory):
        for file in files:
            filenames.add(file)
    return filenames

def get_file_counts_by_dir(base_dir):
    """
    统计 base_dir 下每个子目录中的文件数量
    返回：dict{相对路径: 文件数}
    """
    count_by_dir = defaultdict(int)
    total_files = 0
    for dirpath, _, files in os.walk(base_dir):
        rel_path = os.path.relpath(dirpath, base_dir)
        if rel_path == ".":
            rel_path = "(根目录)"
        count_by_dir[rel_path] += len(files)
        total_files += len(files)
    return count_by_dir, total_files

def log_dir_file_counts(label, count_dict, total, logger):
    logger.info(f"\n{label}（总计 {total} 个文件）:")
    for subdir in sorted(count_dict.keys()):
        logger.info(f"  {subdir}: {count_dict[subdir]} 个文件")

def main():
    # 1. 选择两个目录
    print("请选择包含需对比文件的【Download】文件夹：")
    folder_a = choose_directory("请选择Download文件夹")
    print("请选择包含备份文件的【Back】文件夹：")
    folder_b = choose_directory("请选择Back文件夹")

    if not folder_a or not folder_b:
        print("未选择有效的文件夹，程序退出。")
        return

    # 2. 获取B文件夹所有文件名（用于对比） + 统计信息
    b_filenames = get_all_filenames(folder_b)
    b_dir_counts, total_b_files = get_file_counts_by_dir(folder_b)

    # 3. 设置日志
    log_path = os.path.join(os.path.dirname(__file__), "deletion_log.txt")
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s - %(message)s")
    logger = logging.getLogger()

    # 4. 统计A文件夹，并删除多余文件
    deleted_count = 0
    a_dir_counts = defaultdict(int)
    total_a_files = 0

    for dirpath, _, files in os.walk(folder_a):
        rel_path = os.path.relpath(dirpath, folder_a)
        if rel_path == ".":
            rel_path = "(根目录)"
        for filename in files:
            total_a_files += 1
            a_dir_counts[rel_path] += 1
            file_path = os.path.join(dirpath, filename)
            if filename not in b_filenames:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    message = f"文件路径 {file_path} 的文件，在back中不存在，需重新下载。"
                    print(message)
                    logger.info(message)
                except Exception as e:
                    print(f"无法删除文件 {file_path}：{e}")

    # 5. 输出目录统计
    logger.info("\n统计信息：")
    log_dir_file_counts("A文件夹（Download）", a_dir_counts, total_a_files, logger)
    log_dir_file_counts("B文件夹（Back）", b_dir_counts, total_b_files, logger)

    # 6. 删除统计
    logger.info(f"\n总删除文件数：{deleted_count} 个\n")
    print(f"\n操作完成，总共删除 {deleted_count} 个文件。日志已保存至：{log_path}")

if __name__ == "__main__":
    main()
