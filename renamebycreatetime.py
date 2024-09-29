import os
import time

def rename_amr_files(directory):
    file_list = [f for f in os.listdir(directory) if f.endswith('.amr')]
    file_list.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)))

    for i, file_name in enumerate(file_list, 10001):
        new_file_name = f"{i}.amr"
        os.rename(os.path.join(directory, file_name), os.path.join(directory, new_file_name))

directory = "D:\\MyFiles\\文档\\PersonalSync\\健康档案\\酷-肉丸\\amr"
rename_amr_files(directory)