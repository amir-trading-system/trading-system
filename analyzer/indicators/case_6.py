import analyzer.evidences
import common

from . import indicator

class Indicator(
    indicator.Indicator,
):
    name = "case_6"

    def __init__(
        self,
        milestones: common.objects.Milestones,
        logger,
    ):
        super().__init__(
            milestones=milestones,
            logger=logger,
        )
        self.evidence = analyzer.evidences.current_day_upside_after_lowest_low.Evidence
