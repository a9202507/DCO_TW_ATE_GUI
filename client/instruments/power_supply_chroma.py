from typing import Dict, Optional, Tuple
import time
from .power_supply_interface import DCSourceInterface, OutputTrackingMode

class ChromaDCSource(DCSourceInterface):
    """Chroma DC電源供應器基本實現"""
    
    def get_identification(self) -> str:
        try:
            return self.instrument.query('*IDN?').strip()
        except Exception:
            return ""
    
    def set_voltage(self, channel: int, voltage: float) -> bool:
        try:
            self.instrument.write(f'SOUR{channel}:VOLT {voltage}')
            return True
        except Exception as e:
            print(f"設定電壓失敗: {e}")
            return False
    
    def set_current(self, channel: int, current: float) -> bool:
        try:
            self.instrument.write(f'SOUR{channel}:CURR {current}')
            return True
        except Exception as e:
            print(f"設定電流失敗: {e}")
            return False
    
    def get_voltage_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query(f'SOUR{channel}:VOLT?'))
        except Exception:
            return float('nan')
    
    def get_current_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query(f'SOUR{channel}:CURR?'))
        except Exception:
            return float('nan')
    
    def measure_voltage(self, channel: int) -> float:
        try:
            return float(self.instrument.query(f'MEAS:VOLT? (@{channel})'))
        except Exception:
            return float('nan')
    
    def measure_current(self, channel: int) -> float:
        try:
            return float(self.instrument.query(f'MEAS:CURR? (@{channel})'))
        except Exception:
            return float('nan')
    
    def turn_on(self, channel: Optional[int] = None) -> tuple[bool, str]:
        try:
            if channel is None:
                self.instrument.write('OUTP:STAT ON,(@1:4)')
            else:
                self.instrument.write(f'OUTP:STAT ON,(@{channel})')
            time.sleep(0.1)
            return True, "輸出開啟成功"
        except Exception as e:
            return False, f"輸出開啟失敗: {str(e)}"
    
    def turn_off(self, channel: Optional[int] = None) -> tuple[bool, str]:
        try:
            if channel is None:
                self.instrument.write('OUTP:STAT OFF,(@1:4)')
            else:
                self.instrument.write(f'OUTP:STAT OFF,(@{channel})')
            time.sleep(0.1)
            return True, "輸出關閉成功"
        except Exception as e:
            return False, f"輸出關閉失敗: {str(e)}"
    
    def get_output_state(self, channel: int) -> bool:
        try:
            return int(self.instrument.query(f'OUTP:STAT? (@{channel})')) == 1
        except Exception:
            return False
    
    def set_ovp(self, channel: int, voltage: float) -> bool:
        try:
            self.instrument.write(f'SOUR{channel}:VOLT:PROT {voltage}')
            return True
        except Exception as e:
            print(f"設定OVP失敗: {e}")
            return False
    
    def set_ocp(self, channel: int, current: float) -> bool:
        try:
            self.instrument.write(f'SOUR{channel}:CURR:PROT {current}')
            return True
        except Exception as e:
            print(f"設定OCP失敗: {e}")
            return False
    
    def get_ovp_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query(f'SOUR{channel}:VOLT:PROT?'))
        except Exception:
            return float('nan')
    
    def get_ocp_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query(f'SOUR{channel}:CURR:PROT?'))
        except Exception:
            return float('nan')
    
    def clear_protection(self, channel: Optional[int] = None) -> bool:
        try:
            if channel is None:
                self.instrument.write('OUTP:PROT:CLE (@1:4)')
            else:
                self.instrument.write(f'OUTP:PROT:CLE (@{channel})')
            return True
        except Exception as e:
            print(f"清除保護狀態失敗: {e}")
            return False
    
    def get_protection_status(self, channel: int) -> Dict[str, bool]:
        try:
            status = int(self.instrument.query(f'STAT:QUES:COND? (@{channel})'))
            return {
                'OVP': bool(status & 0x01),
                'OCP': bool(status & 0x02),
                'OTP': bool(status & 0x04)
            }
        except Exception:
            return {'OVP': False, 'OCP': False, 'OTP': False}
    
    def set_output_tracking(self, mode: OutputTrackingMode) -> bool:
        try:
            mode_map = {
                OutputTrackingMode.INDEPENDENT: 'NONE',
                OutputTrackingMode.PARALLEL: 'PARA',
                OutputTrackingMode.SERIES: 'SER',
                OutputTrackingMode.TRACKING: 'TRAC'
            }
            self.instrument.write(f'OUTP:TRAC {mode_map[mode]}')
            return True
        except Exception as e:
            print(f"設定輸出追蹤模式失敗: {e}")
            return False
    
    def set_voltage_slew_rate(self, channel: int, rate: float) -> bool:
        try:
            self.instrument.write(f'SOUR{channel}:VOLT:SLEW {rate}')
            return True
        except Exception as e:
            print(f"設定電壓變化速率失敗: {e}")
            return False
    
    def set_current_slew_rate(self, channel: int, rate: float) -> bool:
        try:
            self.instrument.write(f'SOUR{channel}:CURR:SLEW {rate}')
            return True
        except Exception as e:
            print(f"設定電流變化速率失敗: {e}")
            return False
    
    def get_channel_count(self) -> int:
        try:
            # 這裡需要根據具體型號實現
            return 1
        except Exception:
            return 0
    
    def get_voltage_range(self, channel: int) -> Tuple[float, float]:
        try:
            min_v = float(self.instrument.query(f'SOUR{channel}:VOLT? MIN'))
            max_v = float(self.instrument.query(f'SOUR{channel}:VOLT? MAX'))
            return min_v, max_v
        except Exception:
            return (0.0, 0.0)
    
    def get_current_range(self, channel: int) -> Tuple[float, float]:
        try:
            min_i = float(self.instrument.query(f'SOUR{channel}:CURR? MIN'))
            max_i = float(self.instrument.query(f'SOUR{channel}:CURR? MAX'))
            return min_i, max_i
        except Exception:
            return (0.0, 0.0)
