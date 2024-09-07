import numpy as np
import pandas as pd 

array = np.array([1,2,3,4])

print(array+1)
print(array.shape)

df = pd.read_excel('23总结.xlsx')

filter_df = df[df['主办分行'] == '西宁分行']

print(filter_df.groupby('二级行业')['日均（亿元）'].sum().sort_values(ascending=False))