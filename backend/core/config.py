import os
import json
import logging
import sys
from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional

logger = logging.getLogger(__name__)


class ListenerConfig(BaseModel):
    service_name: str = Field("vllm", description="服务名称")
    hardware_type: str = Field("gpu", description="硬件类型 (gpu/npu)")
    port: int = Field(8082, description="守护进程服务端口")
    listen_port: int = Field(8081, description="监听端口")
    work_dir: str = Field(os.getcwd(), description="工作目录 (默认为当前文件夹)")
    sh_file: str = Field('start_service.sh', description="启动脚本")
    log_dir: Optional[str] = Field(None, description="日志目录（默认在工作目录下log文件夹）")
    check_interval: float = Field(60.0, description="检查间隔（秒）")
    memory_threshold: int = Field(4000, description="内存阈值")
    num_threshold: float = Field(0.5, description="GPU/NPU占用数阈值")
    startup_wait_time: float = Field(60.0, description="启动等待时间")

    @validator('log_dir', pre=True, always=True)
    def set_default_log_dir(cls, v, values):
        if v is None and 'work_dir' in values:
            return os.path.join(values['work_dir'], 'log')
        return v


def load_config(config_path: str) -> ListenerConfig:
    """从指定路径的 config.json 读取配置"""
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
