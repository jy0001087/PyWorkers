import os
import shutil
from tkinter import filedialog
from tkinter import Tk

def select_folder():
    """使用tkinter打开文件夹选择对话框"""
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title="请选择目标文件夹")
    root.destroy()
    return folder_path

def delete_empty_files_and_folders(folder_path):
    """递归删除大小为0的文件和空文件夹"""
    if not os.path.exists(folder_path):
        print("指定的文件夹不存在，请重新选择。")
        return

    # 遍历文件夹
    for root, dirs, files in os.walk(folder_path, topdown=False):
        # 删除大小为0的文件
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) == 0:
                os.remove(file_path)
                print(f"已删除大小为0的文件: {file_path}")

        # 删除空文件夹
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # 检查文件夹是否为空
                shutil.rmtree(dir_path)
                print(f"已删除空文件夹: {dir_path}")

if __name__ == "__main__":
    print("请选择一个目标文件夹：")
    folder_path = select_folder()
    if folder_path:
        print(f"已选择文件夹: {folder_path}")
        delete_empty_files_and_folders(folder_path)
        print("操作完成。")
    else:
        print("未选择任何文件夹，程序已退出。")