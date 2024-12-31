
import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image

def select_folder():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory()
    return folder_path

def compress_images(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(('.jpg', '.jpeg', '.png')):  # 只处理常见的图片格式
                try:
                    image = Image.open(file_path)
                    new_image = image.resize((int(image.width * 0.8), int(image.height * 0.8)))  # 压缩为原尺寸的 80%
                    new_file_path = os.path.join(root, 'resize_' + file)
                    new_image.save(new_file_path)
                except Exception as e:
                    print(f"处理 {file_path} 时出错: {e}")

folder_path = select_folder()
compress_images(folder_path)