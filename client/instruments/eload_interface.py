from abc import ABC, abstractmethod
import pyvisa
from typing import Dict

class LoadInterface(ABC):
    """電子負載機的抽象基類"""
    
    def __init__(self, resource_manager: pyvisa.ResourceManager, address: str):
        self.rm = resource_manager
        self.address = address
        self.instrument = None
    
    def connect(self):
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
    def turn_on(self) -> tuple[bool, str]:
        """開啟負載"""
        pass
    
    @abstractmethod
    def turn_off(self) -> tuple[bool, str]:
        """關閉負載"""
        pass
    
    @abstractmethod
    def get_identification(self) -> str:
        """取得儀器識別訊息"""
        pass
    
    @abstractmethod
    def set_mode(self, mode: str):
        """設定工作模式 (CC/CV/CR/CP)"""
        pass
    
    @abstractmethod
    def set_current(self, current: float):
        """設定電流值 (CC模式)"""
        pass
    
    @abstractmethod
    def set_voltage(self, voltage: float):
        """設定電壓值 (CV模式)"""
        pass
    
    @abstractmethod
    def measure_voltage(self) -> float:
        """測量電壓"""
        pass
    
    @abstractmethod
    def measure_current(self) -> float:
        """測量電流"""
        pass

    @abstractmethod
    def get_status(self) -> Dict:
        """獲取儀器即時狀態

        Returns:
            Dict: e.g., {'output': 'ON', 'current': 1.2}
        """
        pass