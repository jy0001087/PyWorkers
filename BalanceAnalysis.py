import pandas as pd
import openpyxl

def calculate_daily_change(current_path, base_path):
    # 读取 current_path 对应的工作簿
    workbook = openpyxl.load_workbook(current_path)
    if '日均计算结果' in workbook.sheetnames:
        workbook.remove(workbook['日均计算结果'])
        workbook.save(current_path)

    # 读取 excel1 的数据,筛选企金小口径为1的数据
    df1 = pd.read_excel(current_path, sheet_name='2-总行级明细')
    df1 = df1[df1['企金小口径'] == 1]
    # 读取 excel2 的数据
    df2 = pd.read_excel(base_path, sheet_name='2312')

    # 提取共同的列用于匹配和计算
    common_columns = ['核心客户号']
    selected_columns = common_columns + ['日均'] + ['余额']

    # 仅保留共同列和日均存款列的数据
    df1_selected = df1[selected_columns]
    df2_selected = df2[selected_columns]

    # 合并两个 DataFrame 基于共同的列
    merged_df = pd.merge(df1_selected, df2_selected, on=common_columns, suffixes=('_current', '_base'))

    # 计算日均变动
    merged_df['日均变动'] = merged_df['日均_current'] - merged_df['日均_base']
    merged_df['余额变动'] = merged_df['余额_current'] - merged_df['余额_base']

    #增加额外的列，都从df1获取最新当前信息
    extra_info = df1.set_index('核心客户号')[['分行', '一级行业', '客户名称']]
    merged_df = merged_df.join(extra_info, on='核心客户号')

    # 获取 current_path 中的核心客户号
    current_core_customer_ids = set(df1['核心客户号'])
    # 获取 base_path 中的核心客户号
    base_core_customer_ids = set(df2['核心客户号'])

    # 找出 df1 中不在合并结果的行，新增客户
    df1_only = df1[~df1['核心客户号'].isin(merged_df['核心客户号'])]
    df1_only = df1_only[selected_columns]
    df1_only = df1_only.join(df1.set_index('核心客户号')[['分行', '一级行业', '客户名称']], on='核心客户号')
    df1_only['日均_current'] = df1_only['核心客户号'].map(df1.set_index('核心客户号')['日均'])
    df1_only['日均_base'] = 0
    df1_only['余额_current'] = df1_only['核心客户号'].map(df1.set_index('核心客户号')['余额'])
    df1_only['余额_base'] = 0
    df1_only['日均变动'] = df1_only['日均_current'] - df1_only['日均_base']
    df1_only['余额变动'] = df1_only['余额_current'] - df1_only['余额_base']

    # 找出 df2 中不在合并结果中的行，销户客户
    df2_only = df2[~df2['核心客户号'].isin(merged_df['核心客户号'])]
    df2_only = df2_only[selected_columns]
    df2_only = df2_only.join(df2.set_index('核心客户号')[['分行', '一级行业', '客户名称']], on='核心客户号')
    df2_only['日均_current'] = 0
    df2_only['日均_base'] = df2_only['核心客户号'].map(df2.set_index('核心客户号')['日均'])
    df2_only['余额_current'] = 0
    df2_only['余额_base'] = df2_only['核心客户号'].map(df2.set_index('核心客户号')['余额'])
    df2_only['日均变动'] = df2_only['日均_current'] - df2_only['日均_base']
    df2_only['余额变动'] = df2_only['余额_current'] - df2_only['余额_base']
    # 将这些额外的行添加到合并结果中
    final_df = pd.concat([merged_df, df1_only, df2_only], ignore_index=True)


    # 标记客户存续状态
    final_df['客户存续状态'] = final_df['核心客户号'].apply(lambda x: '存续' if x in base_core_customer_ids and x in current_core_customer_ids
                                                             else ('销户' if x in base_core_customer_ids and x not in current_core_customer_ids
                                                                   else ('新增' if x not in base_core_customer_ids and x in current_core_customer_ids
                                                                          else None)))

    # 将计算结果写回到 excel1
    with pd.ExcelWriter(current_path, engine='openpyxl', mode='a') as writer:
        final_df.to_excel(writer, sheet_name='日均计算结果', index=False)

current_path = 'D:\\MyFiles\\文档\\兴业材料\\总行\\经营数据\\2024\\0831.xlsx'
base_path = 'D:\\MyFiles\\文档\\兴业材料\\总行\\经营数据\\2024\\23总结.xlsx'
calculate_daily_change(current_path, base_path)