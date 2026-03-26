#!/bin/bash
# 启动 SGLang (GPU) 守护进程

ulimit -n 10240
mkdir -p backend/log

nohup python backend/listener.py --config backend/configs/sglang_gpu.json >> backend/log/nohup_sglang_gpu.log 2>&1 &

echo "SGLang (GPU) 守护进程已启动，查看日志: tail -f backend/log/nohup_sglang_gpu.log"
