from __future__ import annotations

import common

from . import base_pattern_detector


class PatternDetector(
    base_pattern_detector.PatternDetector,
):
    name = "classic_support_to_resistance"

    def detect_pattern(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        unique_keys: dict[str, bool],
    ) -> list[base_pattern_detector.ClassicSUpportToResistanceDetection]:
        pattern_detections: list[base_pattern_detector.ClassicSUpportToResistanceDetection] = []

        if not self.is_support_bar(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            bar_object=bar_object,
        ):
            return []

        support_bar = bar_object

        potential_resistance_bars = [
            bar_obj
            for bar_obj in bars_since_04_am
            if bar_obj.bar_time.date() == support_bar.bar_time.date()
            and bar_obj.bar_time < support_bar.bar_time
            and bar_obj.high - bar_obj.low > 0.05
            and self.is_resistance_bar(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                bars_since_04_am=bars_since_04_am,
                bar_object=bar_obj,
                support_bar=support_bar,
            )
            and any(
                bar_object
                for bar_object in bars_since_04_am
                if bar_obj.bar_time < bar_object.bar_time < support_bar.bar_time
                and one_minute_timeframe_stock.previous_bar(
                    bar_object=bar_object,
                ) is not None
                and one_minute_timeframe_stock.previous_bar(
                    bar_object=bar_object,
                ).low > bar_object.low
            )
        ]

        for resistance_bar in potential_resistance_bars:
            unique_key = f"{support_bar.symbol}-{support_bar.bar_time}-{resistance_bar.bar_time}"
            if unique_key in unique_keys:
                continue

            bars_beetween_resistance_to_support = [
                bar_object
                for bar_object in bars_since_04_am
                if resistance_bar.bar_time < bar_object.bar_time < support_bar.bar_time
                and bar_object.low/resistance_bar.high <= 0.99
            ]

            resistance_crossed_clean = len(
                [
                    bar_obj
                    for bar_obj in bars_since_04_am
                    if resistance_bar.bar_time < bar_obj.bar_time < support_bar.bar_time
                    and bar_obj.low < resistance_bar.high < bar_obj.high
                    and bar_obj.low/resistance_bar.high <= 0.99
                ]
            ) <= 3

            if not resistance_crossed_clean:
                continue

            for bar_object in bars_beetween_resistance_to_support:
                if not self.is_breakout_bar(
                    potential_confirmation_bar=potential_confirmation_bar,
                    bar_object=bar_object,
                    support_bar=support_bar,
                    resistance_bar=resistance_bar,
                    bars_since_04_am=bars_since_04_am,
                ):
                    continue

                breakout_bar = bar_object

                pattern_detections.append(
                    base_pattern_detector.ClassicSUpportToResistanceDetection(
                        support_bar=support_bar,
                        resistance_bar=resistance_bar,
                        breakout_bar=breakout_bar,
                    )
                )

                unique_keys[unique_key] = True
                break

        return pattern_detections
