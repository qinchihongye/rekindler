#!/bin/bash
echo "*************************************************************************"
echo "Starting vLLM API server......"
# # vllm启动
# CUDA_VISIBLE_DEVICES=0 \
# vllm serve /mnt/workspace/Qwen/Qwen3-8B-AWQ \
#  --tensor-parallel-size 1 \
#  --max-model-len 32768 \
#  --enable-reasoning --reasoning-parser deepseek_r1 \
#  --gpu-memory-utilization 0.7 \
#  --host 0.0.0.0 \
#  --port 8081 \
#  --dtype auto \
#  --served-model-name Qwen3-8B-AWQ-vllm
# echo "vLLM API server started......"
# echo "*************************************************************************"


# vllm启动
CUDA_VISIBLE_DEVICES=0 \
vllm serve /model/ModelScope/Qwen/Qwen3-0.6B \
 --tensor-parallel-size 1 \
 --max-model-len 32768 \
 --gpu-memory-utilization 0.7 \
 --host 0.0.0.0 \
 --port 8081 \
 --dtype auto \
 --served-model-name Qwen3-0.6B-vllm
echo "vLLM API server started......"
echo "*************************************************************************"