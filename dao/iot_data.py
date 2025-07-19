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
from config import IOT_DATA_DB

# 数据库配置
DATABASE_URL = f"sqlite:///{IOT_DATA_DB}"
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
