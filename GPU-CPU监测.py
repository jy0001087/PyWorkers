import time
from datetime import datetime
import subprocess
import requests

# 创建日志文件
log_file_path = f"D:\\GPU、CPU温度记录-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_file = open(log_file_path, 'w')
log_file.write("时间, AMD GPU温度(°C), AMD CPU温度(°C), AMD GPU负载(%), AMD CPU负载(%)\n")


try:
    while True:
        try:
            # 从OpenHardwareMonitor的Web服务器获取数据
            response = requests.get('http://localhost:8085/data.json')
            data = response.json()

            # 筛选AMD相关的数据
            gpu_temp = None
            cpu_temp = None
            gpu_load = None
            cpu_load = None
            gpu_fan = None

            for sensors in data['Children']:
                for sensor in sensors['Children']:
                    for sensor_single in sensor['Children']:
                        if sensor_single['Text'] == 'Temperatures':
                            for sensor_inner in sensor_single['Children']:    
                                if 'CPU Package' in sensor_inner['Text']:
                                    cpu_temp = sensor_inner['Value']
                                elif 'GPU Hot Spot' in sensor_inner['Text']:
                                    gpu_temp = sensor_inner['Value']
                        if sensor_single['Text'] == 'Load':
                            for sensor_inner in sensor_single['Children']:
                                if 'CPU Total' in sensor_inner['Text']:
                                    cpu_load = sensor_inner['Value']                                
                                elif 'GPU Core' in sensor_inner['Text']:
                                    gpu_load = sensor_inner['Value']
                        if sensor_single['Text'] == 'Fans':
                            for sensor_inner in sensor_single['Children']:
                                if 'GPU Fan' in sensor_inner['Text']:
                                    gpu_fan = sensor_inner['Value']  
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 写入日志
            log_file.write(f"{current_time}: GPU温度: {gpu_temp}, 负载: {gpu_load}, 风扇：{gpu_fan};CPU温度: {cpu_temp}, 负载: {cpu_load}\n")
            log_file.flush()  # 立即写入文件

            # 打印到控制台（可选）
            print(f"{current_time}: GPU温度: {gpu_temp}, 负载: {gpu_load}, 风扇：{gpu_fan}; CPU温度: {cpu_temp}, 负载: {cpu_load}")

        except Exception as e:
            print(f"获取数据时出错: {e}")

        # 等待10秒
        time.sleep(10)

except KeyboardInterrupt:
    log_file.close()
    print("日志记录已停止")