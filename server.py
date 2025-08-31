#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from scripts.agent import agent_router
from scripts.iot_data import data_router

# FastAPI 应用
app = FastAPI()

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 创建静态文件目录
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(agent_router)
app.include_router(data_router)

    
if __name__ == "__main__":
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=12346)
