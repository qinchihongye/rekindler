#!/bin/bash
# 启动 MindIE (Ascend NPU) 守护进程

ulimit -n 10240
mkdir -p log

nohup python backend/listener.py --config backend/configs/mindie_npu.json >> log/nohup_mindie_npu.log 2>&1 &

echo "MindIE (NPU) 守护进程已启动，查看日志: tail -f log/nohup_mindie_npu.log"
