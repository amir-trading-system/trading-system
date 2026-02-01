import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "retracement_occured_since_top_bar"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.top_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        has_at_least_one_retracement_bar = any(
            bar_object
            for bar_object in relevant_bars
            if stock.previous_bar(
                bar_object=bar_object,
            ) is not None
            and bar_object.low < stock.bars[bar_object.index+1].low
        )

        has_flag_pattern = False
        if not has_at_least_one_retracement_bar:
            has_flag_pattern = all(
                bar_object
                for bar_object in relevant_bars
                if bar_object.index > current_bar.index
                and stock.previous_bar(
                    bar_object=bar_object,
                ) is not None
                and (
                    bar_object.high < stock.bars[bar_object.index+1].high
                    or abs(bar_object.close - bar_object.open_value) < abs(stock.bars[bar_object.index+1].close - stock.bars[bar_object.index+1].open_value)
                )
            )
        retracement_occured_since_top_bar = (
            has_at_least_one_retracement_bar
            or has_flag_pattern
            or milestones.top_bar.index <= 2
        )

        return common.objects.EvidenceResponse(
            result=retracement_occured_since_top_bar,
            reason=""
            if retracement_occured_since_top_bar
            else "No real retracement occured since top bar",
        )
