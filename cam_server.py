import asyncio
from fastapi import FastAPI, Request, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Set
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 存储所有活跃的客户端队列
active_clients: Set[asyncio.Queue] = set()

async def generate_frames(request: Request):
    """生成视频帧响应给客户端"""
    queue = asyncio.Queue()
    active_clients.add(queue)
    logger.info(f"New client connected: {request.client.host}")

    try:
        while True:
            # 从队列获取视频帧
            frame = await queue.get()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except asyncio.CancelledError:
        logger.info(f"Client disconnected: {request.client.host}")
    finally:
        active_clients.discard(queue)

@app.post("/upload_frame")
async def upload_frame(request: Request):
    """接收 ESP32-CAM 推送的视频帧（原始二进制数据）"""
    try:
        # 直接读取请求体中的二进制数据
        frame_data = await request.body()
        
        if not frame_data:
            raise HTTPException(status_code=400, detail="Empty frame data")
        
        logger.info(f"Received frame with size: {len(frame_data)} bytes")
        
        # 分发给所有客户端
        for queue in list(active_clients):
            try:
                queue.put_nowait(frame_data)
            except asyncio.QueueFull:
                logger.warning("Client queue full, skipping frame")
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                active_clients.discard(queue)
        
        return {"status": "ok", "message": "Frame processed"}
    
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
async def video_feed(request: Request):
    """客户端访问的视频流端点（MJPEG）"""
    return StreamingResponse(
        generate_frames(request),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12346)