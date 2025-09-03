#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from dao.agent_info import AgentDAO, AgentCreate, beijing_tz
from dao.iot_data_info import SensorDataDAO

# 创建路由器
agent_router = APIRouter(prefix="/agent", tags=["Agent Management"])

agent_dao = AgentDAO()

@agent_router.post("/create_agent")
async def create_agent(agent_data: AgentCreate):
    """添加一个新的Agent"""
    try:
        agent = agent_dao.create_agent(name=agent_data.name, freq=agent_data.freq, describe=agent_data.describe)
        return agent
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.delete("/delete_agent/{agent_name}")
async def delete_agent(agent_name: str):
    """删除指定的Agent"""
    try:
        success = agent_dao.delete_agent(agent_name)
        if success:
            return {"message": "Agent deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.get("/get_agent/{agent_name}")
async def get_agent(agent_name: str):
    """获取指定Agent的详细信息"""
    try:
        agent = agent_dao.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.get("/get_all_agent")
async def get_all_agents():
    """获取所有Agent的信息列表"""
    try:
        agents = agent_dao.get_all_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.put("/update_agent/{agent_id}")
async def update_agent(agent_id: int, agent_data: AgentCreate):
    """更新指定Agent的信息"""
    try:
        agent = agent_dao.update_agent(agent_id, agent_data)
        return agent
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_agent_status():
    """获取所有的 agent 的健康状态"""
    agent_status = {}
    agents = agent_dao.get_all_agents()
    for each in agents:
        each_name = agents[each]["name"]
        
        agent = agent_dao.get_agent(each_name)
        
        if agent is None:
            agent_status[each_name] = {"status": "healthy"}
        else:
            start_time = datetime.now(beijing_tz)
            start_time = start_time - timedelta(seconds=agent["freq"])
            sensor_data = SensorDataDAO()
            info = sensor_data.query_sensor_data(device_id=each_name, start_time=start_time, limit=1)
            if len(info) > 0:
                agent_status[each_name] = {"status": "healthy"}
            else:
                agent_status[each_name] = {"status": "unhealthy"}
    return agent_status       
    

@agent_router.get("/health_check/{agent_name}")
async def health_check(agent_name:str):
    """Agent服务的健康检查"""
    
    if agent_name =="*":
        agent_status_info = get_agent_status()
        return {"status": "success", "info": agent_status_info}
        
    else:
        agent = agent_dao.get_agent(agent_name)
        
        if agent is None:
            return {"status": "failed", "error_info": f"未找到对应的 agent:{agent_name}"}
        else:
            start_time = datetime.now(beijing_tz)
            start_time = start_time - timedelta(seconds=agent["freq"])
            sensor_data = SensorDataDAO()
            info = sensor_data.query_sensor_data(device_id=agent_name, start_time=start_time, limit=1)
            if len(info) > 0:
                return {"status": "success", "info": [{agent_name: {"status": "healthy"}}]}
        
    return {"status": "success", "info": [{agent_name: {"status": "unhealthy"}}]}

