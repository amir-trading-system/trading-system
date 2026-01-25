import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "no_bars_closed_under_vwap"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.top_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        no_bars_closed_under_vwap = all(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close >= bar_object.vwap
        )

        return common.objects.EvidenceResponse(
            result=no_bars_closed_under_vwap,
            reason=""
            if no_bars_closed_under_vwap
            else "Some bars closed under vwap since top bar",
        )
