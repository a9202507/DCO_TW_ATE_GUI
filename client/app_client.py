from fastapi import FastAPI, HTTPException
import pyvisa
import httpx
import asyncio
import logging
from typing import List, Dict, Optional
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
    "server_host": "127.0.0.1",  # 服務器地址
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
    """掃描所有VISA儀器（確保每次都獲取最新列表）"""
    found_instruments = []
    local_rm = None

    try:
        # 每次掃描都創建一個新的ResourceManager以避免快取
        local_rm = pyvisa.ResourceManager()
    except Exception as e:
        logger.error(f"❌ VISA初始化失敗: {e}")
        logger.error("請確認已安裝 VISA 驅動程式和 pyvisa 套件")
        return found_instruments

    try:
        resources = local_rm.list_resources()
        logger.info(f"🔍 掃描所有VISA資源: {resources}")
        logger.info(f"🔌 找到 {len(resources)} 個VISA資源")
        
        for resource in resources:
            try:
                logger.info(f"🔗 嘗試連接: {resource}")
                
                inst = local_rm.open_resource(resource)
                inst.timeout = 3000
                
                instrument_info = None
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
                    except pyvisa.errors.VisaIOError:
                        continue
                    except Exception:
                        continue
                
                if not instrument_info:
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

def control_dc_source_instrument(address: str, action: str, value: Optional[str] = None) -> tuple[bool, str]:
    """控制電源 (使用工廠實例)"""
    if not rm:
        return False, "VISA資源管理器未初始化"
    
    try:
        logger.info(f"🎛️ 控制儀器 {address}: action={action}, value={value}")
        
        # 對於電源供應器，使用工廠創建實例
        from instruments.power_supply_factory import DCSourceFactory
        instrument = DCSourceFactory.create_dc_source(rm, address)
        
        if not instrument:
            return False, f"不支持的電源供應器類型 at {address}"
        
        if not instrument.connect():
            return False, f"無法連接到電源供應器 at {address}"
        
        try:
            if action == 'on':
                success, message = instrument.turn_on()
            elif action == 'off':
                success, message = instrument.turn_off()
            elif action == 'set_voltage':
                if value is not None:
                    success = instrument.set_voltage(1, float(value))
                    message = "電壓設定成功" if success else "電壓設定失敗"
                else:
                    return False, "設定電壓需要提供數值"
            elif action == 'set_current':
                if value is not None:
                    success = instrument.set_current(1, float(value))
                    message = "電流設定成功" if success else "電流設定失敗"
                else:
                    return False, "設定電流需要提供數值"
            else:
                return False, f"不支持的動作: {action}"
            
            return success, message
            
        finally:
            instrument.disconnect()
            
    except Exception as e:
        logger.error(f"❌ 控制儀器 {address} 失敗: {e}")
        return False, f"控制儀器失敗: {str(e)}"

def control_eload_instrument(address: str, action: str, value: Optional[str] = None) -> tuple[bool, str]:
    """控制電子負載 (使用工廠實例)"""
    if not rm:
        return False, "VISA資源管理器未初始化"

    try:
        logger.info(f"🎛️ 控制電子負載 {address}: action={action}, value={value}")

        from instruments.eload_factory import LoadFactory
        instrument = LoadFactory.create_load(rm, address)

        if not instrument:
            return False, f"不支持的電子負載類型 at {address}"

        if not instrument.connect():
            return False, f"無法連接到電子負載 at {address}"

        try:
            if action == 'on':
                success, message = instrument.turn_on()
            elif action == 'off':
                success, message = instrument.turn_off()
            elif action == 'set_mode':
                if value is not None:
                    instrument.set_mode(str(value))
                    success, message = True, f"模式設定為 {value} 成功"
                else:
                    return False, "設定模式需要提供數值"
            elif action == 'set_current':
                if value is not None:
                    instrument.set_current(float(value))
                    success, message = True, "電流設定成功"
                else:
                    return False, "設定電流需要提供數值"
            else:
                return False, f"不支持的動作: {action}"
            
            return success, message

        finally:
            instrument.disconnect()

    except Exception as e:
        logger.error(f"❌ 控制電子負載 {address} 失敗: {e}")
        return False, f"控制電子負載失敗: {str(e)}"

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
        value = request.get("value")

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

        elif instrument_type == 'power-supply':
            from instruments.power_supply_factory import DCSourceFactory
            instrument = DCSourceFactory.create_dc_source(rm, address)
            if not instrument:
                raise HTTPException(status_code=404, detail=f"找不到或不支持的電源供應器 at {address}")

            if not instrument.connect():
                raise HTTPException(status_code=500, detail=f"無法連接到電源供應器 at {address}")
            
            try:
                if action == 'set_voltage':
                    if value is not None:
                        success = instrument.set_voltage(1, float(value))
                        message = "電壓設定成功" if success else f"電壓設定失敗: 超出儀器限制 ({value}V)"
                    else:
                        return {"success": False, "message": "設定電壓需要提供數值"}
                elif action == 'set_current':
                    if value is not None:
                        success = instrument.set_current(1, float(value))
                        message = "電流設定成功" if success else f"電流設定失敗: 超出儀器限制 ({value}A)"
                    else:
                        return {"success": False, "message": "設定電流需要提供數值"}
                elif action == 'on':
                    success, message = instrument.turn_on()
                elif action == 'off':
                    success, message = instrument.turn_off()
                else:
                    return {"success": False, "message": f"不支持的電源供應器動作: {action}"}
                
                return {
                    "success": success,
                    "message": message,
                    "address": address,
                    "action": action.upper()
                }
            finally:
                instrument.disconnect()

        elif instrument_type == 'eload':
            success, message = control_eload_instrument(address, action, value)
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
    import argparse
    
    # 創建參數解析器
    parser = argparse.ArgumentParser(description="GPIB儀器控制客戶端")
    
    # 添加 --host 參數
    parser.add_argument(
        "--host",
        type=str,
        default=CLIENT_CONFIG["server_host"],
        help=f"服務器地址 (預設: {CLIENT_CONFIG['server_host']})"
    )
    
    # 更新配置
    args = parser.parse_args()
    CLIENT_CONFIG["server_host"] = args.host

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