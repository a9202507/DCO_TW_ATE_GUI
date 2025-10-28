from typing import Optional, Type
import pyvisa
from .daq_interface import DAQInterface
from .daq_hp_34970a import HP34970A

class DAQFactory:
    """數據擷取器工廠類"""
    
    # 註冊支援的數據擷取器型號
    _models = {
        "HP34970A": HP34970A,
        "Agilent34970A": HP34970A,  # Agilent 版本使用相同的驅動
        "HEWLETT-PACKARD,34970A": HP34970A, # 原始 HP 版本
        # 之後可以在這裡添加更多型號
        # "Keysight34972A": Keysight34972A,
        # "Keithley7700": Keithley7700,
    }
    
    @classmethod
    def create_daq(cls, resource_manager: pyvisa.ResourceManager, address: str) -> Optional[DAQInterface]:
        """
        根據儀器識別創建對應的數據擷取器實例
        
        Args:
            resource_manager: VISA資源管理器
            address: 儀器地址
        
        Returns:
            DAQInterface: 數據擷取器實例，如果不支援該型號則返回None
        """
        try:
            # 先建立臨時連接獲取儀器識別
            temp_inst = resource_manager.open_resource(address)
            idn = temp_inst.query('*IDN?').strip()
            temp_inst.close()
            
            # 尋找對應的數據擷取器類別
            for model_id, daq_class in cls._models.items():
                if model_id in idn:
                    return daq_class(resource_manager, address)
            
            return None
        except Exception as e:
            print(f"建立數據擷取器實例失敗: {e}")
            return None
    
    @classmethod
    def register_model(cls, model_id: str, daq_class: Type[DAQInterface]):
        """
        註冊新的數據擷取器型號
        
        Args:
            model_id: 儀器識別字串中的關鍵字
            daq_class: 數據擷取器類別
        """
        cls._models[model_id] = daq_class