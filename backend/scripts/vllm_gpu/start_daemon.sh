#!/bin/bash
# 启动 vLLM (GPU) 守护进程
# 请从项目根目录运行此脚本

ulimit -n 10240

mkdir -p log

nohup python backend/listener.py --config backend/configs/vllm_gpu.json >> log/nohup_vllm_gpu.log 2>&1 &

echo "vLLM (GPU) daemon started. Check log: tail -f log/nohup_vllm_gpu.log"
