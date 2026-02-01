import common
from . import _evidence
from . import histogram_mostly_positive


class Evidence(
    _evidence.Evidence,
):
    name = "histogram_is_positive_until_now"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        histogram_is_positive_until_now = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.histogram < 0
        )
        if not histogram_is_positive_until_now:
            histogram_mostly_positive_object = histogram_mostly_positive.Evidence()
            histogram_mostly_positive_result = histogram_mostly_positive_object.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
                is_retro=is_retro,
            )

            if histogram_mostly_positive_result.result:
                return histogram_mostly_positive_result

        return common.objects.EvidenceResponse(
            result=histogram_is_positive_until_now,
            reason=""
            if histogram_is_positive_until_now
            else "Histogram was not fully positive",
        )
