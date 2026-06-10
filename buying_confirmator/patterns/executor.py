#pylint: skip-file

import datetime

import common

from . import classic_support_to_resistance
from . import one_support_to_many_resistances
from . import many_supports_to_one_resistance
from . import base_pattern_detector


__detectors__: list[type[base_pattern_detector.PatternDetector]] = [
    classic_support_to_resistance.PatternDetector,
    one_support_to_many_resistances.PatternDetector,
    many_supports_to_one_resistance.PatternDetector,
]

class PatternDetectorExecutor:
    def __init__(
        self,
    ) -> None:
        self.unique_keys = {}

    def find_support_to_resistance_patterns(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[base_pattern_detector.ClassicSUpportToResistanceDetection | base_pattern_detector.OneSupportToManyResistancesDetection | base_pattern_detector.ManySupportsToOneResistaceDetection]:
        support_to_resistance_patterns: list[base_pattern_detector.ClassicSUpportToResistanceDetection | base_pattern_detector.OneSupportToManyResistancesDetection | base_pattern_detector.ManySupportsToOneResistaceDetection] = []

        if (
            potential_confirmation_bar.close < potential_confirmation_bar.ema_9
            or potential_confirmation_bar.ema_9 < potential_confirmation_bar.ema_20
            or potential_confirmation_bar.ema_9 < potential_confirmation_bar.vwap
            or not potential_confirmation_bar.is_positive
            or not potential_confirmation_bar.above_vwap
            or not potential_confirmation_bar.above_volume_average
            or not potential_confirmation_bar.body_percentage >= 0.4
        ):
            return []

        bars_since_04_am = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if bar_object.bar_time >= datetime.datetime(
                year=potential_confirmation_bar.bar_time.year,
                month=potential_confirmation_bar.bar_time.month,
                day=potential_confirmation_bar.bar_time.day,
                hour=4,
            )
        ]

        relevant_bars = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if potential_confirmation_bar.bar_time - datetime.timedelta(minutes=40) < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]
        for bar_object in relevant_bars:
            if bar_object.bar_time.date() != potential_confirmation_bar.bar_time.date():
                continue

            for detector in __detectors__:
                detected_patterns = detector().detect_pattern(
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                    potential_confirmation_bar=potential_confirmation_bar,
                    bars_since_04_am=bars_since_04_am,
                    bar_object=bar_object,
                    unique_keys=self.unique_keys,
                )
                support_to_resistance_patterns.extend(detected_patterns)

        return support_to_resistance_patterns
