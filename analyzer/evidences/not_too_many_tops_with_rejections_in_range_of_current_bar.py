import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "not_too_many_tops_with_rejections_in_range_of_current_bar"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        rejections_count = 0
        for bar_object in relevant_bars:
            if bar_object.high < current_bar.open_value:
                continue
            if (
                True
                and bar_object.high > current_bar.open_value
                and bar_object.high < current_bar.high
                and bar_object.close < bar_object.open_value
                and bar_object.high - bar_object.low > 0
                and (bar_object.high - bar_object.open_value)/(bar_object.high - bar_object.low) >= 0.25
            ):
                rejections_count += 1
                continue

            if (
                True
                and bar_object.high > current_bar.open_value
                and bar_object.high < current_bar.high
                and bar_object.close < bar_object.high
                and bar_object.volume > bar_object.volume_average
                and bar_object.high - bar_object.low > 0
                and (
                        (
                            (bar_object.high - bar_object.close)/(bar_object.high - bar_object.low) >= 0.25
                            and bar_object.close > bar_object.open_value
                        )
                        or (
                            (bar_object.high - bar_object.open_value)/(bar_object.high - bar_object.low) >= 0.25
                            and bar_object.close < bar_object.open_value
                    )
                )
            ):
                rejections_count += 1
                continue

        not_too_many_tops_with_rejections_in_range_of_current_bar = not (
            rejections_count/milestones.starting_bar.index > 0.5
            or rejections_count > 3
        )

        return common.objects.EvidenceResponse(
            result=not_too_many_tops_with_rejections_in_range_of_current_bar,
            reason=""
            if not_too_many_tops_with_rejections_in_range_of_current_bar
            else f"Too many rejection count: {rejections_count}",
        )
