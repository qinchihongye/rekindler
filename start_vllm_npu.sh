#!/bin/bash
# 启动 vLLM (Ascend NPU) 守护进程

ulimit -n 10240
mkdir -p log

nohup python backend/listener.py --config backend/configs/vllm_npu.json >> log/nohup_vllm_npu.log 2>&1 &

echo "vLLM (NPU) 守护进程已启动，查看日志: tail -f log/nohup_vllm_npu.log"
