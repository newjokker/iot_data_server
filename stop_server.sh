#!/bin/bash

# 删除启动的算法服务


pid=$(ps -ef | grep "/usr/local/bin/uvicorn server:app" | grep -v grep | awk 'NR==1{print $2}')

# 如果找到 PID，则终止该进程
if [ -n "$pid" ]; then
    kill -9 $pid
    echo "已终止 Python 进程 (PID: $pid)"
else
    echo "未找到运行的 Python 进程"
fi