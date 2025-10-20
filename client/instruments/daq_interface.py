from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional
import pyvisa

class DAQInterface(ABC):
    """數據擷取器的抽象基類"""
    
    def __init__(self, resource_manager: pyvisa.ResourceManager, address: str):
        self.rm = resource_manager
        self.address = address
        self.instrument = None
    
    def connect(self) -> bool:
        """連接到儀器"""
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.timeout = 10000  # 10秒超時
            return True
        except Exception as e:
            print(f"連接失敗: {e}")
            return False
    
    def disconnect(self):
        """斷開儀器連接"""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
    
    @abstractmethod
    def get_identification(self) -> str:
        """取得儀器識別訊息"""
        pass
    
    @abstractmethod
    def configure_channel(self, channel: Union[int, str], function: str, range: Optional[float] = None, 
                         resolution: Optional[float] = None) -> bool:
        """設定通道配置
        
        Args:
            channel: 通道編號或名稱
            function: 測量功能 (如 'VOLT:DC', 'CURR:DC', 'RES', 'TEMP', etc.)
            range: 測量範圍 (可選)
            resolution: 解析度 (可選)
        """
        pass
    
    @abstractmethod
    def scan_channels(self, channel_list: List[Union[int, str]]) -> bool:
        """設定掃描通道列表"""
        pass
    
    @abstractmethod
    def start_scan(self) -> bool:
        """開始掃描"""
        pass
    
    @abstractmethod
    def stop_scan(self) -> bool:
        """停止掃描"""
        pass
    
    @abstractmethod
    def read_channel(self, channel: Union[int, str]) -> float:
        """讀取單一通道的值"""
        pass
    
    @abstractmethod
    def read_all_channels(self) -> Dict[Union[int, str], float]:
        """讀取所有設定的通道值"""
        pass
    
    @abstractmethod
    def get_alarm_status(self, channel: Union[int, str]) -> Dict[str, bool]:
        """獲取通道警報狀態"""
        pass
    
    @abstractmethod
    def set_alarm(self, channel: Union[int, str], 
                 high_limit: Optional[float] = None, 
                 low_limit: Optional[float] = None) -> bool:
        """設定通道警報限制"""
        pass
