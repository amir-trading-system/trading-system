import analyzer.evidences
import common

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_17"

    def __init__(
        self,
        milestones: common.objects.Milestones,
        logger,
    ):
        super().__init__(
            milestones=milestones,
            logger=logger,
        )
        self.unique_evidences = {
            analyzer.evidences.current_bar_has_histogram_wave.Evidence,
            analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
            analyzer.evidences.current_bar_is_strong_with_high_volume.Evidence,
            analyzer.evidences.histogram_is_positive_until_now.Evidence,
            analyzer.evidences.histogram_top_appears_less_than_twice.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.negative_bars_volume_is_going_down.Evidence,
            analyzer.evidences.most_of_the_session_is_after_top_index.Evidence,
            analyzer.evidences.not_too_many_tops_with_rejections_in_range_of_current_bar.Evidence,
            analyzer.evidences.retracement_should_be_long_enough.Evidence,
            analyzer.evidences.starting_bar_is_not_the_biggest_in_terms_of_volume.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
