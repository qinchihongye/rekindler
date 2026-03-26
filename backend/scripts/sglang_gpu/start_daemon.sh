#!/bin/bash
# 启动 SGLang (GPU) 守护进程
# 请从项目根目录运行此脚本

ulimit -n 10240

mkdir -p log

nohup python backend/listener.py --config backend/configs/sglang_gpu.json >> log/nohup_sglang_gpu.log 2>&1 &

echo "SGLang (GPU) daemon started. Check log: tail -f log/nohup_sglang_gpu.log"
