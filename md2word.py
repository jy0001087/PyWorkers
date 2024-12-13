import tkinter as tk
from tkinter import filedialog
import pypandoc
import os

def select_and_convert():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    markdown_file_path = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md")])

    if not markdown_file_path:
        print("未选择文件，程序退出")
        return

    base_path, file_name = os.path.split(markdown_file_path)
    file_name_without_ext, _ = os.path.splitext(file_name)
    word_file_path = os.path.join(base_path, file_name_without_ext + '.docx')

    output = pypandoc.convert_file(markdown_file_path, 'docx', outputfile=word_file_path)
    if output:
        print(f"转换成功，生成的 Word 文件: {word_file_path}")
    else:
        print("转换失败")

select_and_convert()