class AFGInterface:
    """AFG (Arbitrary Function Generator) 通用介面"""
    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def set_waveform(self, waveform_type: str, frequency: float, amplitude: float):
        raise NotImplementedError()

    def output_on(self):
        raise NotImplementedError()

    def output_off(self):
        raise NotImplementedError()
