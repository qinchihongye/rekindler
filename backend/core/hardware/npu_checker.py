import os
import re
import logging
import torch
import torch_npu

logger = logging.getLogger(__name__)


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
        # 正则：匹配 "数字/ 数字"格式，支持空格（用于抓取显存信息）
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
