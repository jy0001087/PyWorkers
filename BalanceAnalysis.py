import pandas as pd

def calculate_daily_change(excel1_path, excel2_path):
    # 读取 excel1 的数据
    df1 = pd.read_excel(excel1_path, sheet_name='sheet1')
    # 读取 excel2 的数据
    df2 = pd.read_excel(excel2_path, sheet_name='sheet1')

    # 提取共同的列用于匹配和计算
    common_columns = ['核心客户号', '帐号编码']
    selected_columns = common_columns + ['日均存款']

    # 仅保留共同列和日均存款列的数据
    df1_selected = df1[selected_columns]
    df2_selected = df2[selected_columns]

    # 合并两个 DataFrame 基于共同的列
    merged_df = pd.merge(df1_selected, df2_selected, on=common_columns, suffixes=('_excel1', '_excel2'))

    # 计算日均变动
    merged_df['日均变动'] = merged_df['日均存款_excel1'] - merged_df['日均存款_excel2']

    # 将计算结果写回到 excel1
    with pd.ExcelWriter(excel1_path, engine='openpyxl', mode='a') as writer:
        merged_df.to_excel(writer, sheet_name='sheet1', index=False)

excel1_path = 'excel1.xlsx'
excel2_path = 'excel2.xlsx'
calculate_daily_change(excel1_path, excel2_path)