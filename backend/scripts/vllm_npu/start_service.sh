#!/bin/bash
echo "*************************************************************************"
echo "Starting vLLM API server......"
# vllm启动
export VLLM_RPC_TIMEOUT=50000
CUDA_VISIBLE_DEVICES=0 \
nohup python3 -m vllm.entrypoints.api_server \
 --model /mnt/workspace/Qwen/Qwen3-8B-AWQ \
 --port 8081 \
 --host 0.0.0.0 \
 --tensor-parallel-size 1 \
 --served-model-name Qwen3-8B-AWQ-vllm \
 --enable-auto-tool-choice \
 --tool-call-parser deepseek_r1 \
 --gpu-memory-utilization 0.7 \
 --max-model-len 32768 \
 --enable-expert-parallel \
 --quantization ascend

echo "vLLM API server started......"
echo "*************************************************************************"
