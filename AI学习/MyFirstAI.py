import torch
import torch.nn as nn
import torch.nn.functional as F

class MyFirstAI(nn.Module):
    def __init__(self):
        super(MyFirstAI, self).__init__()
        # 第一层：784个像素输入 -> 512个神经元 (宽度)
        self.fc1 = nn.Linear(784, 512)
        # 第二层：512个神经元 -> 10个数字输出 (深度)
        self.fc2 = nn.Linear(512, 10)

    def forward(self, x):
        # 1. 展平图片：把 28x28 变成 784
        x = x.view(-1, 784)
        # 2. 经过第一层，然后加个“灵魂” ReLU
        x = F.relu(self.fc1(x))
        # 3. 经过第二层，输出原始得分
        x = self.fc2(x)
        return x

# 初始化模型并搬到 M4 Max 的 GPU 上
device = torch.device("mps")
model = MyFirstAI().to(device)
print(f"你的 AI 已经就绪，正在硬件: {device} 上运行")