from .afg_interface import AFGInterface

class TektronixAFG3101C(AFGInterface):
    """Tektronix AFG3101C 實作"""
    def __init__(self, resource):
        self.resource = resource
        self.connected = False

    def connect(self):
        # 實際連接儀器的程式碼
        self.connected = True

    def disconnect(self):
        self.connected = False

    def set_waveform(self, waveform_type: str, frequency: float, amplitude: float):
        # 設定波形、頻率、振幅的程式碼
        pass

    def output_on(self):
        # 開啟輸出
        pass

    def output_off(self):
        # 關閉輸出
        pass
