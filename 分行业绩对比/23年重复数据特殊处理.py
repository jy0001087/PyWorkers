import pandas as pd
import tkinter as tk
from tkinter import filedialog

# 创建Tkinter根窗口并隐藏（我们只需要文件对话框功能）
root = tk.Tk()
root.withdraw()

# 弹出文件选择对话框，让用户选择Excel文件
file_path = filedialog.askopenfilename(
    title="选择Excel文件",
    filetypes=[("Excel文件", "*.xlsx *.xls")]
)

# 如果用户取消选择，退出程序
if not file_path:
    print("未选择文件，程序已退出。")
    exit()

# 读取Excel文件
try:
    df = pd.read_excel(file_path, sheet_name='重庆')
except Exception as e:
    print(f"读取Excel文件时出错: {e}")
    exit()

# 检查"核心客户号"列是否有重复值
if df['核心客户号'].duplicated().any():
    print("发现重复的'核心客户号'，开始汇总数据...")
    
    # 对"核心客户号"进行分组，并对"日均"、"余额"、"贷款"列求和
    grouped_df = df.groupby('核心客户号', as_index=False).agg({
        '日均': 'sum',
        '余额': 'sum',
        '贷款': 'sum'
    })
    
    # 对于其他列，取第一个值（假设其他列在重复行中是相同的）
    other_columns = [col for col in df.columns if col not in ['核心客户号', '日均', '余额', '贷款']]
    if other_columns:
        first_value_df = df.groupby('核心客户号').first().reset_index()[['核心客户号'] + other_columns]
        result_df = pd.merge(grouped_df, first_value_df, on='核心客户号')
    else:
        result_df = grouped_df
    
    # 弹出文件保存对话框，让用户选择保存位置
    output_file = filedialog.asksaveasfilename(
        title="保存汇总后的Excel文件",
        defaultextension=".xlsx",
        filetypes=[("Excel文件", "*.xlsx")]
    )
    
    if output_file:
        # 保存结果到新的Excel文件
        try:
            result_df.to_excel(output_file, index=False)
            print(f"处理完成，结果已保存到: {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
    else:
        print("未选择保存位置，程序已退出。")
else:
    print("'核心客户号'列没有重复值，无需汇总。")