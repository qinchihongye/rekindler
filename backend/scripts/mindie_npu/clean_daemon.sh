#!/bin/bash
echo "*************************************************************************"
echo "Start to clean daemon server process..."

# 查找 守护进程 的 PID （通过 listener.py + mindie_npu 配置标识）
DAEMON_PID=$(ps -ef | grep 'listener.py' | grep 'mindie_npu' | grep -v grep | awk '{print $2}')

# 检查是否找到 PID
if [ -z "$DAEMON_PID" ]; then
    echo "No daemon server process found."
else
    echo "Found daemon server process PID: $DAEMON_PID. Attempting to kill..."
    kill -9 $DAEMON_PID
    echo "Kill command issued. Verify process status with 'ps -ef | grep listener.py'."
fi
echo "Cleanup completed..."
echo "*************************************************************************"
