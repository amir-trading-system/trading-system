from __future__ import annotations

import common

from . import base_pattern_detector


class PatternDetector(
    base_pattern_detector.PatternDetector
):
    name = "many_supports_to_one_resistance"

    def detect_pattern(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        unique_keys: dict[str, bool],
    ) -> list[base_pattern_detector.ManySupportsToOneResistaceDetection]:
        pattern_detections: list[base_pattern_detector.ManySupportsToOneResistaceDetection] = []

        if not (
            bar_object.ema_9 > bar_object.ema_20
            and bar_object.ema_9 > bar_object.vwap
            and bar_object.bar_lower_wick_percentage >= 0.15
            and bar_object.macd > 0
            and bar_object.signal_line > 0
            and bar_object.high - bar_object.low < 0.05
        ):
            return []

        previous_bars_with_same_low = sorted(
            [
                bar_obj
                for bar_obj in bars_since_04_am
                if bar_obj.bar_time < bar_object.bar_time
                and 0.99 <= bar_object.low/bar_obj.low <= 1.02
                and bar_obj.ema_9 > bar_obj.ema_20
                and bar_obj.ema_9 > bar_obj.vwap
                and bar_obj.bar_lower_wick_percentage >= 0.15
                and bar_obj.macd > 0
                and bar_obj.signal_line > 0
                and abs(bar_obj.low - bar_object.low) < abs(bar_obj.high - bar_object.low)
            ],
            key=lambda bar_obj: bar_obj.bar_time,
            reverse=True,
        )
        if not previous_bars_with_same_low:
            return []

        previous_bars_with_same_low.append(bar_object)

        first_support_bar = previous_bars_with_same_low[0]
        potential_resistance_bars = sorted(
            [
                bar_obj
                for bar_obj in bars_since_04_am
                if bar_obj.bar_time.date() == first_support_bar.bar_time.date()
                and bar_obj.bar_time < first_support_bar.bar_time
                and self.is_resistance_bar(
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                    bars_since_04_am=bars_since_04_am,
                    bar_object=bar_obj,
                    support_bar=first_support_bar,
                )
            ],
            key=lambda bar_obj: bar_obj.bar_time,
            reverse=True,
        )

        if not potential_resistance_bars:
            return []

        resistance_bar = potential_resistance_bars[0]

        unique_key = f"{first_support_bar.symbol}-{resistance_bar.bar_time}"
        if unique_key in unique_keys:
            return []

        if 2 <= len(previous_bars_with_same_low) <= 6:
            pattern_detections.append(
                base_pattern_detector.ManySupportsToOneResistaceDetection(
                    support_bars=previous_bars_with_same_low,
                    resistance_bar=resistance_bar,
                )
            )
            unique_keys[unique_key] = True

        return pattern_detections
