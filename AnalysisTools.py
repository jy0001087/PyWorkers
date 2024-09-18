import pandas as pd
import tkinter as tk
from tkinter import simpledialog

def get_change_description(change_value):
    """
    根据日均变动值获取对应的描述
    """
    if change_value < 0:
        return "较年初下降"
    elif change_value > 0:
        return "较年初新增"
    else:
        return "较年初无变化"

def print_industry_stats(selected_data, value):
    """
    打印一级行业的统计信息
    """
    # 将日均和日均变动数据保留两位小数
    selected_data.loc[:, '日均_current'] = selected_data['日均_current'].round(2)
    selected_data.loc[:, '日均变动'] = selected_data['日均变动'].round(2)

    total_daily = selected_data['日均_current'].sum()
    total_change = selected_data['日均变动'].sum()

    sorted_data = selected_data.sort_values(by='日均变动')
    top_5 = sorted_data.head(5)
    bottom_5 = sorted_data.tail(5).iloc[::-1]

    change_description = get_change_description(total_change)  # 获取总变动的描述
    print(f" 全行{value}行业的当前日均总计为: {total_daily}亿元，{change_description}")
    print("日均下降前5名分别为：")
    for index, row in top_5.iterrows():
        change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
        if change_description_row!= "较年初无变化":
            print(f"{row['分行']}，{row['客户名称']}，{change_description_row}{row['日均变动']}亿元")
        else :
            print(f"{row['分行']}，{row['客户名称']}，{change_description_row}")
    print("日均提升前5名分别为：")
    for index, row in bottom_5.iterrows():
        change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
        if change_description_row!= "较年初无变化":
            print(f"{row['分行']}，{row['客户名称']}，{change_description_row}{row['日均变动']}亿元")
        else :
            print(f"{row['分行']}，{row['客户名称']}，{change_description_row}")

def print_branch_stats(selected_data, value):
    """
    打印分行的统计信息
    """
    selected_data = selected_data.groupby('一级行业').agg({'日均_current': 'sum', '日均变动': 'sum'}).sort_values(by='日均_current', ascending=False)
    # 将日均和日均变动数据保留两位小数
    selected_data.loc[:, '日均_current'] = selected_data['日均_current'].round(2)
    selected_data.loc[:, '日均变动'] = selected_data['日均变动'].round(2)

    total_branchdaily = selected_data['日均_current'].sum()
    total_branchDailyChange = selected_data['日均变动'].sum()

    change_description = get_change_description(total_branchDailyChange)  # 获取分行总变动的描述
    print(f"输入的分行 '{value}' 的统计结果：")
    print(f"{value}当前机构客户存款为{total_branchdaily}亿元，{change_description}:{total_branchDailyChange}亿元")
    for index, row in selected_data.iterrows():
        change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
        if change_description_row!= "较年初无变化":
            print(f"{index}行业，日均存款：{row['日均_current']}亿元，{change_description_row}: {row['日均变动']}亿元")
        else :
            print(f"{index}行业，日均存款：{row['日均_current']}亿元，{change_description_row}")

def calculate_sum_by_industry(excel_path):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    choice = simpledialog.askstring("输入", "请选择输入类型（行业/分行）：")
    value = simpledialog.askstring("输入", "请输入具体的值：")

    df = pd.read_excel(excel_path, sheet_name='日均计算结果')
    if choice == '行业':
        selected_data = df[df['一级行业'] == value]
        print_industry_stats(selected_data, value)
    elif choice == '分行':
        selected_data = df[df['分行'] == value]
        print_branch_stats(selected_data, value)
    else:
        print("无效的输入类型")

excel_path = 'D:\\MyFiles\\文档\兴业材料\\总行\\经营数据\\2024\\0831.xlsx'
if __name__ == "__main__":
    calculate_sum_by_industry(excel_path)