from typing import Dict, Optional, Tuple
import time
import pyvisa
from .power_supply_interface import DCSourceInterface, OutputTrackingMode

class Chroma62012P(DCSourceInterface):
    """Chroma 62012P DC電源供應器實現"""

    def __init__(self, resource_manager: pyvisa.ResourceManager, address: str):
        super().__init__(resource_manager, address)
        self.max_voltage = 120.0  # 預設最大電壓
        self.max_current = 50.0   # 預設最大電流
        self._identify_model()    # 識別具體型號並設置限制

    def _identify_model(self):
        """根據儀器型號識別具體規格並設置限制"""
        try:
            idn = self.get_identification()
            if idn:
                # 解析型號，例如 "CHROMA,62012P-100-50,..."
                parts = idn.split(',')
                if len(parts) >= 2:
                    model_part = parts[1].strip()
                    if '62012P' in model_part:
                        # 解析型號規格，例如 62012P-100-50
                        model_specs = model_part.split('-')
                        if len(model_specs) >= 3:
                            try:
                                voltage_spec = float(model_specs[1])  # 100V
                                current_spec = float(model_specs[2])  # 50A
                                self.max_voltage = voltage_spec
                                self.max_current = current_spec
                                print(f"識別到 Chroma 62012P 型號: {model_part}, 限制: {self.max_voltage}V, {self.max_current}A")
                            except (ValueError, IndexError):
                                print(f"無法解析型號規格: {model_part}，使用預設值")
                        else:
                            print(f"型號格式不正確: {model_part}，使用預設值")
                    else:
                        print(f"非預期的型號: {model_part}，使用預設值")
            else:
                print("無法獲取儀器識別信息，使用預設值")
        except Exception as e:
            print(f"型號識別失敗: {e}，使用預設值")

    def get_identification(self) -> str:
        try:
            return self.instrument.query('*IDN?').strip()
        except Exception:
            return ""

    def set_voltage(self, channel: int, voltage: float) -> bool:
        try:
            # 檢查電壓是否超過限制
            if voltage > self.max_voltage:
                print(f"電壓設定 {voltage}V 超過儀器限制 {self.max_voltage}V")
                return False
            if voltage < 0:
                print(f"電壓設定 {voltage}V 無效，必須大於等於 0V")
                return False

            # 使用 SCPI 命令設定電壓，例如 SOUR:VOLT 80.00
            self.instrument.write(f'SOUR:VOLT {voltage}')
            return True
        except Exception as e:
            print(f"設定電壓失敗: {e}")
            return False

    def set_current(self, channel: int, current: float) -> bool:
        try:
            # 檢查電流是否超過限制
            if current > self.max_current:
                print(f"電流設定 {current}A 超過儀器限制 {self.max_current}A")
                return False
            if current < 0:
                print(f"電流設定 {current}A 無效，必須大於等於 0A")
                return False

            self.instrument.write(f'SOUR:CURR {current}')
            return True
        except Exception as e:
            print(f"設定電流失敗: {e}")
            return False

    def get_voltage_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query('SOUR:VOLT?'))
        except Exception:
            return float('nan')

    def get_current_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query('SOUR:CURR?'))
        except Exception:
            return float('nan')

    def measure_voltage(self, channel: int) -> float:
        try:
            return float(self.instrument.query('MEAS:VOLT?'))
        except Exception:
            return float('nan')

    def measure_current(self, channel: int) -> float:
        try:
            return float(self.instrument.query('MEAS:CURR?'))
        except Exception:
            return float('nan')

    def turn_on(self, channel: Optional[int] = None) -> tuple[bool, str]:
        try:
            # Chroma 62012P 可能需要 OUTP:STAT ON 格式
            self.instrument.write('CONFigure:OUTPut ON')
            time.sleep(0.1)
            return True, "輸出開啟成功"
        except Exception as e:
            return False, f"輸出開啟失敗: {str(e)}"

    def turn_off(self, channel: Optional[int] = None) -> tuple[bool, str]:
        try:
            # Chroma 62012P 可能需要 OUTP:STAT OFF 格式
            self.instrument.write('CONFigure:OUTPut OFF')
            time.sleep(0.1)
            return True, "輸出關閉成功"
        except Exception as e:
            return False, f"輸出關閉失敗: {str(e)}"

    def get_output_state(self, channel: int) -> bool:
        try:
            return int(self.instrument.query('OUTP:STAT?')) == 1
        except Exception:
            return False

    def set_ovp(self, channel: int, voltage: float) -> bool:
        try:
            self.instrument.write(f'SOUR:VOLT:PROT {voltage}')
            return True
        except Exception as e:
            print(f"設定OVP失敗: {e}")
            return False

    def set_ocp(self, channel: int, current: float) -> bool:
        try:
            self.instrument.write(f'SOUR:CURR:PROT {current}')
            return True
        except Exception as e:
            print(f"設定OCP失敗: {e}")
            return False

    def get_ovp_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query('SOUR:VOLT:PROT?'))
        except Exception:
            return float('nan')

    def get_ocp_setting(self, channel: int) -> float:
        try:
            return float(self.instrument.query('SOUR:CURR:PROT?'))
        except Exception:
            return float('nan')

    def clear_protection(self, channel: Optional[int] = None) -> bool:
        try:
            self.instrument.write('OUTP:PROT:CLE')
            return True
        except Exception as e:
            print(f"清除保護狀態失敗: {e}")
            return False

    def get_protection_status(self, channel: int) -> Dict[str, bool]:
        try:
            status = int(self.instrument.query('STAT:QUES:COND?'))
            return {
                'OVP': bool(status & 0x01),
                'OCP': bool(status & 0x02),
                'OTP': bool(status & 0x04)
            }
        except Exception:
            return {'OVP': False, 'OCP': False, 'OTP': False}

    def set_output_tracking(self, mode: OutputTrackingMode) -> bool:
        # Chroma 62012P 可能不支持追蹤模式，根據手冊確認
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
            self.instrument.write(f'SOUR:VOLT:SLEW {rate}')
            return True
        except Exception as e:
            print(f"設定電壓變化速率失敗: {e}")
            return False

    def set_current_slew_rate(self, channel: int, rate: float) -> bool:
        try:
            self.instrument.write(f'SOUR:CURR:SLEW {rate}')
            return True
        except Exception as e:
            print(f"設定電流變化速率失敗: {e}")
            return False

    def get_channel_count(self) -> int:
        # Chroma 62012P 是單通道電源供應器
        return 1

    def get_voltage_range(self, channel: int) -> Tuple[float, float]:
        try:
            # 返回基於識別到的型號的電壓範圍
            return (0.0, self.max_voltage)
        except Exception:
            return (0.0, 0.0)

    def get_current_range(self, channel: int) -> Tuple[float, float]:
        try:
            # 返回基於識別到的型號的電流範圍
            return (0.0, self.max_current)
        except Exception:
            return (0.0, 0.0)

    def get_status(self) -> Dict:
        """獲取儀器即時狀態"""
        try:
            output_state = self.get_output_state(1)
            voltage = self.measure_voltage(1)
            current = self.measure_current(1)
            voltage_setting = self.get_voltage_setting(1)
            current_setting = self.get_current_setting(1)
            
            return {
                'output': 'ON' if output_state else 'OFF',
                'voltage': voltage,
                'current': current,
                'voltage_setting': voltage_setting,
                'current_setting': current_setting
            }
        except Exception:
            return {
                'output': 'UNKNOWN',
                'voltage': float('nan'),
                'current': float('nan'),
                'voltage_setting': float('nan'),
                'current_setting': float('nan')
            }