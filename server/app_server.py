from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import os
import uuid

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="多客戶端GPIB儀器控制服務器", version="2.0.0")

# 設置模板和靜態文件路徑
# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")),
            name="static")


# 儲存客戶端信息 - 以客戶端IP為key
clients: Dict[str, Dict] = {}

# 客戶端會話超時時間（分鐘）
SESSION_TIMEOUT = 30

def get_client_ip(request: Request) -> str:
    """獲取客戶端真實IP地址"""
    # 檢查是否通過代理
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host

def cleanup_expired_clients():
    """清理過期的客戶端"""
    current_time = datetime.now()
    expired_clients = []
    
    for client_ip, client_info in clients.items():
        last_seen = client_info.get("last_seen")
        if last_seen and (current_time - last_seen).total_seconds() > SESSION_TIMEOUT * 60:
            expired_clients.append(client_ip)
    
    for client_ip in expired_clients:
        del clients[client_ip]
        logger.info(f"清理過期客戶端: {client_ip}")

async def check_client_connection(client_ip: str) -> bool:
    """檢查客戶端程序是否真的在運行"""
    client_url = f"http://{client_ip}:8001"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{client_url}/status")
            return response.status_code == 200
    except:
        return False

def get_client_info(request: Request) -> Dict:
    """獲取當前客戶端信息"""
    client_ip = get_client_ip(request)
    cleanup_expired_clients()
    
    if client_ip not in clients:
        # 創建新的客戶端記錄，初始狀態為 disconnected
        clients[client_ip] = {
            "ip": client_ip,
            "status": "disconnected",
            "instruments": [],
            "last_seen": datetime.now(),
            "session_id": str(uuid.uuid4())[:8]
        }
        logger.info(f"新客戶端連接: {client_ip}")
    else:
        # 更新最後見到時間
        clients[client_ip]["last_seen"] = datetime.now()
    
    return clients[client_ip]

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """返回主頁面"""
    # 確保客戶端記錄存在
    get_client_info(request)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/my-status")
async def get_my_status(request: Request):
    """獲取當前客戶端的狀態"""
    client_info = get_client_info(request)
    client_ip = client_info["ip"]
    
    # 檢查客戶端程序是否真的在運行
    is_connected = await check_client_connection(client_ip)
    client_info["status"] = "connected" if is_connected else "disconnected"
    
    return client_info

@app.post("/api/detect")
async def detect_instruments(request: Request):
    """偵測當前客戶端的儀器"""
    client_info = get_client_info(request)
    client_ip = client_info["ip"]
    
    # 檢查客戶端是否有對應的控制程式在運行
    client_url = f"http://{client_ip}:8001"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{client_url}/detect")
            result = response.json()
            
            if result.get("success"):
                # 更新客戶端的儀器列表
                clients[client_ip]["instruments"] = result.get("instruments", [])
                clients[client_ip]["last_seen"] = datetime.now()
                return result
            else:
                raise HTTPException(status_code=500, detail=result.get("message", "偵測失敗"))
                
    except httpx.RequestError as e:
        logger.error(f"連接客戶端 {client_ip} 失敗: {e}")
        error_msg = "無法連接到您的控制程式，請確認：\n1. app_client.py 正在運行\n2. 防火牆允許8001端口\n3. 網路連接正常"
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/control")
async def control_instrument(request: Request):
    """控制當前客戶端的儀器"""
    client_info = get_client_info(request)
    client_ip = client_info["ip"]
    
    data = await request.json()
    client_url = f"http://{client_ip}:8001"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{client_url}/control", json=data)
            result = response.json()
            
            if result.get("success"):
                clients[client_ip]["last_seen"] = datetime.now()
                return result
            else:
                raise HTTPException(status_code=500, detail=result.get("message", "控制失敗"))
                
    except httpx.RequestError as e:
        logger.error(f"連接客戶端 {client_ip} 失敗: {e}")
        error_msg = "無法連接到您的控制程式，請確認 app_client.py 正在運行"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/status")
async def get_instrument_status(request: Request, instrument_type: str, address: str):
    """獲取儀器的即時狀態"""
    client_info = get_client_info(request)
    client_ip = client_info["ip"]
    client_url = f"http://{client_ip}:8001"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{client_url}/status", 
                params={"instrument_type": instrument_type, "address": address}
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"無法從客戶端 {client_ip} 獲取狀態: {e}")
        # This error is silent on the UI to avoid spamming, but logged here.
        raise HTTPException(status_code=503, detail="無法連接到客戶端控制程式")

@app.get("/api/admin/clients")
async def get_all_clients():
    """管理員接口：獲取所有客戶端（僅供調試使用）"""
    cleanup_expired_clients()
    return {
        "total_clients": len(clients),
        "clients": [
            {
                "ip": info["ip"],
                "session_id": info["session_id"],
                "instruments_count": len(info["instruments"]),
                "last_seen": info["last_seen"].isoformat()
            }
            for info in clients.values()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 啟動多客戶端GPIB儀器控制服務器...")
    print("📱 請在瀏覽器中打開: http://localhost:8000")
    print("🔧 管理員接口: http://localhost:8000/api/admin/clients")
    uvicorn.run(app, host="0.0.0.0", port=8000)
