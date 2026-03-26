#!/bin/bash
# 启动 vLLM (GPU) 守护进程

ulimit -n 10240
mkdir -p log

nohup python backend/listener.py --config backend/configs/vllm_gpu.json >> log/nohup_vllm_gpu.log 2>&1 &

echo "vLLM (GPU) 守护进程已启动，查看日志: tail -f log/nohup_vllm_gpu.log"
