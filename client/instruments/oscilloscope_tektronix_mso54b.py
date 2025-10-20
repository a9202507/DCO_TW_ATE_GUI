from typing import List, Dict, Union, Optional, Tuple
import time
from .oscilloscope_interface import (
    OscilloscopeInterface,
    TriggerMode,
    TriggerSlope,
    AcquisitionMode
)

class TektronixMSO54B(OscilloscopeInterface):
    """Tektronix MSO54B 示波器實現"""
    
    def get_identification(self) -> str:
        try:
            return self.instrument.query('*IDN?').strip()
        except Exception:
            return ""
    
    def auto_setup(self) -> bool:
        try:
            self.instrument.write('AUTOSET EXECUTE')
            time.sleep(5)  # 等待自動設定完成
            return True
        except Exception as e:
            print(f"自動設定失敗: {e}")
            return False
    
    def set_channel_state(self, channel: int, state: bool) -> bool:
        try:
            self.instrument.write(f'CH{channel}:DISPLAY {1 if state else 0}')
            return True
        except Exception as e:
            print(f"設定通道狀態失敗: {e}")
            return False
    
    def set_channel_scale(self, channel: int, scale: float) -> bool:
        try:
            self.instrument.write(f'CH{channel}:SCALE {scale}')
            return True
        except Exception as e:
            print(f"設定通道刻度失敗: {e}")
            return False
    
    def set_channel_offset(self, channel: int, offset: float) -> bool:
        try:
            self.instrument.write(f'CH{channel}:OFFSET {offset}')
            return True
        except Exception as e:
            print(f"設定通道偏移失敗: {e}")
            return False
    
    def set_channel_coupling(self, channel: int, coupling: str) -> bool:
        try:
            self.instrument.write(f'CH{channel}:COUPLING {coupling}')
            return True
        except Exception as e:
            print(f"設定通道耦合失敗: {e}")
            return False
    
    def set_timebase_scale(self, scale: float) -> bool:
        try:
            self.instrument.write(f'HORIZONTAL:SCALE {scale}')
            return True
        except Exception as e:
            print(f"設定時基失敗: {e}")
            return False
    
    def set_timebase_position(self, position: float) -> bool:
        try:
            self.instrument.write(f'HORIZONTAL:POSITION {position}')
            return True
        except Exception as e:
            print(f"設定時基位置失敗: {e}")
            return False
    
    def set_trigger_source(self, source: Union[int, str]) -> bool:
        try:
            if isinstance(source, int):
                source = f'CH{source}'
            self.instrument.write(f'TRIGGER:A:EDGE:SOURCE {source}')
            return True
        except Exception as e:
            print(f"設定觸發源失敗: {e}")
            return False
    
    def set_trigger_mode(self, mode: TriggerMode) -> bool:
        try:
            self.instrument.write(f'TRIGGER:A:MODE {mode.value}')
            return True
        except Exception as e:
            print(f"設定觸發模式失敗: {e}")
            return False
    
    def set_trigger_level(self, level: float) -> bool:
        try:
            self.instrument.write(f'TRIGGER:A:LEVEL {level}')
            return True
        except Exception as e:
            print(f"設定觸發電平失敗: {e}")
            return False
    
    def set_trigger_slope(self, slope: TriggerSlope) -> bool:
        try:
            self.instrument.write(f'TRIGGER:A:EDGE:SLOPE {slope.value}')
            return True
        except Exception as e:
            print(f"設定觸發斜率失敗: {e}")
            return False
    
    def set_acquisition_mode(self, mode: AcquisitionMode, averages: Optional[int] = None) -> bool:
        try:
            self.instrument.write(f'ACQUIRE:MODE {mode.value}')
            if mode == AcquisitionMode.AVERAGING and averages is not None:
                self.instrument.write(f'ACQUIRE:NUMAVG {averages}')
            return True
        except Exception as e:
            print(f"設定擷取模式失敗: {e}")
            return False
    
    def start_acquisition(self) -> bool:
        try:
            self.instrument.write('ACQUIRE:STATE RUN')
            return True
        except Exception as e:
            print(f"開始擷取失敗: {e}")
            return False
    
    def stop_acquisition(self) -> bool:
        try:
            self.instrument.write('ACQUIRE:STATE STOP')
            return True
        except Exception as e:
            print(f"停止擷取失敗: {e}")
            return False
    
    def single_acquisition(self) -> bool:
        try:
            self.instrument.write('ACQUIRE:STOPAFTER SEQUENCE')
            self.instrument.write('ACQUIRE:STATE RUN')
            return True
        except Exception as e:
            print(f"單次擷取失敗: {e}")
            return False
    
    def is_triggered(self) -> bool:
        try:
            return int(self.instrument.query('TRIGGER:STATE?')) == 1
        except Exception:
            return False
    
    def get_waveform_data(self, channel: int) -> Tuple[List[float], List[float]]:
        try:
            # 設定波形數據格式
            self.instrument.write('DATA:SOURCE CH{channel}')
            self.instrument.write('DATA:ENCDG SRIBINARY')
            self.instrument.write('DATA:WIDTH 1')
            self.instrument.write('DATA:START 1')
            
            # 獲取水平和垂直刻度資訊
            x_inc = float(self.instrument.query('WFMOUTPRE:XINCR?'))
            y_mult = float(self.instrument.query('WFMOUTPRE:YMULT?'))
            y_off = float(self.instrument.query('WFMOUTPRE:YOFF?'))
            y_zero = float(self.instrument.query('WFMOUTPRE:YZERO?'))
            
            # 讀取波形數據
            raw_data = self.instrument.query_binary_values('CURVE?', datatype='b')
            
            # 轉換數據
            voltages = [(x - y_off) * y_mult + y_zero for x in raw_data]
            times = [i * x_inc for i in range(len(raw_data))]
            
            return times, voltages
        except Exception as e:
            print(f"獲取波形數據失敗: {e}")
            return [], []
    
    def get_measurement(self, channel: int, measurement_type: str) -> float:
        try:
            # 設定測量
            self.instrument.write(f'MEASUREMENT:IMMED:SOURCE CH{channel}')
            self.instrument.write(f'MEASUREMENT:IMMED:TYPE {measurement_type}')
            
            # 讀取測量值
            return float(self.instrument.query('MEASUREMENT:IMMED:VALUE?'))
        except Exception as e:
            print(f"獲取測量值失敗: {e}")
            return float('nan')
    
    def save_waveform(self, filepath: str, channels: List[int]) -> bool:
        try:
            channel_list = ','.join([f'CH{ch}' for ch in channels])
            self.instrument.write(f'SAVE:WAVEFORM:FILEFORMAT SPREADSHEET')
            self.instrument.write(f'SAVE:WAVEFORM:SOURCELIST {channel_list}')
            self.instrument.write(f'SAVE:WAVEFORM "{filepath}"')
            return True
        except Exception as e:
            print(f"保存波形失敗: {e}")
            return False
    
    def save_screenshot(self, filepath: str) -> bool:
        try:
            self.instrument.write('SAVE:IMAGE:FILEFORMAT PNG')
            self.instrument.write(f'SAVE:IMAGE "{filepath}"')
            return True
        except Exception as e:
            print(f"保存截圖失敗: {e}")
            return False
    
    def set_math_function(self, expression: str) -> bool:
        try:
            self.instrument.write(f'MATH:DEFINE "{expression}"')
            self.instrument.write('MATH:DISPLAY ON')
            return True
        except Exception as e:
            print(f"設定數學運算失敗: {e}")
            return False
    
    def clear_display(self) -> bool:
        try:
            self.instrument.write('CLEAR')
            return True
        except Exception as e:
            print(f"清除顯示失敗: {e}")
            return False
