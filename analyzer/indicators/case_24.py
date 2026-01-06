import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_24"

    def __init__(
        self,
        milestones: analyzer.objects.Milestones,
    ):
        super().__init__(
            milestones=milestones,
        )
        self.unique_evidences = {
            analyzer.evidences.has_bull_pattern.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
