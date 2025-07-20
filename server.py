#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Optional
import os
from dao.iot_data import SensorDataDAO, SensorDataModel

# FastAPI 应用
app = FastAPI()
dao = SensorDataDAO()

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 创建静态文件目录
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/iot_data")
async def receive_data(request: Request):
    try:
        raw_data = await request.json()
        
        # 验证必须包含device_id字段
        if "device_id" not in raw_data:
            raise HTTPException(status_code=400, detail="device_id is required")
        
        # 构建数据对象
        device_id = raw_data.pop("device_id")
        sensor_data = SensorDataModel(device_id=device_id, data=raw_data)
        
        # 保存到数据库
        if not dao.save_sensor_data(sensor_data):
            raise HTTPException(status_code=500, detail="Failed to save data")
        
        return JSONResponse(content={"status": "success"}, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"处理数据时出错: {e}")
        raise HTTPException(status_code=400, detail="Invalid data")

@app.get("/get_iot_device_list")
async def get_device_list():
    """获取设备列表"""
    try:
        devices = dao.get_device_list()
        return JSONResponse(content={"status": "success", "devices": devices}, status_code=200)
    except Exception as e:
        print(f"获取设备列表时出错: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device list")

@app.post("/query_iot_data")
async def get_device_info(request: Request):
    """获取设备信息"""
    try:
        
        json_info = await request.json()
        
        device_id = json_info.get("device_id")
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id is required")
        
        limit = json_info.get("limit", 100)
        limit = int(limit)
        if limit <= 0:
            raise HTTPException(status_code=400, detail="limit must be a positive integer")

        # 转换时间格式
        start_time = json_info.get("start_time", None)
        end_time = json_info.get("end_time", None)
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        # 获取数据
        data = dao.query_sensor_data(
            device_id=device_id,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )
        if not data:
            raise HTTPException(status_code=404, detail="Device not found")
        return JSONResponse(content={"status": "success", "data": data}, status_code=200)
    except Exception as e:
        print(f"获取设备信息时出错: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device info")

@app.get("/menu", response_class=HTMLResponse)
async def view_data():
    """数据查看页面"""
    html_path = os.path.join("templates", "data_view.html")
    return FileResponse(html_path)


if __name__ == "__main__":
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=12346)
