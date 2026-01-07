import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "already_has_indication"

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
            analyzer.evidences.movement_is_after_market_starts.Evidence,
            analyzer.evidences.current_bar_is_positive_and_volatile.Evidence,
            analyzer.evidences.current_bar_higher_than_previous.Evidence,
            analyzer.evidences.current_bar_is_full.Evidence,
            analyzer.evidences.current_bar_is_not_the_volume_weakest_since_top_bar.Evidence,
            analyzer.evidences.retracement_occured_since_top_bar.Evidence,
            analyzer.evidences.current_bar_close_above_top_high_if_crossed_it.Evidence,
            analyzer.evidences.current_bar_after_market_starts.Evidence,
            analyzer.evidences.top_bar_is_not_the_lowest_bar.Evidence,
            analyzer.evidences.at_least_one_bar_was_closed_to_9_ema_since_start.Evidence,
            analyzer.evidences.has_previous_bar_with_indication.Evidence,
        }
        self.evidences = self.unique_evidences
