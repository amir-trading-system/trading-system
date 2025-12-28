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
                analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
                analyzer.evidences.current_bar_is_strong_with_high_volume.Evidence,
                analyzer.evidences.histogram_changed_direction.Evidence,
                analyzer.evidences.all_bars_are_positive_with_own_retracement.Evidence,
                analyzer.evidences.has_big_retracement_between_top_to_start.Evidence,
            },
        )
