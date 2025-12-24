class IndicationResponse:
    def __init__(
        self,
        success_rate: float,
        result: bool,
    ):
        self.success_rate = success_rate
        self.result = result
