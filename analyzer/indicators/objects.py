class IndicatorResponse:
    def __init__(
        self,
        success_count: int,
        success_rate: float,
        result: bool,
        failed_base_evidences_count: int,
    ):
        self.success_rate = success_rate
        self.success_count = success_count
        self.result = result
        self.failed_base_evidences_count = failed_base_evidences_count
