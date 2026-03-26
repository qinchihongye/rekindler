#!/bin/bash
echo "*************************************************************************"
echo "Start to clean daemon server process..."

# 查找 守护进程 的 PID （）用fastapi启动的
DAEMON_PID=$(ps -ef |  grep 'vllm_listen' | grep -v grep| awk '{print $2}')

# 检查是否找到 PID
if [ -z "$DAEMON_PID" ]; then
    echo "No daemon server process  process found."
else
    echo "Found daemon server process  PID: $DAEMON_PID. Attempting to kill its process tree..."
    # 使用 kill_process_tree 终止进程树
    kill -9 $DAEMON_PID
    echo "Kill command issued. Verify process status with 'ps -ef | grep vllm_listen'."
fi
echo "Cleanup completed..."
echo "*************************************************************************"
