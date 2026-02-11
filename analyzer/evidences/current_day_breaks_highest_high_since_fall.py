import common
from common.objects import BarData, Milestones, Stock
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_breaks_highest_high_since_fall"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_day_breaks_highest_high_since_fall = True

        return common.objects.EvidenceResponse(
            result=current_day_breaks_highest_high_since_fall,
            reason=""
            if current_day_breaks_highest_high_since_fall
            else "Current day does not continues any trend",
        )

    def confirm(
        self,
        relevant_stock: Stock,
        potential_confirmation_bar: BarData,
        milestones: Milestones,
        highest_high_one_minute: float,
    ) -> bool:
        return super().confirm(relevant_stock, potential_confirmation_bar, milestones, highest_high_one_minute)
