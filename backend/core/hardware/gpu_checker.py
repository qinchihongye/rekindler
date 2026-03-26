import os
import logging
import torch

logger = logging.getLogger(__name__)


def if_gpus_occupied(memory_threshold: int = 4000, num_threshold: float = 0.5):
    """检查GPU是否被占用

    如果GPU内存使用超过memory_threshold，则认为该GPU被占用
    如果被占用的GPU数量超过总GPU数量的num_threshold比例，则返回True
    否则返回False
    """
    try:
        cmd = 'nvidia-smi | grep "MiB /"'
        str_res = os.popen(cmd).read()
        usage_lines = [x.split("|")[2] for x in str_res.split("\n") if len(x.split("|")) > 2]
        gpu_ct = int(torch.cuda.device_count())  # gpu数量

        occupied = [0 for _ in range(gpu_ct)]  # 初始化长度为 gpu 数量的全 0 列表，用于标记gpu 是否被占用
        if len(usage_lines) == gpu_ct:
            for device_id, usage_info in enumerate(usage_lines):
                memory_usage = int(usage_info.split("MiB /")[0].strip())  # 提取已分配内存
                if memory_usage > memory_threshold:  # 如果已分配内存大于内存阈值，则标记该 gpu 为被占用
                    occupied[device_id] = 1
        if sum(occupied) <= (gpu_ct * num_threshold):  # 若满足，说明有足够的 GPU 未被占用，返回 False
            return False
        return True
    except Exception as e:
        logger.error(f"检查GPU占用时出错: {e}")
        return False
