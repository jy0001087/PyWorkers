import os
import shutil
import logging
from tkinter import Tk, filedialog

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def select_folder(title):
    """使用Windows资源管理器选择文件夹"""
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title=title)
    if not folder_path:
        logging.error("未选择文件夹，程序退出")
        exit()
    return folder_path

def process_folders(a_path, b_path):
    """处理两个文件夹中的文件"""
    # 获取A和B文件夹中的所有文件和文件夹
    a_files = {}
    for root, _, files in os.walk(a_path):
        relative_path = os.path.relpath(root, a_path)
        for file in files:
            file_path = os.path.join(root, file)
            a_files[os.path.join(relative_path, file)] = {
                'path': file_path,
                'size': os.path.getsize(file_path)
            }
    
    b_files = {}
    for root, _, files in os.walk(b_path):
        relative_path = os.path.relpath(root, b_path)
        for file in files:
            file_path = os.path.join(root, file)
            b_files[os.path.join(relative_path, file)] = {
                'path': file_path,
                'size': os.path.getsize(file_path)
            }
    
    # 遍历所有文件路径
    all_files = set(a_files.keys()).union(set(b_files.keys()))
    
    for file_path in all_files:
        a_file = a_files.get(file_path)
        b_file = b_files.get(file_path)
        
        # 情况1: download文件夹中存在，Back文件夹中不存在
        if a_file and not b_file:
            logging.info(f"处理: {file_path} (download存在，Back不存在)")
            
            a_file_path = a_file['path']
            a_file_size = a_file['size']
            
            if a_file_size != 0:
                # 创建Back文件夹中对应的路径
                b_target_dir = os.path.join(b_path, os.path.dirname(file_path))
                os.makedirs(b_target_dir, exist_ok=True)
                
                # 剪切文件到Back文件夹中
                b_target_path = os.path.join(b_path, file_path)
                shutil.move(a_file_path, b_target_path)
                logging.info(f"已将 {a_file_path} 剪切到 {b_target_path}")
                
                # 在download文件夹中创建大小为0的文件
                with open(a_file_path, 'w') as f:
                    pass
                logging.info(f"已在download文件夹中创建大小为0的文件: {a_file_path}")
            else:
                # 删除download文件夹中的大小为0的文件
                # os.remove(a_file_path)  20250721改为不删除，可能是删除的重复文件，计入日志
                # logging.info(f"已删除download文件夹中的大小为0的文件: {a_file_path}")
                logging.info(f"可能重复的文件: {a_file_path}")
            continue
            
        # 情况2: download文件夹中不存在，Back文件夹中存在
        elif not a_file and b_file:
            logging.info(f"处理: {file_path} (download不存在，Back存在)")
            
            a_target_dir = os.path.join(a_path, os.path.dirname(file_path))
            os.makedirs(a_target_dir, exist_ok=True)
            
            a_target_path = os.path.join(a_path, file_path)
            
            # 在download文件夹中创建大小为0的文件
            with open(a_target_path, 'w') as f:
                pass
            logging.info(f"已在download文件夹中创建大小为0的文件: {a_target_path}")
            continue
        
        # 情况3: 两个文件夹中都存在
        elif a_file and b_file:
            a_file_size = a_file['size']
            b_file_size = b_file['size']
            
            logging.info(f"处理: {file_path} (两个文件夹均存在)")
            
            if a_file_size == 0 and b_file_size != 0:
                logging.info(f"文件无需处理: {file_path}")
                continue
                
            elif a_file_size == 0 and b_file_size == 0:
                os.remove(a_file_path)
                os.remove(b_file_path)
                logging.info(f"已删除两个文件夹中的大小为0的文件: {file_path}")
                continue
                
            elif a_file_size != 0:
                # 创建Back文件夹中对应的路径
                b_target_dir = os.path.join(b_path, os.path.dirname(file_path))
                os.makedirs(b_target_dir, exist_ok=True)
                
                # 覆盖Back文件夹中的文件
                b_file_path = b_file['path']
                shutil.copy(a_file_path, b_file_path)
                logging.info(f"已将 {a_file_path} 覆盖到 {b_file_path}")
                
                # 删除download文件夹中的原始文件
                os.remove(a_file_path)
                logging.info(f"已删除download文件夹中的原始文件: {a_file_path}")
                
                # 在download文件夹中创建大小为0的文件
                with open(a_file_path, 'w') as f:
                    pass
                logging.info(f"已在download文件夹中创建大小为0的文件: {a_file_path}")
            continue
        
        # 其他情况
        else:
            logging.error(f"未处理: {file_path} (其他情况)")
            logging.error(f"当前download文件: {a_file}")
            logging.error(f"当前Back文件: {b_file}")
            logging.error("程序因遇到未定义情况而停止")
            exit()

def main():
    logging.info("开始选择文件夹...")
    a_folder = select_folder("选择download文件夹")
    b_folder = select_folder("选择Back文件夹")
    logging.info(f"已选择download文件夹: {a_folder}")
    logging.info(f"已选择Back文件夹: {b_folder}")
    
    logging.info("开始处理文件...")
    process_folders(a_folder, b_folder)
    logging.info("文件处理完成！")

if __name__ == "__main__":
    main()