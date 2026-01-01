import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_7"

    def __init__(
        self,
        milestons: analyzer.objects.Milestones,
    ):
        super().__init__(
            milestons=milestons,
        )
        self.unique_evidences = {
            analyzer.evidences.current_bar_is_top_and_after_own_retracement.Evidence,
            analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
            analyzer.evidences.histogram_is_positive_until_now.Evidence,
            analyzer.evidences.histogram_top_appears_less_than_twice.Evidence,
            analyzer.evidences.milestones_are_valid.Evidence,
            analyzer.evidences.most_of_bars_are_volatile.Evidence,
            analyzer.evidences.fibonacci_retracement.Evidence,
            analyzer.evidences.no_more_than_2_retracements_until_now.Evidence,
            analyzer.evidences.does_not_have_big_retracement_between_top_to_start.Evidence,
            analyzer.evidences.retracement_should_be_long_enough.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
