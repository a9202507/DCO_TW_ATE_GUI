from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional
import pyvisa

class AFGInterface(ABC):
    """訊號產生器的抽象基類"""
    
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
    def set_frequency(self, channel: int, frequency: float) -> bool:
        """設定指定通道的頻率
        
        Args:
            channel: 通道編號
            frequency: 頻率值 (Hz)
        """
        pass

    @abstractmethod
    def output_on(self, channel: int) -> bool:
        """開啟指定通道的輸出
        
        Args:
            channel: 通道編號
        """
        pass

    @abstractmethod
    def output_off(self, channel: int) -> bool:
        """關閉指定通道的輸出
        
        Args:
            channel: 通道編號
        """
        pass