#pylint: skip-file

import datetime

import common


class Helper:
    def __init__(
        self,
    ) -> None:
        self.unique_keys = {}

    def bar_potential_case_details(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[common.objects.ClassicCaseDetails | common.objects.OneSupportToManyResistanceCaseDetails | common.objects.ManySupportsToOneResistanceCaseDetails]:
        case_details: list[common.objects.ClassicCaseDetails | common.objects.OneSupportToManyResistanceCaseDetails | common.objects.ManySupportsToOneResistanceCaseDetails] = []

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
            if potential_confirmation_bar.bar_time - datetime.timedelta(minutes=20) < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        for bar_object in relevant_bars:
            if bar_object.bar_time.date() != potential_confirmation_bar.bar_time.date():
                continue

            self.detect_classic_support_resistance_pattern_cases(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                bars_since_04_am=bars_since_04_am,
                bar_object=bar_object,
                case_details=case_details,
            )

            self.detect_consistent_supports_to_resistance_cases(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                bars_since_04_am=bars_since_04_am,
                bar_object=bar_object,
                case_details=case_details,
            )

            self.detect_consistent_resistances_to_support_cases(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                bars_since_04_am=bars_since_04_am,
                bar_object=bar_object,
                case_details=case_details,
            )

        return case_details

    def detect_classic_support_resistance_pattern_cases(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        case_details: list[common.objects.ClassicCaseDetails],
    ) -> None:
        if not self.is_support_bar(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            bar_object=bar_object,
        ):
            return

        support_bar = bar_object
        potential_resistance_bars = [
            bar_obj
            for bar_obj in bars_since_04_am
            if bar_obj.bar_time.date() == support_bar.bar_time.date()
            and bar_obj.bar_time < support_bar.bar_time
            and self.is_resistance_bar(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                bars_since_04_am=bars_since_04_am,
                bar_object=bar_obj,
                support_bar=support_bar,
            )
        ]

        for resistance_bar in potential_resistance_bars:
            unique_key = f"{support_bar.symbol}-{support_bar.bar_time}-{resistance_bar.bar_time}"
            if unique_key in self.unique_keys:
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
                    bar_object=bar_object,
                    support_bar=support_bar,
                    resistance_bar=resistance_bar,
                    bars_since_04_am=bars_since_04_am,
                ):
                    continue

                breakout_bar = bar_object

                case_details.append(
                    common.objects.ClassicCaseDetails(
                        support_bar=support_bar,
                        resistance_bar=resistance_bar,
                        breakout_bar=breakout_bar,
                    )
                )

                self.unique_keys[unique_key] = True
                break

    def detect_consistent_supports_to_resistance_cases(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        case_details: list[common.objects.ManySupportsToOneResistanceCaseDetails],
    ) -> None:
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
            ],
            key=lambda bar_obj: bar_obj.bar_time,
            reverse=True,
        )
        if not previous_bars_with_same_low:
            return

        previous_bars_with_same_low.append(bar_object)

        first_support_bar = previous_bars_with_same_low[-1]
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
            return

        resistance_bar = potential_resistance_bars[0]

        unique_key = f"{first_support_bar.symbol}-{first_support_bar.bar_time}-{resistance_bar.bar_time}"
        if unique_key in self.unique_keys:
            return

        if len(previous_bars_with_same_low) >= 4:
            case_details.append(
                common.objects.ManySupportsToOneResistanceCaseDetails(
                    support_bars=previous_bars_with_same_low,
                    resistance_bar=resistance_bar,
                )
            )
            self.unique_keys[unique_key] = True

    def detect_consistent_resistances_to_support_cases(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        bars_since_04_am: list[common.objects.BarData],
        bar_object: common.objects.BarData,
        case_details: list[common.objects.OneSupportToManyResistanceCaseDetails],
    ) -> None:
        if not self.is_support_bar(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            bar_object=bar_object,
        ):
            return

        support_bar = bar_object
        potential_resistance_bars = sorted(
            [
                bar_obj
                for bar_obj in bars_since_04_am
                if bar_obj.bar_time.date() == support_bar.bar_time.date()
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
            ],
            key=lambda bar_obj: bar_obj.bar_time,
            reverse=True,
        )
        if not potential_resistance_bars:
            return

        resistance_bar = potential_resistance_bars[-1]

        unique_key = f"{support_bar.symbol}-{support_bar.bar_time}-{resistance_bar.bar_time}"
        if unique_key in self.unique_keys:
            return

        if len(potential_resistance_bars) >= 3:
            case_details.append(
                common.objects.OneSupportToManyResistanceCaseDetails(
                    support_bar=support_bar,
                    resistance_bars=potential_resistance_bars,
                )
            )
            self.unique_keys[unique_key] = True

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
            and bar_object.bar_wick_percentage >= 0.2
            and 0.99 <= bar_object.high/support_bar.low <= 1.02
            and len(
                [
                    bar_obj
                    for bar_obj in bars_since_04_am
                    if bar_object.bar_time < bar_obj.bar_time < support_bar.bar_time
                    and bar_obj.low < bar_object.high < bar_obj.high
                    and bar_obj.low/bar_object.high <= 0.99
                ]
            ) <= 2
        )

    def is_breakout_bar(
        self,
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
        )
