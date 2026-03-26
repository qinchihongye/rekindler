#!/bin/bash
echo "*************************************************************************"
echo "Starting Mindie server......"
# mindie启动
cd /usr/local/Ascend/mindie/latest/mindie-service/bin

export MINDIE_TO_STDOUT=true
export NPU_MEMORY_FRACTION=0.95

./mindieservice_daemon

echo "Mindie server started......"
echo "*************************************************************************"
