import analyzer.evidences

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_29"

    def __init__(
        self,
        milestones: analyzer.objects.Milestones,
        logger,
    ):
        super().__init__(
            milestones=milestones,
            logger=logger,
        )
        self.can_be_confirm_by_itself = True
        self.unique_evidences = {
            analyzer.evidences.current_bar_is_highest_and_full.Evidence,
            analyzer.evidences.most_of_current_bar_is_above_9_ema.Evidence,
        }
        self.evidences.update(
            self.unique_evidences,
        )
