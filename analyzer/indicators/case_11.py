import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_11"

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
            analyzer.evidences.all_bars_are_positive_with_own_retracement.Evidence,
            analyzer.evidences.current_bar_crossed_finally_highest_high.Evidence,
            analyzer.evidences.current_bar_is_top_and_after_own_retracement.Evidence,
            analyzer.evidences.histogram_is_positive_until_now.Evidence,
            analyzer.evidences.histogram_top_appears_less_than_twice.Evidence,
            analyzer.evidences.most_of_bars_are_volatile.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
            analyzer.evidences.histogram_did_not_changed_direction.Evidence,
            analyzer.evidences.starting_bar_is_not_the_biggest_in_terms_of_price.Evidence,
            analyzer.evidences.volume_sum_is_positive.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
