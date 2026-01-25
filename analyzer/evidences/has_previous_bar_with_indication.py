import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "has_previous_bar_with_indication"
    must_to_be_true = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:10]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )

        has_any_bar_with_indication_before = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.has_indication
        )

        has_previous_bar_with_indication = (
            True
            and previous_bar is not None
            and has_any_bar_with_indication_before
            and current_bar.ema_9/current_bar.low >= 0.99
            and current_bar.volume > current_bar.volume_average
            and current_bar.ema_9 > current_bar.vwap
            and current_bar.ema_9 > current_bar.ema_20
            and current_bar.histogram > stock.previous_bar(
                bar_object=current_bar,
            ).histogram
        )

        return common.objects.EvidenceResponse(
            result=has_previous_bar_with_indication,
            reason=""
            if has_previous_bar_with_indication
            else "Does not have previous bars with indication",
        )
