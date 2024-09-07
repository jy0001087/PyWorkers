import os
from PIL import Image

def resize_jpg_files(source_dir, output_dir, new_size=(2673,3840)):
    # 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历源目录下的所有文件
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            # 构造完整的文件路径
            file_path = os.path.join(source_dir, filename)
            # 打开图片
            with Image.open(file_path) as img:
                # 调整图片大小
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 构造输出文件的路径
                output_file_path = os.path.join(output_dir, filename)
                # 保存调整大小后的图片
                img_resized.save(output_file_path, 'JPEG')

                print(f"Resized and saved: {output_file_path}")

# 调用函数
source_directory = "F:\\Julius\\Documents"  # C盘根目录
output_directory = "F:\\Julius\\Documents\\ResizedImages"  # 输出目录
resize_jpg_files(source_directory, output_directory)