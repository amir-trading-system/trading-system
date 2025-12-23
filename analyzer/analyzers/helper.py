import datetime
import enum

from tws import objects as tws_objects

class MilestoneType(enum.Enum):
    STARTING_BAR = 1
    TOP_BAR = 2
    LOWEST_BAR = 3

class MilestoneBar:
    def __init__(
        self,
        index: int,
        bar_object: tws_objects.BarData = None,
        bar_type: MilestoneType = None,
        bar_time: datetime.datetime = None,
        timeframe: int = None,
    ):
        self.index = index
        self.bar_object = bar_object
        self.type = bar_type
        self.bar_time = bar_time
        self.timeframe = timeframe

class AnalyzerHelper:
    #pylint:disable=too-many-locals
    def get_strating_bar(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
    ) -> MilestoneBar:
        starting_bar = MilestoneBar(
            index=0,
            bar_type=MilestoneType.STARTING_BAR,
            timeframe=stock.timeframe,
        )

        starting_datetime = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=4,
        )

        bars_length = len(stock.bars)
        for i in range(current_bar.index,bars_length-1):
            potential_starting_bar: tws_objects.BarData = stock.bars[i]
            if (
                potential_starting_bar.bar_time < starting_datetime
                or current_bar.bar_time < potential_starting_bar.bar_time
            ):
                continue

            previous_bar = stock.bars[i+1]
            # pylint: disable=too-many-boolean-expressions,line-too-long
            is_really_potential_starting_bar = (
                potential_starting_bar.close > potential_starting_bar.open_value
                and potential_starting_bar.volume > previous_bar.volume * 1.5
                and potential_starting_bar.volume > potential_starting_bar.volume_average
                and potential_starting_bar.close > potential_starting_bar.ema_9
                and potential_starting_bar.high > potential_starting_bar.vwap
                and potential_starting_bar.high - potential_starting_bar.low > (previous_bar.high - previous_bar.low) * 2
                and potential_starting_bar.bar_time.day == current_bar.bar_time.day
                and (
                    potential_starting_bar.volume > 50000
                    or potential_starting_bar.bar_time.minute - previous_bar.bar_time.minute > stock.timeframe
                )
            )
            if is_really_potential_starting_bar:
                for j in range(i+1, i+31):
                    if j > len(stock.bars) - 2:
                        break
                    previous_bar: tws_objects.BarData = stock.bars[j]
                    if (previous_bar.bar_time.date() < potential_starting_bar.bar_time.date()
                    and previous_bar.bar_time.time() < datetime.time(hour=16)):
                        continue

                    more_volatile_than_starting_bar = (
                        previous_bar.volume > potential_starting_bar.volume
                        and previous_bar.high >= potential_starting_bar.high
                    )
                    previous_bar_close_to_starting_and_strong = (
                        previous_bar.volume/potential_starting_bar.volume >= 0.75
                        and j-i < 10
                        and previous_bar.volume > previous_bar.volume_average
                    )
                    previous_bar_body_identical_to_starting_bar = (
                        previous_bar.volume/potential_starting_bar.volume >= 0.6
                        and (previous_bar.high - previous_bar.low)/(potential_starting_bar.high - potential_starting_bar.low) > 0.9
                    )

                    previous_bar_is_strong_almost_as_current = (
                        previous_bar.close > previous_bar.open_value
                        and previous_bar.close > previous_bar.ema_9
                        and previous_bar.close > previous_bar.vwap
                        and previous_bar.volume > previous_bar.volume_average * 3
                        and previous_bar.volume > stock.bars[j+1].volume * 3
                        and previous_bar.volume > 200000
                    )

                    bar_before_previous_bar = stock.bars[j+1]
                    potential_starting_bar_before_starting_bar = (
                        (previous_bar.high - previous_bar.low) > (bar_before_previous_bar.high - bar_before_previous_bar.low) * 5
                        and previous_bar.close > previous_bar.open_value
                        and previous_bar.volume > bar_before_previous_bar.volume
                        and previous_bar.volume > previous_bar.volume_average * 3
                        and previous_bar.volume_average >= 10000
                    )

                    previous_bar_is_bigger_than_starting_bar = (
                        previous_bar.high - previous_bar.low > potential_starting_bar.high - potential_starting_bar.low
                        and previous_bar.close > previous_bar.open_value
                    )

                    if (
                        more_volatile_than_starting_bar
                        or previous_bar_close_to_starting_and_strong
                        or previous_bar_body_identical_to_starting_bar
                        or potential_starting_bar_before_starting_bar
                        or previous_bar_is_bigger_than_starting_bar
                        or previous_bar_is_strong_almost_as_current
                    ):
                        is_really_potential_starting_bar = False
                        break

            if is_really_potential_starting_bar:
                starting_bar = MilestoneBar(
                    index=i,
                    bar_object=potential_starting_bar,
                    bar_type=MilestoneType.STARTING_BAR,
                    bar_time=potential_starting_bar.bar_time,
                    timeframe=stock.timeframe,
                )
                break

        return starting_bar

    def get_top_bar(
        self,
        stock: tws_objects.Stock,
        starting_bar: MilestoneBar,
    ) -> MilestoneBar:
        top_bar = MilestoneBar(
            index=0,
            bar_type=MilestoneType.TOP_BAR,
            timeframe=stock.timeframe,
        )

        if starting_bar.index == 0 or len(stock.bars[2:starting_bar.index+1]) == 0:
            return top_bar

        high_picks_bars = [
            {"index": i, "bar": stock.bars[i]}
            for i in range(1, starting_bar.index+1)
            if stock.bars[i].high > stock.bars[i-1].high
            and stock.bars[i].high > stock.bars[i+1].high
        ]

        highest_high = max(
            high_picks_bars,
            key=lambda bar_dict: bar_dict["bar"].high
        )

        last_highest_index = min(
            high_picks_bars,
            key=lambda bar_dict: bar_dict["index"]
        )

        if last_highest_index["bar"].high > highest_high["bar"].high:
            return top_bar

        # pylint:disable=line-too-long,too-many-boolean-expressions
        for i in range(1,starting_bar.index+1):
            potential_top_bar = stock.bars[i]
            previous_bar = stock.bars[i+1]
            right_after_bar = stock.bars[i-1]
            if (
                ## need to fix the highest high logic.
                potential_top_bar.high == highest_high["bar"].high
                and potential_top_bar.high >= previous_bar.high
                and potential_top_bar.high > right_after_bar.high
                and potential_top_bar.close > potential_top_bar.ema_9
                and potential_top_bar.volume > potential_top_bar.volume_average * 2
                and (
                    potential_top_bar.volume > 50000
                    or potential_top_bar.bar_time.minute - previous_bar.bar_time.minute > stock.timeframe
                )
            ):
                top_bar = MilestoneBar(
                    index=i,
                    bar_object=potential_top_bar,
                    bar_type=MilestoneType.TOP_BAR,
                    bar_time=potential_top_bar.bar_time,
                    timeframe=stock.timeframe,
                )
                break

        return top_bar

    def get_lowest_bar_from_top_bar(
        self,
        stock: tws_objects.Stock,
        top_bar: MilestoneBar,
    ) -> MilestoneBar:
        lowest_milestone_bar = MilestoneBar(
            index=0,
            bar_type=MilestoneType.LOWEST_BAR,
            timeframe=stock.timeframe,
        )

        if top_bar.index == 0 or len(stock.bars[1:top_bar.index]) == 0:
            return lowest_milestone_bar

        lowest_low_bar = min(
            stock.bars[1:top_bar.index],
            key=lambda bar: bar.low
        )

        return MilestoneBar(
            index=lowest_low_bar.index,
            bar_object=lowest_low_bar,
            bar_type=MilestoneType.LOWEST_BAR,
            bar_time=lowest_low_bar.bar_time,
            timeframe=stock.timeframe,
        )
