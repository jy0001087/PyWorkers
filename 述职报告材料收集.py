import os
import shutil
import datetime

source_path = r'D:\MyFiles\文档\兴业材料'
destination_path = r'D:\述职报告'

# 将日期字符串转换为日期对象
target_date = datetime.datetime.strptime('2024-01-01', '%Y-%m-%d')

# 检查目标路径是否存在，不存在则创建
if not os.path.exists(destination_path):
    os.makedirs(destination_path)

if not os.path.exists(source_path):
    raise ValueError(f"源路径 {source_path} 不存在")

for root, dirs, files in os.walk(source_path):
    for file in files:
        file_path = os.path.join(root, file)
        file_modify_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_modify_time > target_date:
            shutil.copy(file_path, destination_path)
