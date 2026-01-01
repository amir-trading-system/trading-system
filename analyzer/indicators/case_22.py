import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_22"

    def __init__(
        self,
        milestons: analyzer.objects.Milestones,
    ):
        super().__init__(
            milestons=milestons,
        )
        self.unique_evidences = {
            analyzer.evidences.current_bar_crossed_finally_highest_high.Evidence,
            analyzer.evidences.current_bar_is_highest_and_full.Evidence,
            analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
            analyzer.evidences.current_bar_is_strong_with_high_volume.Evidence,
            analyzer.evidences.histogram_changed_direction.Evidence,
            analyzer.evidences.histogram_is_positive_until_now.Evidence,
            analyzer.evidences.histogram_top_appears_less_than_twice.Evidence,
            analyzer.evidences.most_of_bars_are_volatile.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.fibonacci_retracement.Evidence,
            analyzer.evidences.negative_bars_volume_is_going_down.Evidence,
            analyzer.evidences.no_bars_closed_under_vwap.Evidence,
            analyzer.evidences.starting_bar_is_not_the_biggest_in_terms_of_price.Evidence,
            analyzer.evidences.starting_bar_is_not_the_biggest_in_terms_of_volume.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
