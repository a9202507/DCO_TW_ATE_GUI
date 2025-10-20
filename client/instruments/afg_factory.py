from .afg_tektronix_3101c import TektronixAFG3101C

class AFGFactory:
    @staticmethod
    def create_afg(model: str, resource):
        if model == "TektronixAFG3101C":
            return TektronixAFG3101C(resource)
        raise ValueError(f"Unknown AFG model: {model}")
