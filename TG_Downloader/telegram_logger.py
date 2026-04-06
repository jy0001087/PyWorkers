import logging
import os
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_file, level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        name (str): 日志记录器名称
        log_file (str): 日志文件路径
        level: 日志级别
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def get_group_logger(group_name, group_id):
    """
    获取群组日志记录器
    
    Args:
        group_name (str): 群组名称
        group_id (str): 群组ID
    
    Returns:
        logging.Logger: 群组日志记录器
    """
    # 使用当前日期时间作为文件名的一部分
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/{group_name}_{group_id}_{timestamp}.log"
    return setup_logger(f"group_{group_id}", log_file)

def get_topic_logger(group_name, group_id, topic_title, topic_id):
    """
    获取话题日志记录器
    
    Args:
        group_name (str): 群组名称
        group_id (str): 群组ID
        topic_title (str): 话题标题
        topic_id (str): 话题ID
    
    Returns:
        logging.Logger: 话题日志记录器
    """
    # 使用当前日期时间作为文件名的一部分
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/{group_name}_{topic_title}_{group_id}_{topic_id}_{timestamp}.log"
    return setup_logger(f"topic_{topic_id}", log_file)

def get_main_logger():
    """
    获取主日志记录器
    
    Returns:
        logging.Logger: 主日志记录器
    """
    log_file = "logs/main.log"
    return setup_logger("main", log_file)

def test_logger():
    """
    测试日志记录器功能
    """
    print("开始测试日志记录器功能...")
    
    # 测试主日志记录器
    main_logger = get_main_logger()
    main_logger.info("这是主日志记录器的测试信息")
    main_logger.warning("这是主日志记录器的警告信息")
    main_logger.error("这是主日志记录器的错误信息")
    
    # 测试群组日志记录器
    group_logger = get_group_logger("测试群组", "123456")
    group_logger.info("这是群组日志记录器的测试信息")
    group_logger.debug("这是群组日志记录器的调试信息")
    
    # 测试话题日志记录器
    topic_logger = get_topic_logger("测试群组", "123456", "测试话题", "789012")
    topic_logger.info("这是话题日志记录器的测试信息")
    topic_logger.info("测试完成")
    
    print("日志记录器测试完成！")

if __name__ == "__main__":
    test_logger()