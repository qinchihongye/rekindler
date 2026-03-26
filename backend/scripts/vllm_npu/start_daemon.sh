#!/bin/bash
# 启动 vLLM (Ascend NPU) 守护进程
# 请从项目根目录运行此脚本

ulimit -n 10240

mkdir -p log

nohup python backend/listener.py --config backend/configs/vllm_npu.json >> log/nohup_vllm_npu.log 2>&1 &

echo "vLLM (NPU) daemon started. Check log: tail -f log/nohup_vllm_npu.log"
