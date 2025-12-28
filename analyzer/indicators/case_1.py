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
                analyzer.evidences.no_more_than_2_retracements_until_now.Evidence,
            },
        )
