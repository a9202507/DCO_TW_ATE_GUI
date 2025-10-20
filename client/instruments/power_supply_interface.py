from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional, Tuple
import pyvisa
from enum import Enum

class OutputTrackingMode(Enum):
    """輸出追蹤模式"""
    INDEPENDENT = "INDEPENDENT"  # 獨立模式
    PARALLEL = "PARALLEL"      # 並聯模式
    SERIES = "SERIES"         # 串聯模式
    TRACKING = "TRACKING"      # 追蹤模式

class DCSourceInterface(ABC):
    """DC電源供應器的抽象基類"""
    
    def __init__(self, resource_manager: pyvisa.ResourceManager, address: str):
        self.rm = resource_manager
        self.address = address
        self.instrument = None
    
    def connect(self) -> bool:
        """連接到電源供應器"""
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.timeout = 10000  # 10秒超時
            return True
        except Exception as e:
            print(f"連接失敗: {e}")
            return False
    
    def disconnect(self):
        """斷開電源供應器連接"""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
    
    @abstractmethod
    def get_identification(self) -> str:
        """取得儀器識別訊息"""
        pass
    
    @abstractmethod
    def set_voltage(self, channel: int, voltage: float) -> bool:
        """設定輸出電壓
        
        Args:
            channel: 通道編號
            voltage: 電壓值 (V)
        """
        pass
    
    @abstractmethod
    def set_current(self, channel: int, current: float) -> bool:
        """設定電流限制
        
        Args:
            channel: 通道編號
            current: 電流值 (A)
        """
        pass
    
    @abstractmethod
    def get_voltage_setting(self, channel: int) -> float:
        """讀取電壓設定值"""
        pass
    
    @abstractmethod
    def get_current_setting(self, channel: int) -> float:
        """讀取電流設定值"""
        pass
    
    @abstractmethod
    def measure_voltage(self, channel: int) -> float:
        """測量實際輸出電壓"""
        pass
    
    @abstractmethod
    def measure_current(self, channel: int) -> float:
        """測量實際輸出電流"""
        pass
    
    @abstractmethod
    def turn_on(self, channel: Optional[int] = None) -> tuple[bool, str]:
        """開啟輸出
        
        Args:
            channel: 特定通道編號，若為None則開啟所有通道
        """
        pass
    
    @abstractmethod
    def turn_off(self, channel: Optional[int] = None) -> tuple[bool, str]:
        """關閉輸出
        
        Args:
            channel: 特定通道編號，若為None則關閉所有通道
        """
        pass
    
    @abstractmethod
    def get_output_state(self, channel: int) -> bool:
        """獲取通道輸出狀態"""
        pass
    
    @abstractmethod
    def set_ovp(self, channel: int, voltage: float) -> bool:
        """設定過電壓保護值"""
        pass
    
    @abstractmethod
    def set_ocp(self, channel: int, current: float) -> bool:
        """設定過電流保護值"""
        pass
    
    @abstractmethod
    def get_ovp_setting(self, channel: int) -> float:
        """獲取過電壓保護設定值"""
        pass
    
    @abstractmethod
    def get_ocp_setting(self, channel: int) -> float:
        """獲取過電流保護設定值"""
        pass
    
    @abstractmethod
    def clear_protection(self, channel: Optional[int] = None) -> bool:
        """清除保護狀態"""
        pass
    
    @abstractmethod
    def get_protection_status(self, channel: int) -> Dict[str, bool]:
        """獲取保護狀態
        
        Returns:
            Dict with keys: 'OVP', 'OCP', 'OTP' (過溫保護)
        """
        pass
    
    @abstractmethod
    def set_output_tracking(self, mode: OutputTrackingMode) -> bool:
        """設定輸出追蹤模式 (僅適用於多通道電源供應器)"""
        pass
    
    @abstractmethod
    def set_voltage_slew_rate(self, channel: int, rate: float) -> bool:
        """設定電壓變化速率 (V/s)"""
        pass
    
    @abstractmethod
    def set_current_slew_rate(self, channel: int, rate: float) -> bool:
        """設定電流變化速率 (A/s)"""
        pass
    
    @abstractmethod
    def get_channel_count(self) -> int:
        """獲取通道數量"""
        pass
    
    @abstractmethod
    def get_voltage_range(self, channel: int) -> Tuple[float, float]:
        """獲取通道電壓範圍
        
        Returns:
            Tuple[float, float]: (最小值, 最大值)
        """
        pass
    
    @abstractmethod
    def get_current_range(self, channel: int) -> Tuple[float, float]:
        """獲取通道電流範圍
        
        Returns:
            Tuple[float, float]: (最小值, 最大值)
        """
        pass
