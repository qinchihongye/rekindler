#!/bin/bash
echo "*************************************************************************"
echo "Starting sgLang API server......"
# sglang启动
CUDA_VISIBLE_DEVICES=0 \
python -m sglang.launch_server \
  --model-path /mnt/workspace/Qwen/Qwen3-8B-AWQ \
  --tp 1 \
  --max-prefill-tokens 32768 \
  --mem-fraction-static 0.7 \
  --host 0.0.0.0 \
  --port 8081 \
  --dtype auto \
  --served-model-name Qwen3-8B-AWQ-sglang
echo "sgLang API server started......"
echo "*************************************************************************"
