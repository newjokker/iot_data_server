from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from scripts.agent import AgentDAO, AgentCreate, AgentResponse, beijing_tz
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import os
from dao.iot_data import SensorDataDAO, SensorDataModel


# 创建路由器
data_router = APIRouter(prefix="/data", tags=["Agent Management"])

dao = SensorDataDAO()


@data_router.post("/iot_data")
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

@data_router.get("/get_iot_device_list")
async def get_device_list():
    """获取设备列表"""
    try:
        devices = dao.get_device_list()
        return JSONResponse(content={"status": "success", "devices": devices}, status_code=200)
    except Exception as e:
        print(f"获取设备列表时出错: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device list")

@data_router.post("/query_iot_data")
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

@data_router.get("/menu")
async def view_data():
    """数据查看页面"""
    html_path = os.path.join("templates", "data_view.html")
    return FileResponse(html_path)

@data_router.post("/delete_device_id")
async def delete_device_id(request: Request):
    try:
        raw_data = await request.json()
        
        # 验证必须包含device_id字段
        if "device_id" not in raw_data:
            raise HTTPException(status_code=400, detail="device_id is required")
        
        # 构建数据对象
        device_id = raw_data.pop("device_id")
        
        if dao.delete_device_data(device_id):
            return JSONResponse(content={"status": "success"}, status_code=200)
        else:
            raise HTTPException(status_code=500, detail="Failed to delete device data")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"处理数据时出错: {e}")
        raise HTTPException(status_code=400, detail="Invalid data")

