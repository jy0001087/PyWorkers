import pandas as pd

def calculate_daily_change(current_path, base_path):
    # 读取 excel1 的数据
    df1 = pd.read_excel(current_path, sheet_name='2-总行级明细')
    # 读取 excel2 的数据
    df2 = pd.read_excel(base_path, sheet_name='2312')

    # 提取共同的列用于匹配和计算
    common_columns = ['核心客户号','客户名称','分行','一级行业']
    selected_columns = common_columns + ['日均']

    # 仅保留共同列和日均存款列的数据
    df1_selected = df1[selected_columns]
    df2_selected = df2[selected_columns]

    # 合并两个 DataFrame 基于共同的列
    merged_df = pd.merge(df1_selected, df2_selected, on=common_columns, suffixes=('_current', '_base'))

    # 计算日均变动
    merged_df['日均变动'] = merged_df['日均_current'] - merged_df['日均_base']

    # 将计算结果写回到 excel1
    with pd.ExcelWriter(current_path, engine='openpyxl', mode='a') as writer:
        merged_df.to_excel(writer, sheet_name='日均计算结果', index=False)

current_path = 'D:\\MyFiles\\文档\\兴业材料\\总行\\经营数据\\2024\\0831.xlsx'
base_path = 'D:\\MyFiles\\文档\\兴业材料\\总行\\经营数据\\2024\\23总结.xlsx'
calculate_daily_change(current_path, base_path)