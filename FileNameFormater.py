import os
import tkinter as tk
from tkinter import filedialog

def select_folder():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory()
    return folder_path

def remove_illegal_characters(folder_path):
    illegal_characters = r'\/:*?"<>|'
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            new_file = ''.join(c for c in file if c not in illegal_characters)
            old_path = os.path.join(root, file)
            new_path = os.path.join(root, new_file)
            if old_path!= new_path:
                os.rename(old_path, new_path)

folder_path = select_folder()
remove_illegal_characters(folder_path)