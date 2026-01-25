import common
from . import _evidence
from . import no_more_than_2_retracements_until_now


class Evidence(
    _evidence.Evidence,
):
    name = "first_retracement_is_not_too_late"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[milestones.top_bar.index:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        no_more_than_2_retracements_until_now_evidence = no_more_than_2_retracements_until_now.Evidence()
        evidence = no_more_than_2_retracements_until_now_evidence.find_evidence(
            stock=stock,
            milestones=milestones,
            current_bar=current_bar,
        )

        retracement_indexes: list[int] = evidence.value
        if len(retracement_indexes) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no retracement indexes",
            )

        first_retracement_index = max(retracement_indexes)
        retracement_attempts = len(
            [
                bar_object
                for bar_object in relevant_bars
                if (
                    True
                    and bar_object.high - bar_object.low > 0
                    and (bar_object.open_value - bar_object.low)/(bar_object.high - bar_object.low) >= 0.25
                    and bar_object.volume > bar_object.volume_average
                    and bar_object.open_value - bar_object.low > bar_object.high - bar_object.close
                )
            ]
        )

        first_retracement_is_not_too_late = not (
            True
            and first_retracement_index/milestones.starting_bar.index < 0.4
            and milestones.starting_bar.index >= 10
            and retracement_attempts < 2
        )

        return common.objects.EvidenceResponse(
            result=first_retracement_is_not_too_late,
            reason=""
            if first_retracement_is_not_too_late
            else "First retracement came too late",
        )
