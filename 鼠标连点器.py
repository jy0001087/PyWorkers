import pyautogui
import time
import threading
import sys
import pynput # 新增导入 pynput

# 设置点击间隔（秒）
CLICK_INTERVAL = 0.1

# 控制连点器的运行状态
clicking = False
running_listener = True

# 设置退出热键
# 注意：pyautogui.hotkey() 函数用于模拟按键组合，
# 但在这里我们使用它来检查按键状态以便在后台线程中停止脚本。
# 对于更可靠的退出机制，可以考虑使用 pynput 库。
# 但对于简单的连点器，我们先用一个简单的机制。
EXIT_HOTKEY = ('ctrl', 'c') # 按下 Ctrl+C 退出

def clicker_thread_func():
    global clicking
    print(f"鼠标连点器已启动。每 {CLICK_INTERVAL} 秒点击一次。")
    while running_listener:
        if clicking:
            pyautogui.click()
        time.sleep(CLICK_INTERVAL)
    print("鼠标连点器已完全停止。")

def on_press(key):
    global clicking, running_listener
    try:
        # 监听 Ctrl+[
        if key == pynput.keyboard.Key.f1: # 使用 F1 作为开始键，避免与终端快捷键冲突
            if not clicking:
                clicking = True
                print("检测到 F1。开始连点...")
        # 监听 Ctrl+]
        elif key == pynput.keyboard.Key.f8: # 使用 F8 作为结束键，避免与终端快捷键冲突
            if clicking:
                clicking = False
                print("检测到 F8。停止连点。")
        # 监听 Esc 退出整个程序
        elif key == pynput.keyboard.Key.esc:
            print("检测到 Esc。正在退出程序...")
            running_listener = False
            return False # 停止监听器
    except AttributeError:
        pass # 处理非特殊按键，例如普通字母或数字

if __name__ == "__main__":
    # 在 macOS 上，你可能需要在“系统偏好设置”>“安全性与隐私”>“隐私”>“辅助功能”中
    # 授予终端或你的 IDE（如 VS Code）控制电脑的权限，否则 pyautogui 可能无法工作。

    print("鼠标连点器已启动。")
    print("按下 F1  开始连点。")
    print("按下 F8  停止连点。")
    print("按下 Esc 退出程序。")

    # 启动点击线程
    click_thread = threading.Thread(target=clicker_thread_func)
    click_thread.start()

    # 启动键盘监听器
    with pynput.keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    click_thread.join()