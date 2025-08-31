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
from config import IOT_DATA_DB, AGENT_DB

# 数据库配置
DATABASE_URL = f"sqlite:///{AGENT_DB}"
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

# Pydantic 模型
class AgentCreate(BaseModel):
    name: str
    url: str
    describe: Optional[str] = None

class AgentResponse(BaseModel):
    id: int
    name: str
    url: str
    describe: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# 数据库模型
class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(beijing_tz), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(String(256), nullable=False)
    describe = Column(String(256), nullable=True)

    # 创建索引
    __table_args__ = (
        Index('idx_name', 'name'),
        Index('idx_timestamp', 'timestamp'),
    )

# 创建表
Base.metadata.create_all(bind=engine)

# DAO 类
class AgentDAO:
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

    def create_agent(self, agent_data: AgentCreate) -> Agent:
        """添加agent"""
        with self.get_db() as db:
            # 检查是否已存在相同名称的agent
            existing_agent = db.query(Agent).filter(Agent.name == agent_data.name).first()
            if existing_agent:
                raise HTTPException(status_code=400, detail="Agent with this name already exists")
            
            # 创建新agent
            agent = Agent(
                name=agent_data.name,
                url=agent_data.url,
                describe=agent_data.describe
            )
            db.add(agent)
            db.flush()  # 获取生成的ID
            db.refresh(agent)
            return agent

    def delete_agent(self, agent_id: int) -> bool:
        """删除agent"""
        with self.get_db() as db:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            db.delete(agent)
            return True

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """获取单个agent信息"""
        with self.get_db() as db:
            return db.query(Agent).filter(Agent.id == agent_id).first()

    def get_all_agents(self) -> List[Agent]:
        """获取所有agent信息列表"""
        with self.get_db() as db:
            return db.query(Agent).order_by(Agent.timestamp.desc()).all()

    def update_agent(self, agent_id: int, agent_data: AgentCreate) -> Optional[Agent]:
        """更新agent信息"""
        with self.get_db() as db:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # 检查名称是否与其他agent冲突
            if agent_data.name != agent.name:
                existing_agent = db.query(Agent).filter(Agent.name == agent_data.name).first()
                if existing_agent:
                    raise HTTPException(status_code=400, detail="Agent with this name already exists")
            
            agent.name = agent_data.name
            agent.url = agent_data.url
            agent.describe = agent_data.describe
            db.commit()
            db.refresh(agent)
            return agent

