#!/bin/bash
echo "*************************************************************************"
echo "Start to clean vLLM API server process (Ascend NPU)..."

# 查找 vLLM API server 的 PID
VLLM_PID=$(ps -ef |  grep 'vllm.entrypoints.api_server' | grep -v grep| awk '{print $2}')

# 检查是否找到 PID
if [ -z "$VLLM_PID" ]; then
    echo "No vLLM API server process found."
else
    echo "Found vLLM API server PID: $VLLM_PID. Attempting to kill its process tree..."
    # 使用 kill_process_tree 终止进程树
    # 注意：老版本 vllm 使用 from vllm.utils import kill_process_tree
    python3 -c "from vllm.utils.system_utils import kill_process_tree; kill_process_tree($VLLM_PID)"
    echo "Kill command issued. Verify process status with 'ps -ef | grep vllm'."
fi
echo "Cleanup completed..."
echo "*************************************************************************"
