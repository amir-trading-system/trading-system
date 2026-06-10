from __future__ import annotations

import common


class PatternDetector:
    name = ""

    def detect_pattern(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        unique_keys: dict[str, bool],
    ) -> list[ClassicSUpportToResistanceDetection | ManySupportsToOneResistaceDetection | OneSupportToManyResistancesDetection]:
        raise NotImplementedError()

    def is_support_bar(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        bar_object: common.objects.BarData,
    ) -> bool:
        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=bar_object,
        )
        next_bar = one_minute_timeframe_stock.next_bar(
            bar_object=bar_object,
        )
        previous_to_previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=previous_bar,
        ) if previous_bar is not None else None

        return (
            True
            and bar_object.ema_9 > bar_object.ema_20
            and bar_object.ema_9 > bar_object.vwap
            and bar_object.bar_lower_wick_percentage >= 0.15
            and bar_object.bar_lower_wick_percentage > bar_object.bar_wick_percentage
            and bar_object.macd > 0
            and bar_object.signal_line > 0
            and previous_bar is not None
            and next_bar is not None
            and (
                (
                    True
                    and 0.99 <= bar_object.low/previous_bar.low <= 1.01
                    and bar_object.low < next_bar.low
                )
                or (
                    True
                    and previous_to_previous_bar is not None
                    and bar_object.low == previous_bar.low
                    and previous_bar.low < previous_to_previous_bar.low
                    and bar_object.low < next_bar.low
                )
                or (
                    True
                    and bar_object.low < previous_bar.low
                    and bar_object.low < next_bar.low
                )
            )
        )

    def is_resistance_bar(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        support_bar: common.objects.BarData,
    ) -> bool:
        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=bar_object,
        )
        next_bar = one_minute_timeframe_stock.next_bar(
            bar_object=bar_object,
        )
        return (
            True
            and previous_bar is not None
            and next_bar is not None
            and bar_object.high > previous_bar.high
            and bar_object.high > next_bar.high
            and bar_object.low < support_bar.low
            and bar_object.above_volume_average
            and bar_object.high > bar_object.vwap
            and bar_object.macd > 0
            and bar_object.signal_line > 0
            and bar_object.bar_wick_percentage >= 0.1
            and 0.99 <= bar_object.high/support_bar.low <= 1.02
            and len(
                [
                    bar_obj
                    for bar_obj in bars_since_04_am
                    if bar_object.bar_time < bar_obj.bar_time < support_bar.bar_time
                    and (
                        bar_obj.open_value < bar_object.high < bar_obj.high
                        or bar_obj.close < bar_object.high < bar_obj.high
                    )
                    and bar_obj.low/bar_object.high <= 0.99
                ]
            ) <= 2
        )

    def is_breakout_bar(
        self,
        potential_confirmation_bar: common.objects.BarData,
        bar_object: common.objects.BarData,
        support_bar: common.objects.BarData,
        resistance_bar: common.objects.BarData,
        bars_since_04_am: list[common.objects.BarData],
    ) -> bool:
        return (
            True
            and bar_object.is_positive
            and resistance_bar.bar_time < bar_object.bar_time < support_bar.bar_time
            and bar_object.high > support_bar.low
            and bar_object.low < resistance_bar.high < bar_object.high
            and bar_object.above_volume_average
            and bar_object.bar_wick_percentage < 0.5
            and not any(
                bar_obj
                for bar_obj in bars_since_04_am
                if bar_object.bar_time < bar_obj.bar_time < support_bar.bar_time
                and bar_obj.low/resistance_bar.high < 0.99
            )
            and not any(
                bar_obj
                for bar_obj in bars_since_04_am
                if bar_object.bar_time < bar_obj.bar_time < potential_confirmation_bar.bar_time
                and bar_obj.close < resistance_bar.high
            )
        )

class ClassicSUpportToResistanceDetection:
    def __init__(
        self,
        support_bar: common.objects.BarData,
        resistance_bar: common.objects.BarData,
        breakout_bar: common.objects.BarData = None,
    ):
        self.support_bar = support_bar
        self.resistance_bar = resistance_bar
        self.breakout_bar = breakout_bar


    def get_details(
        self,
    ) -> dict[str, any]:
        return {
            "support_bar_time": self.support_bar.bar_time,
            "resistance_bar_time": self.resistance_bar.bar_time,
            "breakout_bar_time": self.breakout_bar.bar_time,
            "case_type": "classic_support_to_resistance",
        }

class ManySupportsToOneResistaceDetection:
    def __init__(
        self,
        support_bars: list[common.objects.BarData],
        resistance_bar: common.objects.BarData,
    ):
        self.support_bars = support_bars
        self.resistance_bar = resistance_bar

    def get_details(
        self,
    ) -> dict[str, any]:
        return {
            "support_bar_time": [
                bar_object.bar_time
                for bar_object in self.support_bars
            ],
            "resistance_bar_time": self.resistance_bar.bar_time,
            "case_type": "one_resistance_to_many_supports",
        }

class OneSupportToManyResistancesDetection:
    def __init__(
        self,
        support_bar: common.objects.BarData,
        resistance_bars: list[common.objects.BarData],
        breakout_bar: common.objects.BarData = None,
    ):
        self.support_bar = support_bar
        self.resistance_bars = resistance_bars
        self.breakout_bar = breakout_bar

    def get_details(
        self,
    ) -> dict[str, any]:
        return {
            "support_bar_time": self.support_bar.bar_time,
            "resistance_bar_time": [
                bar_object.bar_time
                for bar_object in self.resistance_bars
            ],
            "case_type": "one_support_to_many_resistances",
        }
