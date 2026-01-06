import pandas as pd
import os

def split_excel_by_first_column(file_path):
    # 1. 加载 Excel 文件中的所有 Sheet
    # sheet_name=None 会返回一个字典 {sheet名: DataFrame数据}
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    
    # 获取原文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # 2. 遍历每一个 Sheet
    for sheet_name, df in all_sheets.items():
        if df.empty:
            continue
            
        # 获取第一列的列名
        first_col_name = df.columns[0]
        
        # 3. 按照第一列的值进行分组
        grouped = df.groupby(first_col_name)
        
        for group_value, group_df in grouped:
            # 移除非法文件名字符（如 / \ : 等）
            safe_value = str(group_value).replace("/", "_").replace("\\", "_")
            
            # 4. 构造新文件名：原文件名-汇总名称.xlsx
            new_file_name = f"{base_name}-{safe_value}.xlsx"
            
            # 保存为新的 Excel 文件
            group_df.to_excel(new_file_name, index=False)
            print(f"已生成文件: {new_file_name}")

# 使用示例
file_to_process = "/Users/rfs/Downloads/datou/34-03.xlsx" # 替换为你的文件名
split_excel_by_first_column(file_to_process)