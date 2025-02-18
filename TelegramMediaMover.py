
##先运行这个脚本，把文件拷贝到badk目录
import os
import tkinter as tk
from tkinter import filedialog
import shutil

def select_folder():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title="选择已下载好文件所在的文件夹 不带back")
    return folder_path

def process_folder(folder_path):
    new_folder_path = folder_path + 'back'
    os.makedirs(new_folder_path, exist_ok=True)

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            # 记录文件名
            # 剪切文件到新文件夹
            shutil.move(file_path, os.path.join(new_folder_path, file))
            # 在原位置创建空文件
            open(os.path.join(root, file), 'w').close()

folder_path = select_folder()
process_folder(folder_path)