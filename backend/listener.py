import os
import time
import subprocess
import logging
import sys
import argparse
from threading import Thread
from fastapi import FastAPI
import uvicorn

from core.config import ListenerConfig, load_config
from core.health_checker import check_health

# 设置日志
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
    level="INFO"
)
logger = logging.getLogger(__name__)

# 全局变量（在 main 中初始化）
listener_config = None
hardware_checker = None
SERVICE_COMMAND = None


def restart_service(listener_config: ListenerConfig):
    """启动推理服务"""
    logger.info("*" * 50)
    logger.info(f"Restarting service: {listener_config.service_name}")

    try:
        subprocess.run(SERVICE_COMMAND[listener_config.service_name], shell=True)
        logger.info(f"Service {listener_config.service_name} is restarting...,please wait at least {listener_config.startup_wait_time} seconds!!!!!!")
        time.sleep(listener_config.startup_wait_time)  # 等待服务启动
        logger.info(f"Service {listener_config.service_name} restart command executed")

    except Exception as e:
        logger.error(f"Failed to restart service {listener_config.service_name}: {str(e)}")


def periodic_health_check(listener_config: ListenerConfig):
    """定期检查推理服务是否正常"""
    logger.info(
        f"Starting periodic health check for {listener_config.service_name} on port {listener_config.listen_port}")
    while True:
        try:
            is_health = check_health(port=listener_config.listen_port)  # 健康检查
            gpu_occupied = hardware_checker(memory_threshold=listener_config.memory_threshold,
                                            num_threshold=listener_config.num_threshold
                                            )  # GPU/NPU占用

            if (not is_health) and (not gpu_occupied):  # 如果健康检查失败且GPU/NPU未被占用，则重启服务
                logger.warning(f"Service {listener_config.service_name} is not healthy, attempting to restart")
                restart_service(listener_config=listener_config)
            else:
                if not is_health:  # 健康检查失败，但是有显存占用，则可能是还在启动过程中，或者有显存占用
                    logger.info(f"Service {listener_config.service_name} is not healthy, but GPU is occupied, not restart")
                    logger.info(f"Please wait for the GPU to be released,or for the next health check in {listener_config.check_interval} seconds")
                else: # 健康检查成功
                    logger.info(f"Service {listener_config.service_name} is healthy")

        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")

        time.sleep(listener_config.check_interval)


# 初始化FastAPI应用
app = FastAPI()


@app.get("/health")
async def health_check():
    """健康检查接口"""
    service_health = check_health(port=listener_config.listen_port)
    gpu_occupied = hardware_checker(memory_threshold=listener_config.memory_threshold,
                                    num_threshold=listener_config.num_threshold
                                    )  # GPU/NPU占用
    return {"code": 200,
            "data": {f"{listener_config.service_name}_health": service_health,
                     "gpu_occupied": gpu_occupied
                     }
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rekindler - 推理服务守护进程")
    parser.add_argument("--config", required=True, help="配置文件路径 (例如: backend/configs/vllm_gpu.json)")
    args = parser.parse_args()

    # 加载配置
    listener_config = load_config(args.config)

    # 根据 hardware_type 选择硬件检测函数
    if listener_config.hardware_type == "gpu":
        from core.hardware.gpu_checker import if_gpus_occupied
        hardware_checker = if_gpus_occupied
    elif listener_config.hardware_type == "npu":
        from core.hardware.npu_checker import if_npus_occupied
        hardware_checker = if_npus_occupied
    else:
        logger.error(f"Unknown hardware_type: {listener_config.hardware_type}, must be 'gpu' or 'npu'")
        sys.exit(1)

    # 确保日志目录存在
    if not os.path.exists(listener_config.log_dir):
        os.makedirs(listener_config.log_dir)

    # 创建带时间戳的日志文件
    timestamp = time.strftime("%Y_%m%d_%H%M", time.localtime())
    log_path = os.path.join(listener_config.log_dir, f"{listener_config.service_name}_service_{timestamp}.log")

    SERVICE_COMMAND = {
        listener_config.service_name: f"nohup bash {os.path.join(listener_config.work_dir, listener_config.sh_file)} >> {log_path} 2>&1 &"
    }
    logger.info(f"*" * 100)
    logger.info(f"*" * 50)
    logger.info(f"Starting {listener_config.service_name} listener with configuration:")
    logger.info(f"  - Service name:       {listener_config.service_name}")
    logger.info(f"  - Hardware type:      {listener_config.hardware_type}")
    logger.info(f"  - Port:               {listener_config.listen_port}")
    logger.info(f"  - Listening port:     {listener_config.port}")
    logger.info(f"  - Work directory:     {listener_config.work_dir}")
    logger.info(f"  - Log directory:      {listener_config.log_dir}")
    logger.info(f"  - Check interval:     {listener_config.check_interval} seconds")
    logger.info(f"  - startup_wait_time:  {listener_config.startup_wait_time}")
    logger.info(f"  - sh_file:            {listener_config.sh_file}")
    logger.info(f"  - memory_threshold:   {listener_config.memory_threshold}")
    logger.info(f"  - num_threshold:      {listener_config.num_threshold}")
    logger.info(f"  - Startup script:   \n{listener_config.sh_file}")
    logger.info(f"*" * 50)

    # # 启动服务
    # restart_service(listener_config)

    # 启动周期性检查线程
    health_check_thread = Thread(
        target=periodic_health_check,
        daemon=True,
        name="health_check_thread",
        args=(listener_config,)
    )
    health_check_thread.start()

    logger.info("Starting FastAPI application with Uvicorn...")
    # 使用 Uvicorn 运行 FastAPI 应用，这会阻塞主线程
    uvicorn.run(app, host="0.0.0.0", port=listener_config.port)
