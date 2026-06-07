#pylint: skip-file

import datetime

import common


class Helper:
    def __init__(
        self,
    ) -> None:
        self.unique_keys = {}

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
            and bar_object.bar_lower_wick_percentage >= 0.3
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
        potential_confirmation_bar: common.objects.BarData,
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
            and not bar_object.high < previous_bar.high
            and not bar_object.high < next_bar.high
            and bar_object.low < support_bar.low
            and bar_object.above_volume_average
            and bar_object.high > bar_object.vwap
            and bar_object.bar_wick_percentage >= 0.2
            and 0.99 <= bar_object.high/support_bar.low <= 1.01
            and not any(
                bar_obj
                for bar_obj in one_minute_timeframe_stock.bars
                if support_bar.bar_time < bar_obj.bar_time < potential_confirmation_bar.bar_time
                and bar_obj.close < bar_object.high
            )
            and len(
                [
                    bar_obj
                    for bar_obj in one_minute_timeframe_stock.bars
                    if bar_object.bar_time < bar_obj.bar_time < support_bar.bar_time
                    and bar_obj.low < bar_object.high < bar_obj.high
                ]
            ) <= 4
        )

    def is_breakout_bar(
        self,
        bar_object: common.objects.BarData,
        support_bar: common.objects.BarData,
        resistance_bar: common.objects.BarData,
        one_minute_timeframe_stock: common.objects.Stock,
    ) -> bool:
        return (
            True
            and bar_object.is_positive
            and resistance_bar.bar_time < bar_object.bar_time < support_bar.bar_time
            and bar_object.high > support_bar.low
            and bar_object.low < resistance_bar.high < bar_object.high
            and bar_object.above_volume_average
            and bar_object.bar_wick_percentage < 0.2
            and not any(
                bar_obj
                for bar_obj in one_minute_timeframe_stock.bars
                if bar_object.bar_time < bar_obj.bar_time < support_bar.bar_time
                and bar_obj.low/resistance_bar.high < 0.99
            )
        )

    def bar_potential_case_details(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> common.objects.CaseDetails:
        support_bar: common.objects.BarData = None
        resistance_bar: common.objects.BarData = None
        breakout_bar: common.objects.BarData = None
        unique_key = ""

        bar_potential_case_details = common.objects.CaseDetails(
            is_positive=False,
            support_bar=support_bar,
            resistance_bar=resistance_bar,
            breakout_bar=breakout_bar,
        )

        if (
            potential_confirmation_bar.close < potential_confirmation_bar.ema_9
            or potential_confirmation_bar.ema_9 < potential_confirmation_bar.ema_20
            or potential_confirmation_bar.ema_9 < potential_confirmation_bar.vwap
            or not potential_confirmation_bar.is_positive
            or not potential_confirmation_bar.above_vwap
            or not potential_confirmation_bar.above_volume_average
            or not potential_confirmation_bar.body_percentage >= 0.4
        ):
            return bar_potential_case_details

        for bar_object in one_minute_timeframe_stock.bars:
            if bar_object.bar_time.date() != potential_confirmation_bar.bar_time.date():
                continue

            if bar_object.bar_time > potential_confirmation_bar.bar_time:
                continue

            if (
                True
                and support_bar is not None
                and resistance_bar is None
                and self.is_resistance_bar(
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                    potential_confirmation_bar=potential_confirmation_bar,
                    bar_object=bar_object,
                    support_bar=support_bar,
                )
            ):
                resistance_bar = bar_object
                unique_key = f"{potential_confirmation_bar.symbol}-{support_bar.bar_time}-{resistance_bar.bar_time}"
                break

            if (
                True
                and support_bar is None
                and self.is_support_bar(
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                    bar_object=bar_object,
                )
            ):
                support_bar = bar_object
                continue

        if unique_key in self.unique_keys:
            return bar_potential_case_details

        bars_beetween_resistance_to_support = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if resistance_bar is not None
            and support_bar is not None
            and resistance_bar.bar_time < bar_object.bar_time < support_bar.bar_time
        ]

        for bar_object in bars_beetween_resistance_to_support:
            if (
                len(
                    [
                        bar_obj
                        for bar_obj in one_minute_timeframe_stock.bars
                        if resistance_bar.bar_time < bar_obj.bar_time < support_bar.bar_time
                        and bar_obj.low < resistance_bar.high < bar_obj.high
                    ]
                ) <= 3
                and self.is_breakout_bar(
                    bar_object=bar_object,
                    support_bar=support_bar,
                    resistance_bar=resistance_bar,
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                )
            ):
                breakout_bar = bar_object

                bar_potential_case_details = common.objects.CaseDetails(
                    is_positive=True,
                    support_bar=support_bar,
                    resistance_bar=resistance_bar,
                    breakout_bar=breakout_bar,
                )

                self.unique_keys[unique_key] = True
                break

        return bar_potential_case_details
