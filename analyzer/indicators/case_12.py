import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_12"

    def __init__(
        self,
        milestons: analyzer.objects.Milestones,
    ):
        super().__init__(
            milestons=milestons,
        )
        self.unique_evidences = {
            analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
            analyzer.evidences.current_bar_is_strong_with_high_volume.Evidence,
            analyzer.evidences.histogram_changed_direction.Evidence,
            analyzer.evidences.histogram_is_positive_until_now.Evidence,
            analyzer.evidences.histogram_top_appears_less_than_twice.Evidence,
            analyzer.evidences.milestones_are_valid.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.fibonacci_retracement.Evidence,
            analyzer.evidences.negative_bars_are_weak.Evidence,
            analyzer.evidences.negative_bars_volume_is_going_down.Evidence,
            analyzer.evidences.does_not_have_big_retracement_between_top_to_start.Evidence,
            analyzer.evidences.not_too_many_tops_with_rejections_in_range_of_current_bar.Evidence,
            analyzer.evidences.retracement_should_be_long_enough.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
        self.must_to_have = []
