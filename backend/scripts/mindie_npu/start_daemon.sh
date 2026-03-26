#!/bin/bash
# 启动 MindIE (Ascend NPU) 守护进程
# 请从项目根目录运行此脚本

ulimit -n 10240

mkdir -p log

nohup python backend/listener.py --config backend/configs/mindie_npu.json >> log/nohup_mindie_npu.log 2>&1 &

echo "MindIE (NPU) daemon started. Check log: tail -f log/nohup_mindie_npu.log"
