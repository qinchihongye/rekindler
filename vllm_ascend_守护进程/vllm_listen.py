import os
import time
import subprocess
import requests
import json
import logging
import sys
from threading import Thread
import torch
from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional
from fastapi import FastAPI
import uvicorn
import re

# 设置日志
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
    level="INFO"
)
logger = logging.getLogger(__name__)


class ListenerConfig(BaseModel):
    service_name: str = Field("vllm", description="服务名称")
    port: int = Field(8082, description="守护进程服务端口")
    listen_port: int = Field(8081, description="vllm监听端口")
    work_dir: str = Field(os.getcwd(), description="工作目录 (默认为当前文件夹)")
    sh_file: str = Field('vllm_start.sh', description="vllm启动脚本")
    log_dir: Optional[str] = Field(None, description="日志目录（默认在工作目录下log文件夹）")
    check_interval: float = Field(60.0, description="检查间隔（秒）")
    memory_threshold: int = Field(4000, description="内存阈值")
    num_threshold: float = Field(0.5, description="GPU占用数阈值")
    startup_wait_time: float = Field(60.0, description="vllm启动等待时间")

    @validator('log_dir', pre=True, always=True)
    def set_default_log_dir(cls, v, values):
        if v is None and 'work_dir' in values:
            return os.path.join(values['work_dir'], 'log')
        return v


# 从config.json读取配置
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        listener_config = ListenerConfig(**config)

        return listener_config
    except ValidationError as e:
        errors = e.errors()
        error_msg_list = []
        for error in errors:
            field = error['loc'][0]
            message = error['msg']
            error_msg = f"Validation error in field '{field}': {message}"
            error_msg_list.append(error_msg)
            logger.error(error_msg)
        error_str = "\n".join(error_msg_list)
        logger.error(f"加载配置文件失败: {error_str}")
        sys.exit(1)


def if_npus_occupied(memory_threshold: int = 4000, num_threshold: float = 0.5):
    """检查华为NPU是否被占用

    如果NPU内存使用超过memory_threshold，则认为该NPU被占用
    如果被占用的NPU数量超过总NPU数量的num_threshold比例，则返回True
    否则返回False
    """
    try:
        # npu数量
        npu_ct = int(torch.npu.device_count())

        cmd = 'npu-smi info | grep -A 1 "910B"'  # 提取包含910B的行以及下一行
        str_res = os.popen(cmd).read()
        usage_list = str_res.split("\n")

        # 正则：匹配PCI地址（用于定位目标行）
        pci_pattern = r'\b[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]\b'
        usage_lines = [line for line in usage_list
                       if re.search(pci_pattern, line)
                       ]
        # 正则：匹配 ”数字/ 数字“格式，支持空格（用于抓取显存信息）
        memory_pattern = r'(\d+)\s*/\s*(\d+)\s*\| *'
        occupied = [0 for _ in range(npu_ct)]

        if len(usage_lines) == npu_ct:
            for device_id, usage_info in enumerate(usage_lines):
                match = re.search(memory_pattern, usage_info)
                memory_usage = int(match.group(1))
                # total_usage = int(match.group(2)) # total_usage 用不到

                if memory_usage > memory_threshold:  # 如果已分配内存大于内存阈值，则标记该 npu 为被占用
                    occupied[device_id] = 1
        if sum(occupied) <= (npu_ct * num_threshold):  # 若满足，说明有足够的 NPU 未被占用，返回 False
            return False
        return True
    except Exception as e:
        logger.error(f"检查NPU占用时出错: {e}")
        return False


def check_vllm_health(port: int = 8081):
    """检查vllm服务是否正常"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False


def restart_vllm_service(listener_config: ListenerConfig):
    """启动VLLM服务"""
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
    """定期检查VLLM服务是否正常"""
    logger.info(
        f"Starting periodic health check for {listener_config.service_name} on port {listener_config.listen_port}")
    while True:
        try:
            is_health = check_vllm_health(port=listener_config.listen_port)  # 健康检查
            gpu_occupied = if_npus_occupied(memory_threshold=listener_config.memory_threshold,
                                            num_threshold=listener_config.num_threshold
                                            )  # GPU占用

            if (not is_health) and (not gpu_occupied):  # 如果健康检查失败且GPU未被占用，则重启服务
                logger.warning(f"Service {listener_config.service_name} is not healthy, attempting to restart")
                restart_vllm_service(listener_config=listener_config)
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
    vllm_health = check_vllm_health(port=listener_config.listen_port)
    gpu_occupied = if_npus_occupied(memory_threshold=listener_config.memory_threshold,
                                    num_threshold=listener_config.num_threshold
                                    )  # GPU占用
    return {"code": 200,
            "data": {"vllm_health": vllm_health,
                     "gpu_occupied": gpu_occupied
                     }
            }


if __name__ == "__main__":
    # 加载配置
    listener_config = load_config()

    # 确保日志目录存在
    if not os.path.exists(listener_config.log_dir):
        os.makedirs(listener_config.log_dir)

    # 创建带时间戳的日志文件
    timestamp = time.strftime("%Y_%m%d_%H%M", time.localtime())
    log_path = os.path.join(listener_config.log_dir, f"vllm_service_{timestamp}.log")

    SERVICE_COMMAND = {
        "vllm": f"nohup bash {os.path.join(listener_config.work_dir, listener_config.sh_file)} >> {log_path} 2>&1 &"
    }
    logger.info(f"*" * 100)
    logger.info(f"*" * 50)
    logger.info(f"Starting VLLM listener with configuration:")
    logger.info(f"  - Service name:       {listener_config.service_name}")
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
    # restart_vllm_service(listener_config)

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
    uvicorn.run(app, host="0.0.0.0", port=listener_config.port)  # 可以选择你想要的端口
