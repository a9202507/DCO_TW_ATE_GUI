from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
import httpx
import asyncio
from typing import Dict, List, Optional
import logging
import uuid
from datetime import datetime, timedelta

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="多客戶端GPIB儀器控制服務器", version="2.0.0")

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

def get_client_info(request: Request) -> Dict:
    """獲取當前客戶端信息"""
    client_ip = get_client_ip(request)
    cleanup_expired_clients()
    
    if client_ip not in clients:
        # 創建新的客戶端記錄
        clients[client_ip] = {
            "ip": client_ip,
            "status": "connected",
            "instruments": [],
            "last_seen": datetime.now(),
            "session_id": str(uuid.uuid4())[:8]
        }
        logger.info(f"新客戶端連接: {client_ip}")
    else:
        # 更新最後見到時間
        clients[client_ip]["last_seen"] = datetime.now()
    
    return clients[client_ip]

# HTML模板 - 修改為支援多客戶端
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GPIB儀器控制系統</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .client-info { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
        .client-info h3 { margin: 0 0 10px 0; }
        .client-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .detail-item { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; }
        .detail-label { font-size: 12px; opacity: 0.8; margin-bottom: 5px; }
        .detail-value { font-size: 16px; font-weight: bold; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .button-group { margin-top: 20px; text-align: center; }
        button { padding: 12px 24px; margin: 0 10px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s; }
        .btn-detection { background: linear-gradient(135deg, #007bff, #0056b3); color: white; }
        .btn-on { background: linear-gradient(135deg, #28a745, #1e7e34); color: white; }
        .btn-off { background: linear-gradient(135deg, #dc3545, #bd2130); color: white; }
        button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .status { margin-top: 20px; padding: 15px; border-radius: 5px; animation: fadeIn 0.5s; }
        .status.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.info { background-color: #cce7ff; color: #004085; border: 1px solid #b8daff; }
        .instruments-section { margin-top: 30px; }
        .instruments-list { margin-top: 15px; }
        .instrument-item { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .instrument-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
        .instrument-name { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px; }
        .instrument-address { font-size: 14px; color: #666; font-family: monospace; background: #e9ecef; padding: 4px 8px; border-radius: 4px; }
        .select-btn { padding: 8px 16px; background: linear-gradient(135deg, #17a2b8, #138496); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .select-btn:hover { transform: translateY(-1px); }
        .no-instruments { text-align: center; padding: 40px; color: #666; font-style: italic; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 15px; }
        .stat-item { text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 GPIB儀器控制系統</h1>
        
        <div class="client-info">
            <h3>📡 您的控制會話</h3>
            <div class="client-details">
                <div class="detail-item">
                    <div class="detail-label">客戶端IP</div>
                    <div class="detail-value" id="clientIP">載入中...</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">會話ID</div>
                    <div class="detail-value" id="sessionID">載入中...</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">連線狀態</div>
                    <div class="detail-value" id="connectionStatus">檢查中...</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">儀器數量</div>
                    <div class="detail-value" id="instrumentCount">0</div>
                </div>
            </div>
        </div>
        
        <div class="form-group">
            <label for="instrumentName">🏷️ 儀器名稱:</label>
            <input type="text" id="instrumentName" placeholder="請輸入儀器名稱或從下方列表選擇">
        </div>
        
        <div class="form-group">
            <label for="instrumentAddress">📍 儀器位址:</label>
            <input type="text" id="instrumentAddress" placeholder="例如: GPIB0::10::INSTR">
        </div>
        
        <div class="button-group">
            <button class="btn-detection" onclick="detectInstruments()">
                <span id="detectText">🔍 偵測我的儀器</span>
            </button>
            <button class="btn-on" onclick="controlInstrument('on')" id="onBtn" disabled>⚡ 開啟電源</button>
            <button class="btn-off" onclick="controlInstrument('off')" id="offBtn" disabled>⏹️ 關閉電源</button>
        </div>
        
        <div id="status"></div>
        
        <div class="instruments-section">
            <h3>🔧 我的儀器列表</h3>
            <div id="instrumentsList" class="instruments-list">
                <div class="no-instruments">尚未偵測到任何儀器，請點擊上方的「偵測我的儀器」按鈕</div>
            </div>
        </div>
    </div>

    <script>
        let clientInfo = {};
        let isDetecting = false;
        
        // 檢查客戶端狀態
        async function checkClientStatus() {
            try {
                const response = await fetch('/api/my-status');
                clientInfo = await response.json();
                
                document.getElementById('clientIP').textContent = clientInfo.ip || '未知';
                document.getElementById('sessionID').textContent = clientInfo.session_id || '未知';
                document.getElementById('connectionStatus').textContent = clientInfo.status === 'connected' ? '已連線' : '未連線';
                document.getElementById('instrumentCount').textContent = clientInfo.instruments?.length || 0;
                
                // 根據連線狀態啟用/禁用按鈕
                const hasInstruments = clientInfo.instruments && clientInfo.instruments.length > 0;
                const hasSelectedInstrument = document.getElementById('instrumentAddress').value.trim() !== '';
                
                document.getElementById('onBtn').disabled = !(clientInfo.status === 'connected' && hasSelectedInstrument);
                document.getElementById('offBtn').disabled = !(clientInfo.status === 'connected' && hasSelectedInstrument);
                
            } catch (error) {
                console.error('檢查客戶端狀態失敗:', error);
                document.getElementById('connectionStatus').textContent = '連線錯誤';
            }
        }
        
        // 偵測儀器
        async function detectInstruments() {
            if (isDetecting) return;
            
            isDetecting = true;
            const detectBtn = document.querySelector('.btn-detection');
            const detectText = document.getElementById('detectText');
            
            detectText.innerHTML = '<span class="loading"></span>正在偵測...';
            detectBtn.disabled = true;
            
            showStatus('正在掃描您的GPIB儀器，請稍候...', 'info');
            
            try {
                const response = await fetch('/api/detect', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    displayInstruments(result.instruments);
                    showStatus(`✅ 成功偵測到 {result.instruments.length} 個儀器`, 'success');
                    
                    // 更新客戶端資訊
                    await checkClientStatus();
                } else {
                    showStatus(`❌ 偵測失敗: {result.message}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ 偵測錯誤: {error.message}`, 'error');
            } finally {
                isDetecting = false;
                detectText.innerHTML = '🔍 偵測我的儀器';
                detectBtn.disabled = false;
            }
        }
        
        // 控制儀器
        async function controlInstrument(action) {
            const name = document.getElementById('instrumentName').value.trim();
            const address = document.getElementById('instrumentAddress').value.trim();
            
            if (!name || !address) {
                showStatus('❌ 請填寫儀器名稱和位址', 'error');
                return;
            }
            
            const actionText = action === 'on' ? '開啟' : '關閉';
            showStatus(`⚙️ 正在{actionText}儀器電源...`, 'info');
            
            // 禁用按鈕防止重複點擊
            document.getElementById('onBtn').disabled = true;
            document.getElementById('offBtn').disabled = true;
            
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, address, action })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus(`✅ 
𝑎
𝑐
𝑡
𝑖
𝑜
𝑛
𝑇
𝑒
𝑥
𝑡
操作成功
:
{name}`, 'success');
                } else {
                    showStatus(`❌ 
𝑎
𝑐
𝑡
𝑖
𝑜
𝑛
𝑇
𝑒
𝑥
𝑡
操作失敗
:
{result.message}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ 操作錯誤: {error.message}`, 'error');
            } finally {
                // 重新啟用按鈕
                setTimeout(() => {
                    const hasSelectedInstrument = document.getElementById('instrumentAddress').value.trim() !== '';
                    document.getElementById('onBtn').disabled = !hasSelectedInstrument;
                    document.getElementById('offBtn').disabled = !hasSelectedInstrument;
                }, 1000);
            }
        }
        
        // 顯示狀態訊息
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = `<div class="status {type}">{message}</div>`;
            
            // 自動清除成功訊息
            if (type === 'success') {
                setTimeout(() => {
                    statusDiv.innerHTML = '';
                }, 5000);
            }
        }
        
        // 顯示儀器列表
        function displayInstruments(instruments) {
            const listDiv = document.getElementById('instrumentsList');
            
            if (instruments.length === 0) {
                listDiv.innerHTML = '<div class="no-instruments">未發現任何GPIB儀器<br><small>請確認儀器已正確連接並開啟電源</small></div>';
                return;
            }
            
            let html = '';
            instruments.forEach((inst, index) => {
                html += `
                    <div class="instrument-item">
                        <div class="instrument-header">
                            <div>
                                <div class="instrument-name">📟 ${inst.name}</div>
                                <div class="instrument-address">${inst.address}</div>
                            </div>
                            <button class="select-btn" onclick="fillInstrumentInfo('${inst.name.replace(/'/g, "\\'")}', '${inst.address}')">
                                選擇此儀器
                            </button>
                        </div>
                    </div>
                `;
            });
            listDiv.innerHTML = html;
        }
        
        // 填入儀器資訊
        function fillInstrumentInfo(name, address) {
            document.getElementById('instrumentName').value = name;
            document.getElementById('instrumentAddress').value = address;
            showStatus(`✅ 已選擇儀器: {name}`, 'success');
            
            // 啟用控制按鈕
            document.getElementById('onBtn').disabled = false;
            document.getElementById('offBtn').disabled = false;
        }
        
        // 監聽輸入框變化
        document.getElementById('instrumentAddress').addEventListener('input', function() {
            const hasValue = this.value.trim() !== '';
            document.getElementById('onBtn').disabled = !hasValue;
            document.getElementById('offBtn').disabled = !hasValue;
        });
        
        // 定期檢查客戶端狀態
        setInterval(checkClientStatus, 10000); // 每10秒檢查一次
        
        // 初始化
        checkClientStatus();
        
        // 頁面載入完成提示
        window.addEventListener('load', function() {
            showStatus('🎉 歡迎使用GPIB儀器控制系統！您可以開始偵測和控制您的儀器了。', 'info');
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """返回主頁面"""
    # 確保客戶端記錄存在
    get_client_info(request)
    return HTML_TEMPLATE

@app.get("/api/my-status")
async def get_my_status(request: Request):
    """獲取當前客戶端的狀態"""
    client_info = get_client_info(request)
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
        error_msg = f"無法連接到您的控制程式，請確認：\n1. app_client.py 正在運行\n2. 防火牆允許8001端口\n3. 網路連接正常"
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
        error_msg = f"無法連接到您的控制程式，請確認 app_client.py 正在運行"
        raise HTTPException(status_code=500, detail=error_msg)

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
