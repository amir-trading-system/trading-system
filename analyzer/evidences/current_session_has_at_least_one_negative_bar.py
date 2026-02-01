import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_session_has_at_least_one_negative_bar"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_session_has_at_least_one_negative_bar = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close < bar_object.open_value
        )

        return common.objects.EvidenceResponse(
            result=current_session_has_at_least_one_negative_bar,
            reason=""
            if current_session_has_at_least_one_negative_bar
            else "No bar was negative since starting bar",
        )
