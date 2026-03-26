#!/bin/bash
# 停止 vLLM (Ascend NPU) — 守护进程 + 推理服务

echo "正在停止 vLLM (NPU) 守护进程..."
DAEMON_PID=$(ps -ef | grep 'listener.py' | grep 'vllm_npu' | grep -v grep | awk '{print $2}')
if [ -z "$DAEMON_PID" ]; then
    echo "未找到守护进程。"
else
    kill -9 $DAEMON_PID
    echo "守护进程已停止 (PID: $DAEMON_PID)"
fi

echo "正在停止 vLLM 推理服务..."
VLLM_PID=$(ps -ef | grep 'vllm.entrypoints.api_server' | grep -v grep | awk '{print $2}')
if [ -z "$VLLM_PID" ]; then
    echo "未找到 vLLM 推理服务。"
else
    # 注意：老版本 vllm 使用 from vllm.utils import kill_process_tree
    python3 -c "from vllm.utils.system_utils import kill_process_tree; kill_process_tree($VLLM_PID)" 2>/dev/null || kill -9 $VLLM_PID
    echo "vLLM 推理服务已停止 (PID: $VLLM_PID)"
fi

echo "清理完成。"
