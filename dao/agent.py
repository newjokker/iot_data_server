#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import HTTPException
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import pytz
from pydantic import BaseModel
from config import AGENT_DB


DATABASE_URL = f"sqlite:///{AGENT_DB}"  
beijing_tz = pytz.timezone('Asia/Shanghai')

# SQLAlchemy 配置
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

class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime, default=lambda: datetime.now(beijing_tz), nullable=False)
    name = Column(String(100), nullable=False, unique=True)
    freq = Column(Integer, nullable=False)  # 上传频率，单位：1/freq 秒
    describe = Column(String(256), nullable=True)

# 创建数据表（如果尚未创建）
Base.metadata.create_all(bind=engine)


class AgentCreate(BaseModel):
    name: str
    freq: int
    describe: Optional[str] = None

class AgentUpdate(BaseModel):
    freq: Optional[int] = None
    describe: Optional[str] = None

class AgentOut(BaseModel):
    id: int
    create_time: datetime
    name: str
    freq: int
    describe: Optional[str]
    
    class Config:
        orm_mode = True


class AgentDAO:
    @contextmanager
    def get_db(self):
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def create_agent(self, name: str, freq: int, describe: Optional[str] = None) -> Agent:
        with self.get_db() as db:
            # 检查是否已存在同名 agent
            existing = db.query(Agent).filter(Agent.name == name).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Agent with name '{name}' already exists.")
            agent = Agent(name=name, freq=freq, describe=describe)
            db.add(agent)
            db.flush()  # 为了能拿到 agent.id（可选）
            return agent

    def delete_agent(self, name: int) -> bool:
        with self.get_db() as db:
            agent = db.query(Agent).filter(Agent.name == name).first()
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent with name {name} not found.")
            db.delete(agent)
            return True

    def get_agent(self, name: str) -> Optional[Agent]:
        with self.get_db() as db:
            return db.query(Agent).filter(Agent.name == name).first()

    def get_all_agents(self) -> Dict[str, Dict]:
        with self.get_db() as db:
            agents = db.query(Agent).all()
            result = {}
            for agent in agents:
                result[agent.name] = {
                    "id": agent.id,
                    "create_time": agent.create_time,
                    "name": agent.name,
                    "freq": agent.freq,
                    "describe": agent.describe
                }
            return result

    def update_agent(self, name: str, freq: Optional[int] = None, describe: Optional[str] = None) -> Agent:
        with self.get_db() as db:
            agent = db.query(Agent).filter(Agent.name == name).first()
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent with name '{name}' not found.")
            if freq is not None:
                agent.freq = freq
            if describe is not None:
                agent.describe = describe
            return agent

