#!/bin/bash
echo "*************************************************************************"
echo "Start to clean sgLang API server process..."

# 查找 sgLang API server 的 PID
sgLang_PID=$(ps -ef |  grep 'sglang.launch_server' | grep -v grep| awk '{print $2}')

# 检查是否找到 PID
if [ -z "$sgLang_PID" ]; then
    echo "No sgLang API server process found."
else
    echo "Found sgLang API server PID: $sgLang_PID. Attempting to kill its process tree..."
    # kill sglang进程
    kill -9 $sgLang_PID
    echo "Kill command issued. Verify process status with 'ps -ef | grep sglang.launch_server'."
fi
echo "Cleanup completed..."
echo "*************************************************************************"
