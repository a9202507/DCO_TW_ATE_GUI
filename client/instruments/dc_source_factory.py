from typing import Optional, Type
import pyvisa
from .dc_source_interface import DCSourceInterface

class DCSourceFactory:
    """DC電源供應器工廠類"""
    
    # 註冊支援的電源供應器型號
    _models = {
        # 後續可以添加更多型號
        # "Chroma,62012P": Chroma62012P,
        # "Chroma,62024P": Chroma62024P,
        # "HP,E3631A": HPE3631A,
        # "HP,6632B": HP6632B,
    }
    
    @classmethod
    def create_dc_source(cls, resource_manager: pyvisa.ResourceManager, address: str) -> Optional[DCSourceInterface]:
        """
        根據儀器識別創建對應的電源供應器實例
        
        Args:
            resource_manager: VISA資源管理器
            address: 儀器地址
        
        Returns:
            DCSourceInterface: 電源供應器實例，如果不支援該型號則返回None
        """
        try:
            # 先建立臨時連接獲取儀器識別
            temp_inst = resource_manager.open_resource(address)
            idn = temp_inst.query('*IDN?').strip()
            temp_inst.close()
            
            # 尋找對應的電源供應器類別
            for model_id, source_class in cls._models.items():
                if model_id in idn:
                    return source_class(resource_manager, address)
            
            return None
        except Exception as e:
            print(f"建立電源供應器實例失敗: {e}")
            return None
    
    @classmethod
    def register_model(cls, model_id: str, source_class: Type[DCSourceInterface]):
        """
        註冊新的電源供應器型號
        
        Args:
            model_id: 儀器識別字串中的關鍵字
            source_class: 電源供應器類別
        """
        cls._models[model_id] = source_class
