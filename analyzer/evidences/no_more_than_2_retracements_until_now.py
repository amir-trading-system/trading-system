from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "no_more_than_2_retracements_until_now"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        retracements = 0
        retracements_indexes: list[int] = []
        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )
            if not previous_bar or not next_bar:
                continue

            if (
                True
                and bar_object.low > previous_bar.low
                and bar_object.low < next_bar.low
            ):
                continue

            if (
                True
                and bar_object.high < previous_bar.high
                and bar_object.high < next_bar.high
                and next_bar.close > next_bar.open_value
                and (
                    bar_object.low <= bar_object.ema_9
                    or bar_object.ema_9/bar_object.low >= 0.9
                )
            ):
                if previous_bar.index not in retracements_indexes:
                    retracements += 1
                    retracements_indexes.append(bar_object.index)
                continue

            if (
                True
                and bar_object.high < previous_bar.high
                and bar_object.low < previous_bar.low
                and bar_object.low < next_bar.low
                and next_bar.close > next_bar.open_value
                and (
                    bar_object.low <= bar_object.ema_9
                    or bar_object.ema_9/bar_object.low >= 0.9
                )
            ):
                if previous_bar.index not in retracements_indexes:
                    retracements += 1
                    retracements_indexes.append(bar_object.index)
                continue

            if (
                True
                and bar_object.high < previous_bar.high
                and bar_object.high < next_bar.high
                and (bar_object.close - bar_object.low)/(bar_object.high - bar_object.low) > 0.5
                and (bar_object.open_value - bar_object.low)/(bar_object.high - bar_object.low) > 0.5
                and bar_object.low < previous_bar.low
                and bar_object.low < next_bar.low
            ):
                if previous_bar.index not in retracements_indexes:
                    retracements += 1
                    retracements_indexes.append(bar_object.index)
                continue

            if (
                True
                and bar_object.high < previous_bar.high
                and bar_object.low < previous_bar.low
                and bar_object.low < next_bar.low
                and bar_object.low - bar_object.ema_9 < previous_bar.low - previous_bar.ema_9
                and bar_object.low - bar_object.ema_9 < next_bar.low - next_bar.ema_9
                and (bar_object.close - bar_object.low)/(bar_object.high - bar_object.low) > 0.5
                and (bar_object.open_value - bar_object.low)/(bar_object.high - bar_object.low) > 0.5
                and bar_object.volume < previous_bar.volume
            ):
                if previous_bar.index not in retracements_indexes:
                    retracements += 1
                    retracements_indexes.append(bar_object.index)
                continue

            if (
                True
                and bar_object.index < milestones.top_bar.index
                and bar_object.index > current_bar.index
                and bar_object.low < previous_bar.low
                and bar_object.low < next_bar.low
                and bar_object.ema_9/bar_object.low >= 0.99
                and bar_object.index-1 == current_bar.index
            ):
                if previous_bar.index not in retracements_indexes:
                    retracements += 1
                    retracements_indexes.append(bar_object.index)
                continue

            if (
                True
                and bar_object.low < previous_bar.low
                and bar_object.low < next_bar.low
                and bar_object.low < bar_object.ema_9
                and next_bar.close > next_bar.open_value
                and bar_object.volume < bar_object.volume_average
            ):
                if previous_bar.index not in retracements_indexes:
                    retracements += 1
                    retracements_indexes.append(bar_object.index)
                continue

        no_more_than_2_retracements_until_now = 1 <= retracements <= 2

        return objects.EvidenceResponse(
            result=no_more_than_2_retracements_until_now,
            reason=""
            if no_more_than_2_retracements_until_now
            else "More than 2 retracements or no retracements at all",
        )
