from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional, Tuple
import pyvisa
from enum import Enum

class TriggerMode(Enum):
    AUTO = "AUTO"
    NORMAL = "NORM"
    SINGLE = "SINGLE"

class TriggerSlope(Enum):
    RISING = "RISE"
    FALLING = "FALL"
    EITHER = "EITHER"

class AcquisitionMode(Enum):
    SAMPLE = "SAMPLE"
    PEAK_DETECT = "PEAK"
    AVERAGING = "AVERAGE"
    HIGH_RES = "HIRES"

class OscilloscopeInterface(ABC):
    """示波器的抽象基類"""
    
    def __init__(self, resource_manager: pyvisa.ResourceManager, address: str):
        self.rm = resource_manager
        self.address = address
        self.instrument = None
    
    def connect(self) -> bool:
        """連接到示波器"""
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.timeout = 10000  # 10秒超時
            return True
        except Exception as e:
            print(f"連接失敗: {e}")
            return False
    
    def disconnect(self):
        """斷開示波器連接"""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
    
    @abstractmethod
    def get_identification(self) -> str:
        """取得儀器識別訊息"""
        pass
    
    @abstractmethod
    def auto_setup(self) -> bool:
        """執行自動設定"""
        pass
    
    @abstractmethod
    def set_channel_state(self, channel: int, state: bool) -> bool:
        """設定通道開關狀態"""
        pass
    
    @abstractmethod
    def set_channel_scale(self, channel: int, scale: float) -> bool:
        """設定通道垂直刻度 (V/div)"""
        pass
    
    @abstractmethod
    def set_channel_offset(self, channel: int, offset: float) -> bool:
        """設定通道垂直偏移 (V)"""
        pass
    
    @abstractmethod
    def set_channel_coupling(self, channel: int, coupling: str) -> bool:
        """設定通道耦合方式 (DC/AC/GND)"""
        pass
    
    @abstractmethod
    def set_timebase_scale(self, scale: float) -> bool:
        """設定時基 (s/div)"""
        pass
    
    @abstractmethod
    def set_timebase_position(self, position: float) -> bool:
        """設定時基位置 (s)"""
        pass
    
    @abstractmethod
    def set_trigger_source(self, source: Union[int, str]) -> bool:
        """設定觸發源"""
        pass
    
    @abstractmethod
    def set_trigger_mode(self, mode: TriggerMode) -> bool:
        """設定觸發模式"""
        pass
    
    @abstractmethod
    def set_trigger_level(self, level: float) -> bool:
        """設定觸發電平 (V)"""
        pass
    
    @abstractmethod
    def set_trigger_slope(self, slope: TriggerSlope) -> bool:
        """設定觸發斜率"""
        pass
    
    @abstractmethod
    def set_acquisition_mode(self, mode: AcquisitionMode, averages: Optional[int] = None) -> bool:
        """設定擷取模式"""
        pass
    
    @abstractmethod
    def start_acquisition(self) -> bool:
        """開始擷取"""
        pass
    
    @abstractmethod
    def stop_acquisition(self) -> bool:
        """停止擷取"""
        pass
    
    @abstractmethod
    def single_acquisition(self) -> bool:
        """單次擷取"""
        pass
    
    @abstractmethod
    def is_triggered(self) -> bool:
        """檢查是否已觸發"""
        pass
    
    @abstractmethod
    def get_waveform_data(self, channel: int) -> Tuple[List[float], List[float]]:
        """獲取波形數據
        
        Returns:
            Tuple[List[float], List[float]]: (時間數據, 電壓數據)
        """
        pass
    
    @abstractmethod
    def get_measurement(self, channel: int, measurement_type: str) -> float:
        """獲取測量值 (Vpp, Frequency, Period等)"""
        pass
    
    @abstractmethod
    def save_waveform(self, filepath: str, channels: List[int]) -> bool:
        """保存波形數據到文件"""
        pass
    
    @abstractmethod
    def save_screenshot(self, filepath: str) -> bool:
        """保存螢幕截圖"""
        pass
    
    @abstractmethod
    def set_math_function(self, expression: str) -> bool:
        """設定數學運算"""
        pass
    
    @abstractmethod
    def clear_display(self) -> bool:
        """清除顯示"""
        pass
