#!/bin/bash
echo "*************************************************************************"
echo "Start to clean MindIEServers API server process..."

# 查找 MindIE API server 的 PIDs
MINDIE_PIDS=$(ps -ef | grep 'mindieservice_daemon' | grep -v grep | awk '{print $2}')

# 检查是否找到 PIDs
if [ -z "$MINDIE_PIDS" ]; then
    echo "No MindIEServers API server process found."
else
    echo "Found MindIEServers PIDs: $MINDIE_PIDS. Attempting to kill them..."
    # 循环遍历每个 PID 并终止进程
    for PID in $MINDIE_PIDS; do
        echo "Killing process PID: $PID"
        kill $PID
    done
    echo "Kill commands issued. Verify process status with 'ps -ef | grep mindieservice_daemon'."
fi
echo "Cleanup completed..."
echo "*************************************************************************"
