import pandas as pd
import tkinter as tk
from tkinter import simpledialog
import logging

# 配置日志
logging.basicConfig(filename='output.log', level=logging.INFO, format='%(message)s', filemode='w')

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

    #计算日均及余额
    total_daily = selected_data['日均_current'].sum()
    total_change = selected_data['日均变动'].sum()

    total_balance = selected_data['余额_current'].sum()
    total_banalce_change = selected_data['余额变动'].sum()

    sorted_data = selected_data.sort_values(by='日均变动')
    top_5 = sorted_data.head(5)
    bottom_5 = sorted_data.tail(5).iloc[::-1]

    # 按照客户存续状态统计不同状态的客户个数
    customer_status_counts = selected_data['客户存续状态'].value_counts()

    change_description_balance = get_change_description(total_banalce_change)
    change_description = get_change_description(total_change)  # 获取总变动的描述
    logging.info(f" 全行{value}行业的当前日均总计为: {total_daily:.2f}亿元，{change_description}{total_change:.2f}亿元;余额总计为：{total_balance:.2f}亿元，{change_description_balance}{total_banalce_change:.2f}亿元")
    logging.info(f"当前总客户数为：{customer_status_counts.get('存续', 0)+customer_status_counts.get('新增', 0)}，其中，存续客户为：{customer_status_counts.get('存续', 0)}，较年初销户：{customer_status_counts.get('销户', 0)}，较年初新增新增：{customer_status_counts.get('新增', 0)}户")

    logging.info("日均下降前5名分别为：")
    for index, row in top_5.iterrows():
        change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
        if change_description_row!= "较年初无变化":
            logging.info(f"{row['分行']}，{row['客户名称']}，{change_description_row}{row['日均变动']:.2f}亿元")
        else :
            logging.info(f"{row['分行']}，{row['客户名称']}，{change_description_row}")
    logging.info("日均提升前5名分别为：")
    for index, row in bottom_5.iterrows():
        change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
        if change_description_row!= "较年初无变化":
            logging.info(f"{row['分行']}，{row['客户名称']}，{change_description_row}{row['日均变动']:.2f}亿元")
        else :
            logging.info(f"{row['分行']}，{row['客户名称']}，{change_description_row}")

def print_branch_stats(selected_data, value):
    """
    打印分行的统计信息
    """
    # 将日均和日均变动数据保留两位小数
    selected_data.loc[:, '日均_current'] = selected_data['日均_current'].round(2)
    selected_data.loc[:, '日均变动'] = selected_data['日均变动'].round(2)
    selected_data_grouped = selected_data.groupby('一级行业').agg({'日均_current': 'sum', '日均变动': 'sum'}).sort_values(by='日均_current', ascending=False)

    total_branchdaily = selected_data_grouped['日均_current'].sum()
    total_branchDailyChange = selected_data_grouped['日均变动'].sum()

    change_description = get_change_description(total_branchDailyChange)  # 获取分行总变动的描述
    logging.info(f"输入的分行 '{value}' 的统计结果：")
    logging.info(f"{value}当前机构客户存款为{total_branchdaily:.2f}亿元，{change_description}:{total_branchDailyChange:.2f}亿元")
    for index, row in selected_data_grouped.iterrows():
        change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
        if change_description_row!= "较年初无变化":
            logging.info(f"{index}行业，日均存款：{row['日均_current']:.2f}亿元，{change_description_row}: {row['日均变动']:.2f}亿元")
        else :
            logging.info(f"{index}行业，日均存款：{row['日均_current']:.2f}亿元，{change_description_row}")

        sort_data = selected_data[selected_data['一级行业'] == index]
        sorted_data = sort_data.sort_values(by='日均_current', ascending=False)  # 按日均存款降序排序
        top_5 = sorted_data.head(5)  # 获取前 5 名

        logging.info(f"{index}行业，日均存款前 5 名分别为：")
        for _, row in top_5.iterrows():
            logging.info(f"^^^^^{row['客户名称']}，日均存款：{row['日均_current']:.2f}亿元")

        sort_data = selected_data[selected_data['一级行业'] == index]
        sorted_data = sort_data.sort_values(by='日均变动')
        top_5 = sorted_data.head(5)
        bottom_5 = sorted_data.tail(5).iloc[::-1]

        # 计算日均变动大于 0 的条数
        count_positive_change = sum(1 for _, row in top_5.iterrows() if row['日均变动'] < 0)
        if count_positive_change > 0:
            logging.info(f"日均下降前{count_positive_change}名分别为：")
            for index, row in top_5.iterrows():
                change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
                if change_description_row == "较年初下降":
                    logging.info(f"-----{row['客户名称']}，{change_description_row}{row['日均变动']:.2f}亿元")

        # 计算日均变动大于 0 的条数
        count_positive_change = sum(1 for _, row in bottom_5.iterrows() if row['日均变动'] > 0)
        if count_positive_change > 0:
            logging.info(f"日均提升前{count_positive_change}名分别为：")
            for index, row in bottom_5.iterrows():
                change_description_row = get_change_description(row['日均变动'])  # 获取每行变动的描述
                if change_description_row == "较年初新增":
                    logging.info(f"+++++{row['客户名称']}，{change_description_row}{row['日均变动']:.2f}亿元")

def calculate_sum_by_industry(excel_path):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    try:
        choice = simpledialog.askstring("输入", "请选择输入类型（行业/分行）：")
        value = simpledialog.askstring("输入", "请输入具体的值：")
    except tk.TclError:
        logging.error("用户取消了输入操作")
        return
    
    try:
        df = pd.read_excel(excel_path, sheet_name='日均计算结果')
    except FileNotFoundError:
        logging.error("文件未找到，请检查文件路径")
        return
    except pd.errors.ParserError:
        logging.error("Excel 文件解析错误，请检查文件内容")
        return
    
    if choice == '行业':
        selected_data = df[df['一级行业'] == value]
        print_industry_stats(selected_data, value)
    elif choice == '分行':
        selected_data = df[df['分行'] == value]
        print_branch_stats(selected_data, value)
    else:
        logging.info("无效的输入类型")

excel_path = 'D:\\MyFiles\\文档\兴业材料\\总行\\经营数据\\2024\\0831.xlsx'
if __name__ == "__main__":
    calculate_sum_by_industry(excel_path)