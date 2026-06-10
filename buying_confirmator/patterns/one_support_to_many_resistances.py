from __future__ import annotations

import common

from . import base_pattern_detector


class PatternDetector(
    base_pattern_detector.PatternDetector
):
    name = "one_support_to_many_resistances"

    def detect_pattern(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        unique_keys: dict[str, bool],
    ) -> list[base_pattern_detector.OneSupportToManyResistancesDetection]:
        pattern_detections: list[base_pattern_detector.OneSupportToManyResistancesDetection] = []

        if not self.is_support_bar(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            bar_object=bar_object,
        ):
            return []

        support_bar = bar_object
        potential_resistance_bars = sorted(
            [
                bar_obj
                for bar_obj in bars_since_04_am
                if bar_obj.bar_time.date() == support_bar.bar_time.date()
                and bar_object.high - bar_object.low > 0.05
                and one_minute_timeframe_stock.previous_bar(
                    bar_object=bar_obj,
                ) is not None
                and one_minute_timeframe_stock.next_bar(
                    bar_object=bar_obj,
                ) is not None
                and one_minute_timeframe_stock.previous_bar(
                    bar_object=bar_obj,
                ).high <= bar_obj.high
                and one_minute_timeframe_stock.next_bar(
                    bar_object=bar_obj,
                ).high <= bar_obj.high
                and bar_obj.bar_time < support_bar.bar_time
                and 0.99 <= support_bar.low/bar_obj.high <= 1.02
                and bar_obj.ema_9 > bar_obj.ema_20
                and bar_obj.ema_9 > bar_obj.vwap
                and (
                    bar_obj.bar_wick_percentage >= 0.15
                    or not bar_obj.is_positive
                )
                and bar_obj.macd > 0
                and bar_obj.signal_line > 0
                and not any(
                    bar_between
                    for bar_between in bars_since_04_am
                    if bar_obj.bar_time < bar_between.bar_time < support_bar.bar_time
                    and bar_between.macd < 0
                    and bar_between.signal_line < 0
                )
            ],
            key=lambda bar_obj: bar_obj.bar_time,
            reverse=True,
        )
        if not potential_resistance_bars:
            return []

        resistance_bar = potential_resistance_bars[0]

        unique_key = f"{support_bar.symbol}-{resistance_bar.bar_time}"
        if unique_key in unique_keys:
            return []

        if 2 <= len(potential_resistance_bars) <= 6:
            pattern_detections.append(
                base_pattern_detector.OneSupportToManyResistancesDetection(
                    support_bar=support_bar,
                    resistance_bars=potential_resistance_bars,
                )
            )
            unique_keys[unique_key] = True

        return pattern_detections
