from typing import Optional, Type
import pyvisa
from .oscilloscope_interface import OscilloscopeInterface
from .tektronix_mso54b import TektronixMSO54B

class OscilloscopeFactory:
    """示波器工廠類"""
    
    # 註冊支援的示波器型號
    _models = {
        "MSO54B": TektronixMSO54B,
        # 之後可以在這裡添加更多型號
        # "DSOX3024T": KeysightDSOX3024T,
        # "DPO7054C": TektronixDPO7054C,
    }
    
    @classmethod
    def create_oscilloscope(cls, resource_manager: pyvisa.ResourceManager, address: str) -> Optional[OscilloscopeInterface]:
        """
        根據儀器識別創建對應的示波器實例
        
        Args:
            resource_manager: VISA資源管理器
            address: 儀器地址
        
        Returns:
            OscilloscopeInterface: 示波器實例，如果不支援該型號則返回None
        """
        try:
            # 先建立臨時連接獲取儀器識別
            temp_inst = resource_manager.open_resource(address)
            idn = temp_inst.query('*IDN?').strip()
            temp_inst.close()
            
            # 尋找對應的示波器類別
            for model_id, scope_class in cls._models.items():
                if model_id in idn:
                    return scope_class(resource_manager, address)
            
            return None
        except Exception as e:
            print(f"建立示波器實例失敗: {e}")
            return None
    
    @classmethod
    def register_model(cls, model_id: str, scope_class: Type[OscilloscopeInterface]):
        """
        註冊新的示波器型號
        
        Args:
            model_id: 儀器識別字串中的關鍵字
            scope_class: 示波器類別
        """
        cls._models[model_id] = scope_class
