import common

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_crossed_finally_highest_high"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        bars_trying_cross_highest_high_attempts = 0
        current_close_above_high = (
            True
            and current_bar.high > milestones.top_bar.bar_object.high
            and current_bar.close/milestones.top_bar.bar_object.high >= 0.9
        )
        if current_close_above_high:
            bars_trying_cross_highest_high_attempts = len(
                [
                    bar_object.index
                    for bar_object in relevant_bars
                    if bar_object.high/milestones.top_bar.bar_object.high >= 0.96
                    and bar_object.high - bar_object.low > 0
                    and (bar_object.close - bar_object.low)/(bar_object.high - bar_object.low) <= 0.7
                ]
            )

        current_bar_crossed_finally_highest_high = (
            True
            and current_close_above_high
            and bars_trying_cross_highest_high_attempts >= 2
        )

        return common.objects.EvidenceResponse(
            result=current_bar_crossed_finally_highest_high,
            reason=""
            if current_bar_crossed_finally_highest_high
            else f"not enough attempts to cross highest high. attemps: {bars_trying_cross_highest_high_attempts}",
        )
