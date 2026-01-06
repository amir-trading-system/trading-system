import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_27"

    def __init__(
        self,
        milestones: analyzer.objects.Milestones,
        logger,
    ):
        super().__init__(
            milestones=milestones,
            logger=logger,
        )
        self.unique_evidences = {
            analyzer.evidences.current_bar_crossed_finally_highest_high.Evidence,
            analyzer.evidences.current_bar_is_the_first_one_to_cross_top_bar.Evidence,
            analyzer.evidences.current_high_is_highest.Evidence,
            analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
            analyzer.evidences.current_bar_is_strong_with_high_volume.Evidence,
            analyzer.evidences.milestones_are_valid.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.fibonacci_retracement.Evidence,
            analyzer.evidences.negative_bars_volume_is_going_down.Evidence,
            analyzer.evidences.no_bars_closed_under_vwap.Evidence,
            analyzer.evidences.no_more_than_2_retracements_until_now.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
