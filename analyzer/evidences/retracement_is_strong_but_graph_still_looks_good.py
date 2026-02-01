import common
from . import _evidence
from . import fibonacci_retracement

class Evidence(
    _evidence.Evidence,
):
    name = "retracement_is_strong_but_graph_still_looks_good"

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

        fibonacci_retracement_evidence = fibonacci_retracement.Evidence()
        fibonacci_retracement_result = fibonacci_retracement_evidence.find_evidence(
            stock=stock,
            milestones=milestones,
            current_bar=current_bar,
            is_retro=is_retro,
        )

        if fibonacci_retracement_result.result:
            return common.objects.EvidenceResponse(
                result=False,
                reason="Fibonacci retracement is good so indicator wont run",
            )

        positive_histograms_count = 0
        negative_histograms_count = 0

        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if not previous_bar:
                continue

            if bar_object.histogram > previous_bar.histogram:
                positive_histograms_count += 1
            else:
                negative_histograms_count += 1

        most_histograms_are_positive = positive_histograms_count > 0 and negative_histograms_count/positive_histograms_count <= 0.5
        previous_bar = milestones.previous_bar.bar_object
        price_jumps_on_current_bar = (
            True
            and current_bar.high - current_bar.low > 0
            and (previous_bar.high - previous_bar.low)/(current_bar.high - current_bar.low) < 0.5
            and current_bar.close > current_bar.open_value
            and previous_bar.low/current_bar.low >= 0.9
        )

        retracement_is_strong_but_graph_still_looks_good = (
            True
            and float(fibonacci_retracement_result.value) > 0.8
            and most_histograms_are_positive
            and price_jumps_on_current_bar
        )

        return common.objects.EvidenceResponse(
            result=retracement_is_strong_but_graph_still_looks_good,
            reason=""
            if retracement_is_strong_but_graph_still_looks_good
            else "Retracement not so strong or price does not jumps on current bar",
        )
