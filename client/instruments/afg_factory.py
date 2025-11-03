from typing import Optional, Type
import pyvisa
from .afg_interface import AFGInterface
from .afg_tektronix_3101c import AFGTektronix3101C

class AFGFactory:
    """訊號產生器工廠類"""
    
    _models = {
        "TEKTRONIX,AFG3101C": AFGTektronix3101C,
    }
    
    @classmethod
    def create_afg(cls, resource_manager: pyvisa.ResourceManager, address: str) -> Optional[AFGInterface]:
        """
        根據儀器識別創建對應的訊號產生器實例
        
        Args:
            resource_manager: VISA資源管理器
            address: 儀器地址
        
        Returns:
            AFGInterface: 訊號產生器實例，如果不支援該型號則返回None
        """
        try:
            temp_inst = resource_manager.open_resource(address)
            idn = temp_inst.query('*IDN?').strip()
            temp_inst.close()
            
            for model_id, afg_class in cls._models.items():
                if model_id in idn:
                    return afg_class(resource_manager, address)
            
            return None
        except Exception as e:
            print(f"建立訊號產生器實例失敗: {e}")
            return None
    
    @classmethod
    def register_model(cls, model_id: str, afg_class: Type[AFGInterface]):
        """
        註冊新的訊號產生器型號
        
        Args:
            model_id: 儀器識別字串中的關鍵字
            afg_class: 訊號產生器類別
        """
        cls._models[model_id] = afg_class