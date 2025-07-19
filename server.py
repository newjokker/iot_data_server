#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
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

@app.get("/query_iot_data")
async def get_data(
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = 100
):
    try:
        data = dao.query_sensor_data(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return JSONResponse(content={"status": "success", "data": data}, status_code=200)
    except Exception as e:
        print(f"查询数据时出错: {e}")
        raise HTTPException(status_code=500, detail="Failed to query data")

@app.get("/menu", response_class=HTMLResponse)
async def view_data(
    request: Request,
    device_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100
):
    """数据查看页面"""
    try:
        # 转换时间格式
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # 获取数据
        data = dao.query_sensor_data(
            device_id=device_id,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )
        
        # 获取设备列表
        devices = dao.get_device_list()
        
        return templates.TemplateResponse(
            "data_view.html",
            {
                "request": request,
                "data": data,
                "devices": devices,
                "current_device": device_id,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit
            }
        )
    except Exception as e:
        print(f"渲染页面时出错: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


if __name__ == "__main__":
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12345)
