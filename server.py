#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import pytz
from pydantic import BaseModel
import os

# 数据库配置
DATABASE_URL = "sqlite:///sensor_data.db"
beijing_tz = pytz.timezone('Asia/Shanghai')

# SQLAlchemy 基础配置
Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据模型
class SensorDataModel(BaseModel):
    device_id: str
    data: Dict

# 数据库模型
class SensorData(Base):
    __tablename__ = 'sensor_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(beijing_tz), nullable=False)
    device_id = Column(String(64), nullable=False)
    data_json = Column(JSON, nullable=False)

    __table_args__ = (
        Index('idx_sensor_data_device_id', 'device_id'),
        Index('idx_sensor_data_timestamp', 'timestamp'),
    )

# 创建表
Base.metadata.create_all(bind=engine)

# DAO 类
class SensorDataDAO:
    @contextmanager
    def get_db(self):
        """提供数据库会话上下文"""
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def save_sensor_data(self, sensor_data: SensorDataModel) -> bool:
        """保存传感器数据到数据库"""
        try:
            with self.get_db() as db:
                db_data = SensorData(
                    device_id=sensor_data.device_id,
                    data_json=sensor_data.data
                )
                db.add(db_data)
            return True
        except SQLAlchemyError as e:
            print(f"保存数据到数据库失败: {str(e)}")
            return False

    def query_sensor_data(
        self,
        device_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """查询传感器数据"""
        with self.get_db() as db:
            query = db.query(SensorData)
            
            if device_id:
                query = query.filter(SensorData.device_id == device_id)
            if start_time:
                query = query.filter(SensorData.timestamp >= start_time)
            if end_time:
                query = query.filter(SensorData.timestamp <= end_time)
                
            query = query.order_by(SensorData.timestamp.desc())
            
            if limit:
                query = query.limit(limit)
                
            return [
                {
                    "id": record.id,
                    "timestamp": record.timestamp.isoformat(),
                    "device_id": record.device_id,
                    "data": record.data_json
                }
                for record in query
            ]
    
    def get_device_list(self) -> List[str]:
        """获取所有设备的唯一ID列表"""
        with self.get_db() as db:
            devices = db.query(SensorData.device_id).distinct().all()
            return [device[0] for device in devices]

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

@app.get("/", response_class=HTMLResponse)
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

@app.on_event("startup")
async def startup_event():
    print(f"服务已启动，数据将保存到SQLite数据库: {DATABASE_URL}")
    # 确保模板目录存在
    os.makedirs("templates", exist_ok=True)
    
    # 创建默认模板文件（如果不存在）
    create_default_templates()

def create_default_templates():
    """创建默认的HTML模板文件"""
    # 数据查看页面模板
    data_view_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoT 数据查看</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.0/font/bootstrap-icons.css">
    <style>
        .json-data {
            max-height: 200px;
            overflow-y: auto;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
        }
        .filter-section {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .device-badge {
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="mb-4">IoT 数据查看</h1>
        
        <!-- 筛选表单 -->
        <div class="filter-section">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    <label for="device_id" class="form-label">设备ID</label>
                    <select class="form-select" id="device_id" name="device_id">
                        <option value="">全部设备</option>
                        {% for device in devices %}
                        <option value="{{ device }}" {% if device == current_device %}selected{% endif %}>{{ device }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-3">
                    <label for="start_time" class="form-label">开始时间</label>
                    <input type="datetime-local" class="form-control" id="start_time" name="start_time" value="{{ start_time }}">
                </div>
                <div class="col-md-3">
                    <label for="end_time" class="form-label">结束时间</label>
                    <input type="datetime-local" class="form-control" id="end_time" name="end_time" value="{{ end_time }}">
                </div>
                <div class="col-md-2">
                    <label for="limit" class="form-label">显示条数</label>
                    <input type="number" class="form-control" id="limit" name="limit" min="1" value="{{ limit }}">
                </div>
                <div class="col-12">
                    <button type="submit" class="btn btn-primary">筛选</button>
                    <a href="/" class="btn btn-outline-secondary ms-2">重置</a>
                </div>
            </form>
        </div>
        
        <!-- 设备快捷筛选 -->
        <div class="mb-3">
            <span class="me-2">快速筛选:</span>
            {% for device in devices %}
            <span class="badge bg-secondary device-badge me-1" onclick="filterDevice('{{ device }}')">{{ device }}</span>
            {% endfor %}
        </div>
        
        <!-- 数据表格 -->
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>设备ID</th>
                        <th>时间戳</th>
                        <th>数据</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in data %}
                    <tr>
                        <td>{{ item.id }}</td>
                        <td>{{ item.device_id }}</td>
                        <td>{{ item.timestamp }}</td>
                        <td>
                            <div class="json-data">
                                <pre>{{ item.data | tojson(indent=2) }}</pre>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="4" class="text-center">没有找到数据</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- 数据统计 -->
        <div class="mt-3 text-muted">
            共显示 {{ data | length }} 条记录
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function filterDevice(deviceId) {
            document.getElementById('device_id').value = deviceId;
            document.querySelector('form').submit();
        }
        
        // 自动填充时间格式
        document.addEventListener('DOMContentLoaded', function() {
            const now = new Date();
            const timeInputs = document.querySelectorAll('input[type="datetime-local"]');
            
            // 如果没有值，设置默认时间范围（最近24小时）
            if (!timeInputs[0].value && !timeInputs[1].value) {
                const endTime = new Date();
                const startTime = new Date();
                startTime.setDate(startTime.getDate() - 1);
                
                timeInputs[0].value = formatDateTimeLocal(startTime);
                timeInputs[1].value = formatDateTimeLocal(endTime);
            }
        });
        
        function formatDateTimeLocal(date) {
            return date.toISOString().slice(0, 16);
        }
    </script>
</body>
</html>
"""

    # 错误页面模板
    error_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>错误</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger">
            <h4 class="alert-heading">发生错误</h4>
            <p>{{ error }}</p>
            <hr>
            <a href="/" class="btn btn-outline-danger">返回首页</a>
        </div>
    </div>
</body>
</html>
"""

    # 创建模板文件（如果不存在）
    templates_dir = "templates"
    os.makedirs(templates_dir, exist_ok=True)
    
    if not os.path.exists(os.path.join(templates_dir, "data_view.html")):
        with open(os.path.join(templates_dir, "data_view.html"), "w", encoding="utf-8") as f:
            f.write(data_view_html)
    
    if not os.path.exists(os.path.join(templates_dir, "error.html")):
        with open(os.path.join(templates_dir, "error.html"), "w", encoding="utf-8") as f:
            f.write(error_html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12345)
