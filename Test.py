import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

df = pd.read_excel('23总结.xlsx')
branch = '福州分行'

filter_df = df[df['主办分行'] == branch]

result_df = filter_df.groupby('二级行业')['日均（亿元）'].sum().sort_values(ascending=False)

print(result_df)

plt.rcParams['font.sans-serif'] = ['SimHei'] 

x = result_df.index
y = result_df.values

# 处理 x 轴标签，每行显示两个中文
formatted_x = []
for label in x:
    words = label.split()
    new_label = []
    line = ""
    for word in words:
        if len(line) + len(word) < 4:  # 假设每个中文字符占 2 个单位
            line += word + " "
        else:
            new_label.append(line.strip())
            line = word + " "+"\n"
    new_label.append(line.strip())
    formatted_x.append("\n".join(new_label))


plt.bar(formatted_x,y)

# 计算日均存款值的汇总数
total_balance = sum(y)

for i, v in enumerate(y):
    percentage = v / total_balance * 100
    plt.text(i, v + 0.1, f"{v:.2f} ({percentage:.2f}%)", ha='center') 



# 添加标题和坐标轴标签
plt.title(branch+'存款柱状图'+'         '+f"机构存款总日均: {total_balance:.2f}")
plt.xlabel('行业')
plt.ylabel('日均存款（亿元）')
#用于旋转 x 轴标签以更好地显示
plt.xticks(rotation=90) 

# 显示图形
plt.show()