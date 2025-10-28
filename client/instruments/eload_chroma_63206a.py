from .eload_interface import LoadInterface
import time

class Chroma63206A(LoadInterface):
    """Chroma 63206A 電子負載機實現"""
    
    def turn_on(self) -> tuple[bool, str]:
        try:
            self.instrument.write('LOAD ON')
            time.sleep(0.5)
            return True, "負載開啟成功"
        except Exception as e:
            return False, f"負載開啟失敗: {str(e)}"
    
    def turn_off(self) -> tuple[bool, str]:
        try:
            self.instrument.write('LOAD OFF')
            time.sleep(0.5)
            return True, "負載關閉成功"
        except Exception as e:
            return False, f"負載關閉失敗: {str(e)}"
    
    def get_identification(self) -> str:
        try:
            return self.instrument.query('*IDN?').strip()
        except Exception:
            return ""
    
    def set_mode(self, mode: str):
        """設定工作模式
        mode: 'CC', 'CV', 'CR', 或 'CP'
        """
        mode_map = {
            'CC': 'CURR',
            'CV': 'VOLT',
            'CR': 'RES',
            'CP': 'POW'
        }
        if mode.upper() in mode_map:
            self.instrument.write(f'MODE {mode_map[mode.upper()]}')
    
    def set_current(self, current: float):
        self.instrument.write(f'CURR:STAT:L1 {current}')
    
    def set_voltage(self, voltage: float):
        self.instrument.write(f'VOLT:STAT:L1 {voltage}')
    
    def measure_voltage(self) -> float:
        return float(self.instrument.query('MEAS:VOLT?'))
    
    def measure_current(self) -> float:
        return float(self.instrument.query('MEAS:CURR?'))

    def measure_power(self) -> float:
        return float(self.instrument.query('FETC:POW?'))

    def get_mode(self) -> str:
        mode = self.instrument.query('MODE?').strip()
        mode_map = {
            'CURR': 'CC',
            'VOLT': 'CV',
            'RES': 'CR',
            'POW': 'CP'
        }
        return mode_map.get(mode, 'UNKNOWN')

    def get_status(self) -> dict:
        try:
            output_str = self.instrument.query('LOAD?').strip()
            output = 'ON' if output_str == '1' else 'OFF'
            current = self.measure_current()
            voltage = self.measure_voltage()
            power = self.measure_power()
            mode = self.get_mode()
            return {
                'output': output,
                'current': current,
                'voltage': voltage,
                'power': power,
                'mode': mode,
            }
        except Exception:
            return {
                'output': 'UNKNOWN',
                'current': 0,
                'voltage': 0,
                'power': 0,
                'mode': 'UNKNOWN',
            }
