import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_23"

    def __init__(
        self,
        milestons: analyzer.objects.Milestones,
    ):
        super().__init__(
            milestons=milestons,
        )
        self.unique_evidences = {
            analyzer.evidences.has_classic_bars_wave.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
