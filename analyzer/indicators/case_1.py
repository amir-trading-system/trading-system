import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_1"

    def __init__(
        self,
    ):
        self.evidences.update(
            {
                analyzer.evidences.fibonacci_retracement.Evidence,
            },
        )
