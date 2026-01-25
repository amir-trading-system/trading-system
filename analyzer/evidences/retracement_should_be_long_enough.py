import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "retracement_should_be_long_enough"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        retracement_should_be_long_enough = all(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close <= bar_object.open_value
        ) or milestones.top_bar.index >= 3

        return common.objects.EvidenceResponse(
            result=retracement_should_be_long_enough,
            reason=""
            if retracement_should_be_long_enough
            else "Retracement is not long enough",
        )
