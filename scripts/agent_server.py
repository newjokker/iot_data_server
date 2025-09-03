from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from dao.agent import AgentDAO, AgentCreate


# 创建路由器
agent_router = APIRouter(prefix="/agent", tags=["Agent Management"])


# 初始化DAO
agent_dao = AgentDAO()

# API路由 - 全部使用 /agent 前缀
@agent_router.post("/create_agent")
async def create_agent(agent_data: AgentCreate):
    """添加一个新的Agent"""
    try:
        agent = agent_dao.create_agent(agent_data)
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

@agent_router.get("/health_check/{agent_name}")
async def health_check(agent_name:str):
    """Agent服务的健康检查"""
    
    
    
    # 查看上次上传的时间和对应的上传频率是否对应，要是超过两个频率没有上传就是异常
    
    return {"status": "healthy", "timestamp": datetime.now(beijing_tz), "service": "agent-management"}

