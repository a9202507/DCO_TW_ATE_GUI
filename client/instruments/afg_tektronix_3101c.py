from .afg_interface import AFGInterface
import pyvisa

class AFGTektronix3101C(AFGInterface):
    """Tektronix AFG3101C 訊號產生器的具體實現"""

    def get_identification(self) -> str:
        """取得儀器識別訊息"""
        try:
            return self.instrument.query('*IDN?')
        except pyvisa.errors.VisaIOError as e:
            print(f"取得儀器識別訊息失敗: {e}")
            return ""

    def set_frequency(self, channel: int, frequency: float) -> bool:
        """設定指定通道的頻率"""
        try:
            self.instrument.write(f'SOURce{channel}:FREQuency:FIXed {frequency}')
            return True
        except pyvisa.errors.VisaIOError as e:
            print(f"設定頻率失敗: {e}")
            return False

    def output_on(self, channel: int) -> bool:
        """開啟指定通道的輸出"""
        try:
            self.instrument.write(f'OUTPut{channel}:STATe ON')
            return True
        except pyvisa.errors.VisaIOError as e:
            print(f"開啟輸出失敗: {e}")
            return False

    def output_off(self, channel: int) -> bool:
        """關閉指定通道的輸出"""
        try:
            self.instrument.write(f'OUTPut{channel}:STATe OFF')
            return True
        except pyvisa.errors.VisaIOError as e:
            print(f"關閉輸出失敗: {e}")
            return False