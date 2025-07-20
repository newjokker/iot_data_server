#!/bin/bash 

# Check if escalator_algo_server is running
if systemctl is-active --quiet iot_data_server.service; then
    echo "iot_data_server.service is running. Stopping it..."
    sudo systemctl stop iot_data_server.service
    echo "Service stopped."
fi

echo "Copy server to /etc/systemd/system"
sudo cp ./iot_data_server.service  /etc/systemd/system/iot_data_server.service

# Reload systemd daemon, enable, and start the service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling iot_data_server.service..."
sudo systemctl enable iot_data_server.service

echo "Starting iot_data_server.service..."
sudo systemctl start iot_data_server.service

# Wait for 20 seconds
echo "Wait for start..."
sleep 5

# Check the status of the service
echo "Checking the status of iot_data_server.service..."
sudo systemctl status iot_data_server.service

# 查看实时日志
# journalctl -u iot_data_server.service -f 

# 关闭服务
# sudo systemctl disable iot_data_server; sudo systemctl stop iot_data_server

# 开启服务
# sudo systemctl start iot_data_server; sudo systemctl enable iot_data_server



