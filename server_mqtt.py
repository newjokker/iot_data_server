#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from datetime import datetime
from typing import Optional
import os
from dao.iot_data_info import SensorDataDAO, SensorDataModel
import paho.mqtt.client as mqtt
import ssl

# 数据库访问层
dao = SensorDataDAO()

# MQTT 配置
MQTT_BROKER = "broker.emqx.io"          # 公共测试服务器，生产环境请自建
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "iot/data"            # 设备发布数据的主题
MQTT_TOPIC_COMMAND = "iot/command"      # 服务端下发命令的主题

# 创建静态文件目录（保留原有Web界面）
os.makedirs("static", exist_ok=True)

class MQTTServer:
    def __init__(self):
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc, properties):
        print(f"Connected with result code {rc}")
        client.subscribe(MQTT_TOPIC_DATA)  # 订阅设备数据主题
        client.subscribe(f"{MQTT_TOPIC_COMMAND}/+")  # 订阅所有命令响应

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            data = json.loads(payload)

            if topic.startswith(MQTT_TOPIC_DATA):
                # 处理设备上报数据
                self.handle_sensor_data(data)
            elif topic.startswith(MQTT_TOPIC_COMMAND):
                # 处理设备响应（可选）
                print(f"Received command response: {data}")

        except Exception as e:
            print(f"Error processing message: {e}")

    def handle_sensor_data(self, data):
        """处理传感器数据并存入数据库"""
        if "device_id" not in data:
            print("Missing device_id in payload")
            return

        device_id = data.pop("device_id")
        sensor_data = SensorDataModel(device_id=device_id, data=data)
        
        if not dao.save_sensor_data(sensor_data):
            print("Failed to save sensor data")
        else:
            print(f"Data saved for device {device_id}")

    def publish_command(self, device_id, command):
        """向特定设备发送命令"""
        topic = f"{MQTT_TOPIC_COMMAND}/{device_id}"
        self.client.publish(topic, json.dumps(command))

    def start(self):
        # 启用TLS（生产环境推荐）
        # self.client.tls_set(ca_certs=None, cert_reqs=ssl.CERT_REQUIRED)
        # self.client.username_pw_set("username", "password")
        
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

# 保留原有的HTTP接口（可选）
from fastapi import FastAPI, HTTPException
app = FastAPI()
mqtt_server = MQTTServer()

@app.on_event("startup")
async def startup_event():
    mqtt_server.start()

@app.on_event("shutdown")
async def shutdown_event():
    mqtt_server.stop()

if __name__ == "__main__":
    # 启动MQTT服务
    server = MQTTServer()
    server.start()
    
    try:
        # 保持主线程运行
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        server.stop()