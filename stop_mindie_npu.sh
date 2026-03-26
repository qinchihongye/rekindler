#!/bin/bash
# 停止 MindIE (Ascend NPU) — 守护进程 + 推理服务

echo "正在停止 MindIE (NPU) 守护进程..."
DAEMON_PID=$(ps -ef | grep 'listener.py' | grep 'mindie_npu' | grep -v grep | awk '{print $2}')
if [ -z "$DAEMON_PID" ]; then
    echo "未找到守护进程。"
else
    kill -9 $DAEMON_PID
    echo "守护进程已停止 (PID: $DAEMON_PID)"
fi

echo "正在停止 MindIE 推理服务..."
MINDIE_PIDS=$(ps -ef | grep 'mindieservice_daemon' | grep -v grep | awk '{print $2}')
if [ -z "$MINDIE_PIDS" ]; then
    echo "未找到 MindIE 推理服务。"
else
    for PID in $MINDIE_PIDS; do
        kill $PID
        echo "MindIE 进程已停止 (PID: $PID)"
    done
fi

echo "清理完成。"
