#!/bin/bash
# 停止 SGLang (GPU) — 守护进程 + 推理服务

echo "正在停止 SGLang (GPU) 守护进程..."
DAEMON_PID=$(ps -ef | grep 'listener.py' | grep 'sglang_gpu' | grep -v grep | awk '{print $2}')
if [ -z "$DAEMON_PID" ]; then
    echo "未找到守护进程。"
else
    kill -9 $DAEMON_PID
    echo "守护进程已停止 (PID: $DAEMON_PID)"
fi

echo "正在停止 SGLang 推理服务..."
SGLANG_PID=$(ps -ef | grep 'sglang.launch_server' | grep -v grep | awk '{print $2}')
if [ -z "$SGLANG_PID" ]; then
    echo "未找到 SGLang 推理服务。"
else
    kill -9 $SGLANG_PID
    echo "SGLang 推理服务已停止 (PID: $SGLANG_PID)"
fi

echo "清理完成。"
