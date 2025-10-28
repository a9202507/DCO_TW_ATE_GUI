from fastapi import FastAPI, HTTPException
import pyvisa
import httpx
import asyncio
import logging
from typing import List, Dict
from instruments.daq_factory import DAQFactory
import time
import socket
import threading

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPIB儀器控制客戶端", version="2.0.0")

# VISA資源管理器
rm = None
instruments: Dict[str, any] = {}

# 客戶端配置
CLIENT_CONFIG = {
    "server_host": "192.168.0.144",  # 服務器地址
    "server_port": 8000,
    "client_port": 8001,
    "heartbeat_interval": 30  # 心跳間隔（秒）
}

def get_local_ip():
    """獲取本機IP地址"""
    try:
        # 創建一個UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def initialize_visa():
    """初始化VISA資源管理器"""
    global rm
    try:
        rm = pyvisa.ResourceManager()
        logger.info(f"✅ VISA資源管理器初始化成功 - Backend: {rm}")
        
        # 測試VISA是否正常工作
        resources = rm.list_resources()
        logger.info(f"📡 可用資源: {len(resources)} 個")
        for res in resources:
            logger.info(f"   - {res}")
        
        return True
    except Exception as e:
        logger.error(f"❌ VISA初始化失敗: {e}")
        logger.error("請確認已安裝 VISA 驅動程式和 pyvisa 套件")
        return False

def scan_gpib_instruments() -> List[Dict[str, str]]:
    """掃描所有VISA儀器（包括GPIB、Serial、USB等）"""
    found_instruments = []
    
    if not rm:
        logger.error("❌ VISA資源管理器未初始化")
        return found_instruments
    
    try:
        # 獲取所有可用資源
        resources = rm.list_resources()
        logger.info(f"🔍 掃描所有VISA資源: {resources}")
        logger.info(f"🔌 找到 {len(resources)} 個VISA資源")
        
        # 掃描所有資源
        for resource in resources:
            try:
                logger.info(f"🔗 嘗試連接: {resource}")
                
                # 嘗試連接儀器
                inst = rm.open_resource(resource)
                inst.timeout = 3000  # 3秒超時（縮短以避免Serial port卡住）
                
                # 查詢儀器身份
                instrument_info = None
                
                # 嘗試標準SCPI命令
                for cmd in ['*IDN?', 'ID?']:
                    try:
                        response = inst.query(cmd).strip()
                        if response:
                            instrument_info = {
                                "name": response,
                                "address": resource
                            }
                            logger.info(f"✅ 發現儀器: {response} @ {resource}")
                            break
                    except pyvisa.errors.VisaIOError as e:
                        logger.debug(f"命令 {cmd} 失敗 ({resource}): {e}")
                        continue
                    except Exception as e:
                        logger.debug(f"命令 {cmd} 錯誤 ({resource}): {e}")
                        continue
                
                # 如果所有識別命令都失敗，至少記錄地址
                if not instrument_info:
                    # 判斷資源類型
                    if 'GPIB' in resource:
                        res_type = "GPIB儀器"
                    elif 'ASRL' in resource:
                        res_type = "Serial設備"
                    elif 'USB' in resource:
                        res_type = "USB儀器"
                    elif 'TCPIP' in resource:
                        res_type = "網絡儀器"
                    else:
                        res_type = "VISA儀器"
                    
                    instrument_info = {
                        "name": f"{res_type} @ {resource}",
                        "address": resource
                    }
                    logger.info(f"⚠️ 發現未識別設備: {resource}")
                
                found_instruments.append(instrument_info)
                inst.close()
                
            except pyvisa.errors.VisaIOError as e:
                logger.warning(f"⚠️ VISA錯誤於 {resource}: {e}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ 無法連接到 {resource}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"❌ 掃描儀器時發生錯誤: {e}")
    
    logger.info(f"🎯 掃描完成，共發現 {len(found_instruments)} 個儀器")
    return found_instruments

def control_instrument_power(address: str, action: str) -> tuple[bool, str]:
    """控制儀器電源"""
    if not rm:
        return False, "VISA資源管理器未初始化"
    
    try:
        logger.info(f"🎛️ 控制儀器 {address}: {action}")
        
        inst = rm.open_resource(address)
        inst.timeout = 10000  # 10秒超時
        
        # 獲取儀器標識
        try:
            idn = inst.query('*IDN?').strip()
        except:
            idn = ""
        
        # Chroma 63206A特定命令
        if "Chroma,63206A" in idn:
            commands = {
                'on': ['LOAD ON'],  # Chroma 63206A specific command
                'off': ['LOAD OFF']  # Chroma 63206A specific command
            }
        else:
            # 其他儀器的標準SCPI命令
            commands = {
                'on': ['OUTP ON', 'OUTPUT:STATE ON', ':OUTP:STAT ON', 'OUTP 1'],
                'off': ['OUTP OFF', 'OUTPUT:STATE OFF', ':OUTP:STAT OFF', 'OUTP 0']
            }
        
        success = False
        last_error = ""
        
        for cmd in commands.get(action.lower(), []):
            try:
                inst.write(cmd)
                # 等待命令執行
                time.sleep(0.5)
                
                # 嘗試確認狀態（可選）
                try:
                    inst.write('*OPC?')
                    inst.read()
                except:
                    pass  # 忽略確認失敗
                
                success = True
                logger.info(f"✅ 儀器 {address} {action.upper()} 成功 (命令: {cmd})")
                break
                
            except Exception as e:
                last_error = str(e)
                logger.debug(f"命令 {cmd} 失敗: {e}")
                continue
        
        inst.close()
        
        if success:
            return True, f"儀器 {action.upper()} 操作成功"
        else:
            return False, f"所有控制命令都失敗，最後錯誤: {last_error}"
        
    except Exception as e:
        logger.error(f"❌ 控制儀器 {address} 失敗: {e}")
        return False, f"控制儀器失敗: {str(e)}"

async def heartbeat_to_server():
    """定期向服務器發送心跳"""
    server_url = f"http://{CLIENT_CONFIG['server_host']}:{CLIENT_CONFIG['server_port']}"
    
    while True:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{server_url}/api/my-status")
                if response.status_code == 200:
                    logger.debug("💓 心跳正常")
                else:
                    logger.warning("⚠️ 服務器心跳異常")
        except Exception as e:
            logger.debug(f"💔 心跳失敗: {e}")
        
        await asyncio.sleep(CLIENT_CONFIG['heartbeat_interval'])

@app.on_event("startup")
async def startup_event():
    """啟動時執行"""
    local_ip = get_local_ip()
    logger.info(f"🚀 啟動GPIB儀器控制客戶端...")
    logger.info(f"📍 本機IP: {local_ip}")
    logger.info(f"🌐 服務器: {CLIENT_CONFIG['server_host']}:{CLIENT_CONFIG['server_port']}")
    
    # 初始化VISA
    if not initialize_visa():
        logger.error("❌ VISA初始化失敗，某些功能可能無法使用")
    else:
        # 啟動時執行一次掃描以驗證
        logger.info("🔍 執行啟動掃描...")
        instruments_found = scan_gpib_instruments()
        logger.info(f"✅ 啟動掃描完成，發現 {len(instruments_found)} 個儀器")
    
    # 啟動心跳任務
    asyncio.create_task(heartbeat_to_server())
    
    logger.info("✅ 客戶端啟動完成")

@app.post("/detect")
async def detect_instruments():
    """偵測儀器API端點"""
    try:
        logger.info("🔍 開始偵測VISA儀器...")
        
        start_time = time.time()
        instruments_list = scan_gpib_instruments()
        scan_time = time.time() - start_time
        
        logger.info(f"⏱️ 掃描完成，耗時 {scan_time:.2f} 秒")
        
        return {
            "success": True,
            "instruments": instruments_list,
            "count": len(instruments_list),
            "scan_time": round(scan_time, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ 偵測儀器失敗: {e}")
        return {
            "success": False,
            "message": f"偵測失敗: {str(e)}",
            "instruments": []
        }

@app.post("/control")
async def control_instrument(request: dict):
    """控制儀器API端點"""
    try:
        address = request.get("address")
        action = request.get("action")
        instrument_type = request.get("instrument_type")

        if not all([address, action, instrument_type]):
            raise HTTPException(status_code=400, detail="缺少必要參數 (address, action, instrument_type)")

        logger.info(f"🎛️ 控制請求: {instrument_type} ({address}) - {action.upper()}")

        global rm
        if not rm:
            if not initialize_visa():
                raise HTTPException(status_code=500, detail="VISA資源管理器初始化失敗")

        if instrument_type == 'daq':
            if action == 'read':
                channels_to_read = request.get("value")
                if not channels_to_read or not isinstance(channels_to_read, list):
                    raise HTTPException(status_code=400, detail="缺少DAQ通道參數 (value)")

                from instruments.daq_factory import DAQFactory
                daq_instrument = DAQFactory.create_daq(rm, address)
                if not daq_instrument:
                    raise HTTPException(status_code=404, detail=f"找不到或不支持的DAQ儀器 at {address}")

                if not daq_instrument.connect():
                    raise HTTPException(status_code=500, detail=f"無法連接到DAQ儀器 at {address}")
                
                try:
                    results = daq_instrument.read_channels(channels_to_read)
                    return {
                        "success": True,
                        "message": f"成功讀取 {len(results)} 個通道",
                        "results": results
                    }
                finally:
                    daq_instrument.disconnect()
            else:
                raise HTTPException(status_code=400, detail=f"不支持的DAQ動作: {action}")

        elif instrument_type in ['power_supply', 'eload']:
            success, message = control_instrument_power(address, action)
            return {
                "success": success,
                "message": message,
                "address": address,
                "action": action.upper()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的儀器類型: {instrument_type}")

    except Exception as e:
        logger.error(f"❌ 控制儀器失敗: {e}")
        if isinstance(e, HTTPException):
            return {"success": False, "message": e.detail}
        return {"success": False, "message": f"控制失敗: {str(e)}"}

@app.get("/status")
async def get_status():
    """獲取客戶端狀態"""
    local_ip = get_local_ip()
    
    # 檢查VISA狀態
    visa_status = "正常" if rm else "未初始化"
    available_resources = []
    
    if rm:
        try:
            available_resources = rm.list_resources()
        except:
            visa_status = "錯誤"
    
    return {
        "status": "running",
        "local_ip": local_ip,
        "visa_status": visa_status,
        "available_resources": len(available_resources),
        "resources": available_resources,
        "server_config": CLIENT_CONFIG
    }

@app.get("/debug/resources")
async def debug_resources():
    """Debug endpoint to check raw VISA resources"""
    try:
        if not rm:
            return {"error": "VISA not initialized"}
        resources = rm.list_resources()
        return {
            "visa_backend": str(rm),
            "resources": list(resources),
            "resource_count": len(resources)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    """客戶端資訊頁面"""
    return {
        "message": "GPIB儀器控制客戶端",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "/detect": "偵測儀器",
            "/control": "控制儀器",
            "/status": "獲取狀態",
            "/debug/resources": "調試資源列表"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🔧 GPIB儀器控制客戶端 v2.0.0")
    print("=" * 60)
    print(f"📍 本機IP: {get_local_ip()}")
    print(f"🌐 客戶端API: http://localhost:{CLIENT_CONFIG['client_port']}")
    print(f"🔗 連接服務器: {CLIENT_CONFIG['server_host']}:{CLIENT_CONFIG['server_port']}")
    print("=" * 60)
    print("📝 請確認:")
    print("   1. VISA驅動程式已安裝")
    print("   2. GPIB儀器已正確連接")
    print("   3. 防火牆允許8001端口")
    print("   4. 服務器正在運行")
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=CLIENT_CONFIG['client_port'],
        log_level="info"
    )