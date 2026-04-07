import asyncio
import sys
from telegram_logger import get_main_logger
import file_indexer
import get_media

main_logger = get_main_logger()

async def run_pipeline():
    """
    调度中枢：按顺序执行文件整理与媒体下载任务
    """
    main_logger.info("="*50)
    main_logger.info("调度中枢启动")
    main_logger.info("="*50)

    # 阶段 1: 存量文件整理（完整性检查、损坏文件隔离、注册表同步）
    main_logger.info(">>> 阶段 1: 执行存量文件完整性检查与整理")
    try:
        # 将同步的阻塞型 I/O 操作放入线程池，避免阻塞异步事件循环
        loop = asyncio.get_running_loop()
        count = await loop.run_in_executor(None, file_indexer.scan_existing_files)
        main_logger.info(f"<<< 阶段 1 完成，共处理/扫描 {count} 个文件")
    except Exception as e:
        main_logger.error(f"!!! 阶段 1 执行异常: {e}")
        import traceback
        traceback.print_exc()
        main_logger.warning("阶段 1 失败，但将继续执行阶段 2...")

    # 阶段 2: 媒体信息获取与下载（防重检查、下载、注册表更新）
    main_logger.info(">>> 阶段 2: 执行媒体信息获取与下载")
    try:
        await get_media.get_all_media_info()
        main_logger.info("<<< 阶段 2 完成")
    except Exception as e:
        main_logger.error(f"!!! 阶段 2 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

    main_logger.info("="*50)
    main_logger.info("全部任务执行完毕")
    main_logger.info("="*50)
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(run_pipeline())
    sys.exit(exit_code)
