from typing import List, Dict, Union, Optional
import time
from .daq_interface import DAQInterface

class HP34970A(DAQInterface):
    """HP/Agilent 34970A 數據擷取器實現"""
    
    def get_identification(self) -> str:
        try:
            return self.instrument.query('*IDN?').strip()
        except Exception:
            return ""
    
    def configure_channel(self, channel: Union[int, str], function: str, 
                         range: Optional[float] = None, 
                         resolution: Optional[float] = None) -> bool:
        try:
            # 構建命令
            cmd = f'CONF:{function} '
            
            # 添加範圍和解析度（如果提供）
            if range is not None:
                cmd += f'{range}'
                if resolution is not None:
                    cmd += f',{resolution}'
            
            # 在通道前添加掃描卡插槽號（假設格式為 '101'）
            if isinstance(channel, int):
                channel = f'{((channel-1)//100 + 1)}{"0"}{((channel-1)%100 + 1):02d}'
            
            cmd += f'(@{channel})'
            self.instrument.write(cmd)
            return True
        except Exception as e:
            print(f"配置通道失敗: {e}")
            return False
    
    def scan_channels(self, channel_list: List[Union[int, str]]) -> bool:
        try:
            # 轉換通道格式（如果需要）
            formatted_channels = []
            for ch in channel_list:
                if isinstance(ch, int):
                    formatted_ch = f'{((ch-1)//100 + 1)}{"0"}{((ch-1)%100 + 1):02d}'
                    formatted_channels.append(formatted_ch)
                else:
                    formatted_channels.append(ch)
            
            # 設定掃描列表
            channel_str = ','.join(formatted_channels)
            self.instrument.write(f'ROUTE:SCAN (@{channel_str})')
            return True
        except Exception as e:
            print(f"設定掃描通道失敗: {e}")
            return False
    
    def start_scan(self) -> bool:
        try:
            self.instrument.write('INIT')
            return True
        except Exception as e:
            print(f"開始掃描失敗: {e}")
            return False
    
    def stop_scan(self) -> bool:
        try:
            self.instrument.write('ABOR')
            return True
        except Exception as e:
            print(f"停止掃描失敗: {e}")
            return False
    
    def read_channel(self, channel: Union[int, str]) -> float:
        try:
            # 格式化通道號
            if isinstance(channel, int):
                channel = f'{((channel-1)//100 + 1)}{"0"}{((channel-1)%100 + 1):02d}'
            
            # 讀取指定通道
            result = self.instrument.query(f'MEAS? (@{channel})')
            return float(result.strip())
        except Exception as e:
            print(f"讀取通道失敗: {e}")
            return float('nan')
    
    def read_all_channels(self) -> Dict[Union[int, str], float]:
        try:
            # 觸發一次掃描
            self.start_scan()
            # 等待掃描完成
            self.instrument.query('*OPC?')
            
            # 讀取所有數據
            data = self.instrument.query('FETCH?').split(',')
            
            # 獲取當前掃描列表
            scan_list = self.instrument.query('ROUTE:SCAN?')
            channels = scan_list.strip('(@)').split(',')
            
            # 將數據與通道對應
            result = {}
            for ch, val in zip(channels, data):
                result[ch] = float(val)
            return result
        except Exception as e:
            print(f"讀取所有通道失敗: {e}")
            return {}
    
    def get_alarm_status(self, channel: Union[int, str]) -> Dict[str, bool]:
        try:
            if isinstance(channel, int):
                channel = f'{((channel-1)//100 + 1)}{"0"}{((channel-1)%100 + 1):02d}'
            
            status = self.instrument.query(f'STAT:ALARM:EVEN? (@{channel})')
            status = int(status)
            
            return {
                'high': bool(status & 0x01),  # 高警報
                'low': bool(status & 0x02),   # 低警報
            }
        except Exception as e:
            print(f"獲取警報狀態失敗: {e}")
            return {'high': False, 'low': False}
    
    def set_alarm(self, channel: Union[int, str], 
                 high_limit: Optional[float] = None, 
                 low_limit: Optional[float] = None) -> bool:
        try:
            if isinstance(channel, int):
                channel = f'{((channel-1)//100 + 1)}{"0"}{((channel-1)%100 + 1):02d}'
            
            if high_limit is not None:
                self.instrument.write(f'CALC:LIM:UPP {high_limit},(@{channel})')
                self.instrument.write(f'CALC:LIM:UPP:STAT ON,(@{channel})')
            
            if low_limit is not None:
                self.instrument.write(f'CALC:LIM:LOW {low_limit},(@{channel})')
                self.instrument.write(f'CALC:LIM:LOW:STAT ON,(@{channel})')
            
            return True
        except Exception as e:
            print(f"設定警報失敗: {e}")
            return False
