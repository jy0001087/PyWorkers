import os  # 导入操作系统相关的模块，用于文件和目录操作
import shutil  # 导入用于文件复制、移动等操作的模块
import tkinter as tk  # 导入 tkinter 库，并将其简称为 tk
from tkinter import filedialog  # 从 tkinter 中导入文件对话框相关的模块

def select_folders():  # 定义一个名为 select_folders 的函数
    root = tk.Tk()  # 创建一个 tkinter 的主窗口对象
    root.withdraw()  # 隐藏刚创建的主窗口
    folder_a = filedialog.askdirectory(title="选择文件夹 back")  # 弹出对话框让用户选择文件夹 A，并将选择的路径存储在 folder_a 变量中
    folder_b = filedialog.askdirectory(title="选择文件夹 源文件夹")  # 弹出对话框让用户选择文件夹 B，并将选择的路径存储在 folder_b 变量中
    return folder_a, folder_b  # 返回选择的文件夹 A 和 B 的路径

def find_relative_path(folder, filename):
    for root, dirs, files in os.walk(folder):
        if filename in files:
            return os.path.relpath(os.path.join(root, filename), folder)
    return None

def process_folders(folder_a, folder_b):  # 定义一个名为 process_folders 的函数，接收文件夹 A 和 B 的路径作为参数
    for root_a, dirs_a, files_a in os.walk(folder_a):  # 使用 os.walk 遍历文件夹 A 及其子目录
        for file_a in files_a:  # 遍历文件夹 A 中的每个文件
            relative_path_in_b=find_relative_path(folder_b,file_a)
            target_dir_in_a = os.path.join(folder_a, relative_path_in_b)  # 根据相对路径构建在文件夹 A 中的目标目录路径
            target_dir_in_a = target_dir_in_a.split("\\"+file_a)
            target_dir_in_a = target_dir_in_a[0]
            if not os.path.exists(target_dir_in_a):  # 如果目标目录不存在
                os.makedirs(target_dir_in_a)  # 创建目标目录
            file_path_a = os.path.join(root_a, file_a)
            shutil.move(file_path_a, target_dir_in_a)  # 将当前文件移动到目标目录

folder_a, folder_b = select_folders()  # 调用 select_folders 函数选择文件夹 A 和 B，并将返回的路径分别存储在 folder_a 和 folder_b 变量中
process_folders(folder_a, folder_b)  # 调用 process_folders 函数，对选择的文件夹 A 和 B 进行处理