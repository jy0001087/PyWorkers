import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
import os

class CountdownTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("倒计时时钟")
        self.root.geometry("600x160")  # 调整窗口大小以确保所有控件都能显示
        self.root.attributes("-alpha", 0.1)  # 设置窗口底色全透明
        self.root.overrideredirect(True)  #隐藏标题栏
        self.root.attributes("-topmost", True)  # 窗口置顶
        self.root.config(bg="#5a5d5f")

        # 创建输入框和标签
        self.hour_label = tk.Label(root, text="小时:", font=("Arial", 18))
        self.hour_label.grid(row=0, column=0, padx=10, pady=10)
        self.hour_entry = tk.Entry(root, width=5, font=("Arial", 24))  # 字体放大三倍
        self.hour_entry.insert(0, "0")  # 默认值为0
        self.hour_entry.grid(row=0, column=1, padx=10, pady=10)

        self.minute_label = tk.Label(root, text="分钟:", font=("Arial", 18))
        self.minute_label.grid(row=0, column=2, padx=10, pady=10)
        self.minute_entry = tk.Entry(root, width=5, font=("Arial", 24))  # 字体放大三倍
        self.minute_entry.grid(row=0, column=3, padx=10, pady=10)

        # 加载图标并调整大小
        resources_dir = os.path.join(os.path.dirname(__file__), "resources")
        self.start_icon = PhotoImage(file=os.path.join(resources_dir, "start.png")).subsample(5, 5)  # 缩放图标
        self.stop_icon = PhotoImage(file=os.path.join(resources_dir, "stop.png")).subsample(5, 5)  # 缩放图标

        # 创建按钮
        self.start_button = tk.Button(root, image=self.start_icon, command=self.start_countdown, borderwidth=0)
        self.start_button.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")
        self.stop_button = tk.Button(root, image=self.stop_icon, command=self.stop_countdown, state=tk.DISABLED, borderwidth=0)
        self.stop_button.grid(row=0, column=5, padx=10, pady=10, sticky="nsew")

        # 创建倒计时显示标签
        self.time_label = tk.Label(root, text="00:00:00", font=("Arial", 30), bg="white", relief="solid", borderwidth=1)
        self.time_label.grid(row=1, column=0, columnspan=6, pady=10, padx=10, sticky="nsew")

        # 标志变量，用于控制倒计时是否运行
        self.is_running = False
        self.after_id = None  # 用于存储 root.after 的 ID，方便取消定时器

        # 绑定快捷键
        self.root.bind("<F9>", lambda event: self.start_countdown())
        self.root.bind("<F10>", lambda event: self.stop_countdown())

    def start_countdown(self):
        if self.is_running:  # 如果已经在运行，提示用户
            messagebox.showwarning("警告", "倒计时已经在运行中！")
            return

        # 获取用户输入的小时和分钟
        try:
            hours = int(self.hour_entry.get())
            minutes = int(self.minute_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")
            return

        # 计算总秒数
        total_seconds = hours * 3600 + minutes * 60

        # 如果总秒数为0，提示用户
        if total_seconds == 0:
            messagebox.showerror("输入错误", "倒计时时间不能为0！")
            return

        # 开始倒计时
        self.is_running = True
        self.update_time_label(total_seconds)
        self.countdown(total_seconds)

        # 启用停止按钮，禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def countdown(self, remaining_seconds):
        if remaining_seconds > 0 and self.is_running:
            # 更新倒计时显示
            self.update_time_label(remaining_seconds)
            # 每秒更新一次
            self.after_id = self.root.after(1000, self.countdown, remaining_seconds - 1)
        else:
            # 倒计时结束，弹出提示框
            self.time_label.config(text="倒计时结束！")
            messagebox.showinfo("倒计时结束", "时间到！")
            self.reset_buttons()
            self.is_running = False  # 重置倒计时状态

    def stop_countdown(self):
        # 停止倒计时
        if self.is_running:
            self.is_running = False
            self.time_label.config(text="倒计时已停止！")
            if self.after_id:
                self.root.after_cancel(self.after_id)  # 取消定时器
            self.reset_buttons()

    def reset_buttons(self):
        # 重置按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_time_label(self, total_seconds):
        # 将总秒数转换为小时、分钟和秒
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        # 更新显示标签
        self.time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownTimer(root)
    root.mainloop()