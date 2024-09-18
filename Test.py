import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

df = pd.read_excel('23总结.xlsx')
branch = '成都分行'

filter_df = df[df['主办分行'] == branch]

result_df = filter_df.groupby('二级行业')['日均（亿元）'].sum().sort_values(ascending=False)

print(result_df)

plt.rcParams['font.sans-serif'] = ['SimHei'] 

x = result_df.index
y = result_df.values

colors = ['red', 'green', 'blue']  # 自定义颜色列表
plt.gca().set_facecolor('lightgray')  # 例如设置为浅灰色
plt.barh(x,y,color=colors, edgecolor='black', linewidth=0.5, alpha=0.8)


# 计算日均存款值的汇总数
total_balance = sum(y)

for i, v in enumerate(y):
    percentage = v / total_balance * 100
    plt.text(v + 1,i,f"{v:.2f} ({percentage:.2f}%)", ha='left') 



# 添加标题和坐标轴标签
plt.title(branch+'存款柱状图'+'         '+f"机构存款总日均: {total_balance:.2f}")
plt.xlabel('日均存款（亿元）')
plt.ylabel('行业')
#用于旋转 x 轴标签以更好地显示
plt.xticks(rotation=60) 
plt.xlim(0, max(y) * 1.2)  # 根据数据适当调整 x 轴范围
plt.yticks(range(len(x)), x)  # 调整 y 轴刻度标签

# 显示图形
plt.show()