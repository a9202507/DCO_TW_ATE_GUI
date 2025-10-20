from typing import Optional, Type
import pyvisa
from .electronic_load_interface import LoadInterface
from .chroma_63206a_electronic_load import Chroma63206A

class LoadFactory:
    """電子負載機工廠類"""
    
    # 註冊支援的負載機型號
    _models = {
        "Chroma,63206A": Chroma63206A,
        # 之後可以在這裡添加更多型號
        # "ITECH,IT8811": ITech8811,
        # "BK,8600": BK8600,
    }
    
    @classmethod
    def create_load(cls, resource_manager: pyvisa.ResourceManager, address: str) -> Optional[LoadInterface]:
        """
        根據儀器識別創建對應的負載機實例
        
        Args:
            resource_manager: VISA資源管理器
            address: 儀器地址
        
        Returns:
            LoadInterface: 負載機實例，如果不支援該型號則返回None
        """
        try:
            # 先建立臨時連接獲取儀器識別
            temp_inst = resource_manager.open_resource(address)
            idn = temp_inst.query('*IDN?').strip()
            temp_inst.close()
            
            # 尋找對應的負載機類別
            for model_id, load_class in cls._models.items():
                if model_id in idn:
                    return load_class(resource_manager, address)
            
            return None
        except Exception as e:
            print(f"建立負載機實例失敗: {e}")
            return None
    
    @classmethod
    def register_model(cls, model_id: str, load_class: Type[LoadInterface]):
        """
        註冊新的負載機型號
        
        Args:
            model_id: 儀器識別字串中的關鍵字
            load_class: 負載機類別
        """
        cls._models[model_id] = load_class
