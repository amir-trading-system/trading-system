import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_8_a"

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
            analyzer.evidences.current_session_has_at_least_one_negative_bar.Evidence,
            analyzer.evidences.histogram_changed_direction.Evidence,
            analyzer.evidences.histogram_is_positive_until_now.Evidence,
            analyzer.evidences.histogram_top_appears_less_than_twice.Evidence,
            analyzer.evidences.milestones_are_valid.Evidence,
            analyzer.evidences.most_of_bars_are_volatile.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.most_of_the_session_is_before_top_index.Evidence,
            analyzer.evidences.fibonacci_retracement.Evidence,
            analyzer.evidences.no_more_than_2_retracements_until_now.Evidence,
            analyzer.evidences.does_not_have_big_retracement_between_top_to_start.Evidence,
            analyzer.evidences.first_retracement_is_not_too_late.Evidence,
            analyzer.evidences.retracement_should_be_long_enough.Evidence,
            analyzer.evidences.starting_bar_is_not_the_biggest_in_terms_of_volume.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
