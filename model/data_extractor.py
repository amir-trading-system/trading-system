import datetime

import common


class DataExtractor:
    @staticmethod
    def feature_high_lows_pct(
        one_minute_timeframe_stock: common.objects.Stock,
        one_minute_bars: list[common.objects.BarData],
    ):
        swing_lows: list[float] = []
        for bar_object in one_minute_bars[1:]:
            if (
                bar_object.low < bar_object.vwap
                or bar_object.ema_9 < bar_object.vwap
                or bar_object.ema_9 < bar_object.ema_20
            ):
                break

            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )

            if previous_bar is None or next_bar is None:
                continue

            is_local_low = (
                bar_object.low < previous_bar.low
                and bar_object.low < next_bar.low
            )
            bullish_context = (
                bar_object.low > bar_object.vwap
                and bar_object.ema_9 > bar_object.vwap
                and bar_object.ema_9 > bar_object.ema_20
            )
            if is_local_low and bullish_context:
                swing_lows.append(bar_object.low)

        if len(swing_lows) < 2:
            return 0.0

        higher_count = 0
        for i in range(1, len(swing_lows)):
            if swing_lows[i] > swing_lows[i - 1]:
                higher_count += 1

        return higher_count / (len(swing_lows) - 1)

    @staticmethod
    def analyze_last_pullback(
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, float]:
        pullback_analysis = {
            "feature_pullback_sharpness": 0.0,
            "feature_pullback_depth": 0.0,
            "feature_number_of_negative_bars_in_pullback_pct": 0.0,
            "feature_pullback_to_trend_ratio": 0.0,
        }

        bars_since_highest_high = [
            bar_object
            for bar_object in one_minute_bars
            if highest_high_one_minute_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        if bars_since_highest_high:
            lowest_low_bar = None
            lowest_low_since_highest_high = min(
                bar_object.low
                for bar_object in bars_since_highest_high
            )

            for bar_object in bars_since_highest_high:
                if bar_object.low == lowest_low_since_highest_high:
                    lowest_low_bar = bar_object

            pullback_bars = [
                bar_object
                for bar_object in bars_since_highest_high
                if highest_high_one_minute_bar.bar_time < bar_object.bar_time <= lowest_low_bar.bar_time
            ]

            number_of_negative_bars_in_pullback = len(
                [
                    bar_object
                    for bar_object in pullback_bars
                    if bar_object.close < bar_object.open_value
                ]
            )

            pullback_duration = len(pullback_bars)
            pullback_size = sum(
                bar_object.high - bar_object.low
                for bar_object in pullback_bars
            )

            pullback_analysis["feature_pullback_sharpness"] = pullback_size/pullback_duration
            pullback_analysis["feature_pullback_depth"] = highest_high_one_minute_bar.high - lowest_low_bar.low if lowest_low_bar is not None else 0.0
            pullback_analysis["feature_number_of_negative_bars_in_pullback_pct"] = number_of_negative_bars_in_pullback/len(pullback_bars)
            pullback_analysis["feature_pullback_to_trend_ratio"] = pullback_analysis["feature_pullback_depth"]/highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else 0

        return pullback_analysis

    @staticmethod
    def extract_features_from_symbol_data(
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        volume_sum_since_market_open: float,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, float]:
        total_bars = len(one_minute_bars)
        total_volume = 0
        positive_volume_sum = 0
        negative_volume_sum = 0
        positive_movement = 0
        negative_movement = 0

        positive_bars_counter = 0
        negative_bars_counter = 0
        last_bars_positive_bars = 0
        last_bars_negative_bars = 0

        bars_with_at_least_50_pct_wick_counter = 0
        strong_positive_bars_with_full_body_counter = 0
        bars_with_negative_momentum_histogram_counter = 0
        bars_with_lower_volume_average_counter = 0
        macd_under_signal_line_counter = 0
        ema_9_keeps_going_up_counter = 0
        strong_bars_above_volume_average_counter = 0
        bars_above_volume_average_counter = 0
        strong_bars_counter = 0
        bars_after_strong_bars_that_continues_trend_counter = 0
        high_volume_bars_with_rejection_counter = 0
        bars_with_rejection_inside_entry_bar_range: list[common.objects.BarData] = []
        bars_with_highest_volume: list[common.objects.BarData] = []
        bars_without_movement_counter = 0
        bars_above_vwap_counter = 0

        for bar_object in one_minute_bars:
            total_volume += bar_object.volume
            is_positive = bar_object.close > bar_object.open_value
            above_volume_average = bar_object.volume > bar_object.volume_average
            has_rejection = bar_object.bar_wick_percentage >= 0.5

            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )

            if bar_object.macd < bar_object.signal_line:
                macd_under_signal_line_counter += 1

            if bar_object.bar_wick_percentage >= 0.5:
                bars_with_at_least_50_pct_wick_counter += 1

            if is_positive:
                positive_volume_sum += bar_object.volume
                positive_bars_counter += 1
                positive_movement += bar_object.close - bar_object.open_value
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_positive_bars += 1
                if bar_object.body_percentage >= 0.75:
                    strong_positive_bars_with_full_body_counter += 1
            else:
                negative_volume_sum += bar_object.volume
                negative_bars_counter += 1
                negative_movement += bar_object.open_value - bar_object.close
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_negative_bars += 1

            if previous_bar is not None:
                if bar_object.histogram < previous_bar.histogram:
                    bars_with_negative_momentum_histogram_counter += 1
                if previous_bar.ema_9 < bar_object.ema_9:
                    ema_9_keeps_going_up_counter += 1

            if (
                True
                and previous_bar is not None
                and previous_bar.volume_average > bar_object.volume_average
            ):
                bars_with_lower_volume_average_counter += 1

            if (
                True
                and above_volume_average
                and bar_object.close > bar_object.vwap
            ):
                bars_with_highest_volume.append(bar_object)

            if above_volume_average:
                bars_above_volume_average_counter += 1
                if bar_object.close/bar_object.high >= 0.9:
                    strong_bars_above_volume_average_counter += 1
                if has_rejection:
                    high_volume_bars_with_rejection_counter += 1

            if (
                True
                and is_positive
                and above_volume_average
                and bar_object.body_percentage > 0.4
                and bar_object.bar_wick_percentage <= 0.4
            ):
                strong_bars_counter += 1
                if (
                    True
                    and next_bar is not None
                    and next_bar.high >= bar_object.high * 0.995
                ):
                    bars_after_strong_bars_that_continues_trend_counter += 1

            if (
                True
                and bar_object.bar_time + datetime.timedelta(hours=1) >= potential_confirmation_bar.bar_time
                and bar_object.index - 1 > potential_confirmation_bar.index
                and potential_confirmation_bar.open_value < bar_object.high < potential_confirmation_bar.close
                and bar_object.close < potential_confirmation_bar.open_value
                and bar_object.volume > bar_object.volume_average
                and bar_object.close < bar_object.high
                and bar_object.close > bar_object.vwap
                and bar_object.close > bar_object.ema_9
                and bar_object.close > bar_object.ema_20
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high < bar_object.high
                and next_bar.high < bar_object.high
            ):
                bars_with_rejection_inside_entry_bar_range.append(bar_object)

            if round(bar_object.high, 2) == round(bar_object.low, 2):
                bars_without_movement_counter += 1

            if bar_object.close > bar_object.vwap:
                bars_above_vwap_counter += 1

        feature_bars_with_rejection_inside_entry_bar_range_pct = 0
        max_bars_since_first_breakout_attempt = 0
        if bars_with_rejection_inside_entry_bar_range:
            breakout_attempts_total_bars = len(bars_with_rejection_inside_entry_bar_range)
            max_bars_since_first_breakout_attempt = max(
                bar_object.index
                for bar_object in bars_with_rejection_inside_entry_bar_range
            ) - potential_confirmation_bar.index

            feature_bars_with_rejection_inside_entry_bar_range_pct = breakout_attempts_total_bars/max_bars_since_first_breakout_attempt

        bar_volume_close_to_entry_point_sum = 0
        bar_volume_close_to_market_open_sum = 0
        market_open_bar = one_minute_bars[-1]
        for bar_object in bars_with_highest_volume:
            if market_open_bar.index - bar_object.index < bar_object.index - potential_confirmation_bar.index:
                bar_volume_close_to_market_open_sum += bar_object.volume
            else:
                bar_volume_close_to_entry_point_sum += bar_object.volume

        pullback_analysis = DataExtractor.analyze_last_pullback(
            potential_confirmation_bar=potential_confirmation_bar,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            one_minute_bars=one_minute_bars,
        )
        minutes_since_market_open = ((potential_confirmation_bar.bar_time.hour - 9) * 60) + potential_confirmation_bar.bar_time.minute - 30

        volume_sum_from_middle_point_to_entry_point = sum(
            bar_object.volume
            for bar_object in one_minute_bars
            if bar_object.index <= potential_confirmation_bar.index + round(minutes_since_market_open/2)
        )
        volume_sum_from_market_start_to_middle_point = sum(
            bar_object.volume
            for bar_object in one_minute_bars
            if bar_object.index > potential_confirmation_bar.index + round(minutes_since_market_open/2)
        )

        feature_volume_before_middle_point_vs_after_middle_point_pct = volume_sum_from_market_start_to_middle_point/volume_sum_from_middle_point_to_entry_point
        feature_histogram_negative_momentum_pct = bars_with_negative_momentum_histogram_counter/total_bars
        feature_bars_with_at_least_50_pct_wick_pct = bars_with_at_least_50_pct_wick_counter/total_bars
        feature_strong_positive_bars_with_full_body_pct = strong_positive_bars_with_full_body_counter/positive_bars_counter if positive_bars_counter > 0 else 0
        feature_minutes_since_market_open_to_total_market_minutes_pct = minutes_since_market_open/390
        feature_bars_with_lower_volume_average_pct = bars_with_lower_volume_average_counter/total_bars
        feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = bar_volume_close_to_entry_point_sum > bar_volume_close_to_market_open_sum
        feature_macd_under_signal_line_counter = macd_under_signal_line_counter/total_bars
        feature_strong_bars_above_volume_average_pct = strong_bars_above_volume_average_counter/bars_above_volume_average_counter
        feature_strong_bars_above_volume_average_to_total_bars_pct = strong_bars_above_volume_average_counter/total_bars
        feature_bars_above_volume_average_pct = bars_above_volume_average_counter/total_bars
        feature_strong_bars_has_continuation = bars_after_strong_bars_that_continues_trend_counter/strong_bars_counter
        feature_high_volume_bars_with_rejection_pct = high_volume_bars_with_rejection_counter/bars_above_volume_average_counter
        feature_previous_bar_to_highest_high_pct = 0
        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )
        if previous_bar is not None:
            feature_previous_bar_to_highest_high_pct = previous_bar.high/highest_high_one_minute_bar.high

        feature_highest_volume_before_to_entry_bar_volume_ratio = 0
        feature_highest_average_volume_before_to_entry_bar_average_volume_ratio = 0
        feature_highest_average_volume_before_to_entry_bar_volume_ratio = 0
        volume_per_minute = volume_sum_since_market_open/minutes_since_market_open
        if len(one_minute_bars[1:]) > 0:
            feature_highest_volume_before_to_entry_bar_volume_ratio = max(
                bar_object.volume
                for bar_object in one_minute_bars[1:]
            )/potential_confirmation_bar.volume

            feature_highest_average_volume_before_to_entry_bar_average_volume_ratio = max(
                bar_object.volume_average
                for bar_object in one_minute_bars[1:]
            )/potential_confirmation_bar.volume_average

            feature_highest_average_volume_before_to_entry_bar_volume_ratio = max(
                bar_object.volume_average
                for bar_object in one_minute_bars[1:]
            )/potential_confirmation_bar.volume

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )
        bars_since_highest_high = [
            bar_object
            for bar_object in one_minute_bars[1:]
            if bar_object.bar_time > highest_high_one_minute_bar.bar_time
        ]
        strong_entry_bar_points = 0
        if potential_confirmation_bar.body_percentage >= 0.9:
            strong_entry_bar_points += 2
        if potential_confirmation_bar.volume > highest_high_one_minute_bar.volume:
            strong_entry_bar_points += 1
        if len(one_minute_bars[1:]) > 0 and potential_confirmation_bar.volume/max(bar_object.volume for bar_object in one_minute_bars[1:]) >= 0.9:
            strong_entry_bar_points += 2
        if 0.95 <= potential_confirmation_bar.ema_9/potential_confirmation_bar.low <= 1.05:
            strong_entry_bar_points += 2
        if potential_confirmation_bar.close > highest_high_one_minute_bar.high:
            strong_entry_bar_points += 1
        if previous_bar is not None and previous_bar.volume < potential_confirmation_bar.volume:
            strong_entry_bar_points += 1
        if (
            potential_confirmation_bar.open_value > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.vwap
        ):
            strong_entry_bar_points += 1
        if not any(
            bar_object
            for bar_object in bars_since_highest_high
            if bar_object.volume > bar_object.volume_average * 1.1
        ):
            strong_entry_bar_points += 1
        if potential_confirmation_bar.bar_is_solid:
            strong_entry_bar_points += 2

        feature_high_lows_pct = DataExtractor.feature_high_lows_pct(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            one_minute_bars=one_minute_bars,
        )

        crossed_any_resistance = any(
            r_l
            for r_l in day_timeframe_stock.resistance_levels
            if potential_confirmation_bar.low < r_l.close < potential_confirmation_bar.close
        )
        if not crossed_any_resistance:
            crossed_any_resistance = any(
                [
                    bar_object
                    for bar_object in one_minute_bars
                    if potential_confirmation_bar.low < bar_object.close < potential_confirmation_bar.close
                ]
            )

        bars_closed_under_ema_20_since_highest_high = [
            bar_object
            for bar_object in bars_since_highest_high
            if bar_object.close < bar_object.ema_20
        ]
        min_volume_average_since_highest_high = 0
        max_volume_average_since_highest_high = 0

        if bars_since_highest_high:
            min_volume_average_since_highest_high = min(
                bar_object.volume_average
                for bar_object in bars_since_highest_high
            )
            max_volume_average_since_highest_high = max(
                bar_object.volume_average
                for bar_object in bars_since_highest_high
            )

        volume_to_volume_average_ratio_since_highest_high = 0
        for bar_object in bars_since_highest_high:
            volume_to_volume_average_ratio_since_highest_high += bar_object.volume/bar_object.volume_average

        feature_ema_9_has_been_tested_since_highest_high = False
        for bar_object in bars_since_highest_high:
            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )

            if (
                True
                and previous_bar is not None
                and previous_bar.ema_9 < bar_object.ema_9
            ):
                feature_ema_9_has_been_tested_since_highest_high = True
                break

        last_10_bars = [
            bar_object
            for bar_object
            in one_minute_bars
            if bar_object.bar_time + datetime.timedelta(minutes=10) > potential_confirmation_bar.bar_time
        ]

        last_10_bars_range_average = sum(
            bar_object.high - bar_object.low
            for bar_object in last_10_bars
        )/len(last_10_bars)

        feature_weak_bars_since_highest_high_to_total_pct = len(
            [
                bar_object
                for bar_object in bars_since_highest_high
                if bar_object.ema_9 < bar_object.vwap
                and bar_object.close < bar_object.vwap
                and bar_object.volume/bar_object.volume_average <= 1.1
            ]
        )/len(bars_since_highest_high) if bars_since_highest_high else 0

        feature_bars_since_highest_high_to_total_bars_pct = len(bars_since_highest_high)/total_bars
        feature_weak_bars_to_bars_since_highest_high_to_total_bars = feature_weak_bars_since_highest_high_to_total_pct/feature_bars_since_highest_high_to_total_bars_pct if feature_bars_since_highest_high_to_total_bars_pct > 0 else 0

        features = {
            "feature_has_positive_more_than_negative_bars": positive_bars_counter > negative_bars_counter,
            "feature_pullback_sharpness": pullback_analysis["feature_pullback_sharpness"],
            "feature_pullback_depth": pullback_analysis["feature_pullback_depth"],
            "feature_number_of_negative_bars_in_pullback_pct": pullback_analysis["feature_number_of_negative_bars_in_pullback_pct"],
            "feature_price_minus_vwap_at_entry": potential_confirmation_bar.close - potential_confirmation_bar.vwap,
            "feature_pullback_to_trend_ratio": pullback_analysis["feature_pullback_to_trend_ratio"],
            "feature_histogram_negative_momentum_pct": feature_histogram_negative_momentum_pct,
            "feature_strong_positive_bars_with_full_body_pct": feature_strong_positive_bars_with_full_body_pct,
            "feature_minutes_since_market_open_to_total_market_minutes_pct": feature_minutes_since_market_open_to_total_market_minutes_pct,
            "feature_bars_with_at_least_50_pct_wick_pct": feature_bars_with_at_least_50_pct_wick_pct,
            "feature_bars_with_lower_volume_average_pct": feature_bars_with_lower_volume_average_pct,
            "feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open": feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open,
            "feature_highest_volume_before_to_entry_bar_volume_ratio": feature_highest_volume_before_to_entry_bar_volume_ratio,
            "feature_highest_average_volume_before_to_entry_bar_average_volume_ratio": feature_highest_average_volume_before_to_entry_bar_average_volume_ratio,
            "feature_highest_average_volume_before_to_entry_bar_volume_ratio": feature_highest_average_volume_before_to_entry_bar_volume_ratio,
            "feature_macd_under_signal_line_counter": feature_macd_under_signal_line_counter,
            "feature_entry_bar_strengh_pct": strong_entry_bar_points / 13,
            "feature_ema_9_keeps_going_up_pct": ema_9_keeps_going_up_counter/total_bars,
            "feature_strong_bars_above_volume_average_pct": feature_strong_bars_above_volume_average_pct,
            "feature_strong_bars_above_volume_average_to_total_bars_pct": feature_strong_bars_above_volume_average_to_total_bars_pct,
            "feature_bars_above_volume_average_pct": feature_bars_above_volume_average_pct,
            "feature_strong_bars_has_continuation": feature_strong_bars_has_continuation,
            "feature_high_volume_bars_with_rejection_pct": feature_high_volume_bars_with_rejection_pct,
            "feature_previous_bar_to_highest_high_pct": feature_previous_bar_to_highest_high_pct,
            "feature_bar_volume_to_volume_sum_since_market_open": potential_confirmation_bar.volume/(volume_sum_since_market_open - potential_confirmation_bar.volume),
            "feature_volume_average_to_bar_volume": potential_confirmation_bar.volume_average/potential_confirmation_bar.volume,
            "feature_volume_per_minute_to_bar_volume": round(volume_per_minute, 2)/potential_confirmation_bar.volume,
            "feature_high_lows_pct": feature_high_lows_pct,
            "feature_bars_with_rejection_inside_entry_bar_range_pct": feature_bars_with_rejection_inside_entry_bar_range_pct,
            "feature_positive_vs_negative_volume": positive_volume_sum/negative_volume_sum if negative_volume_sum > 0 else 1,
            "feature_positive_vs_negative_movement": positive_movement/negative_movement if negative_movement > 0 else 1,
            "feature_volume_before_middle_point_vs_after_middle_point_pct": feature_volume_before_middle_point_vs_after_middle_point_pct,
            "feature_bars_without_movement_pct": bars_without_movement_counter/total_bars,
            "feature_last_negative_to_positive_bars_pct": last_bars_negative_bars/last_bars_positive_bars if last_bars_positive_bars > 0 else 0,
            "feature_crossed_any_resistance": crossed_any_resistance,
            "feature_bars_above_vwap_pct": bars_above_vwap_counter/total_bars,
            "feature_entry_bar_profit_pct": (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/potential_confirmation_bar.open_value,
            "feature_entry_bar_volume_to_highest_bar_volume_pct": potential_confirmation_bar.volume/highest_high_one_minute_bar.volume,
            "feature_previous_bar_volume_to_entry_bar_volume_pct": previous_bar.volume/potential_confirmation_bar.volume if previous_bar is not None else 0,
            "feature_bars_closed_under_ema_20_since_highest_high_bar_pct": len(bars_closed_under_ema_20_since_highest_high)/(highest_high_one_minute_bar.index - potential_confirmation_bar.index),
            "feature_volume_average_change_since_highest_high_pct": min_volume_average_since_highest_high/max_volume_average_since_highest_high if max_volume_average_since_highest_high > 0 else 0,
            "feature_volume_to_volume_average_ratio_since_highest_high": volume_to_volume_average_ratio_since_highest_high/len(bars_since_highest_high) if len(bars_since_highest_high) > 0 else 0,
            "feature_entry_bar_volume_is_highest_until_now": max(bar_object.volume for bar_object in one_minute_bars) == potential_confirmation_bar.volume,
            "feature_ema_9_has_been_tested_since_highest_high": feature_ema_9_has_been_tested_since_highest_high,
            "feature_entry_strength_vs_avg": (potential_confirmation_bar.high - potential_confirmation_bar.low)/last_10_bars_range_average,
            "feature_weak_bars_since_highest_high_to_total_pct": feature_weak_bars_since_highest_high_to_total_pct,
            "feature_bars_since_highest_high_to_total_bars_pct": feature_bars_since_highest_high_to_total_bars_pct,
            "feature_weak_bars_to_bars_since_highest_high_to_total_bars": feature_weak_bars_to_bars_since_highest_high_to_total_bars,
        }

        return features
