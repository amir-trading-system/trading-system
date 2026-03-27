import common


class DataExtractor:
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

        positive_bars_counter = 0
        negative_bars_counter = 0

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
        bars_with_highest_volume: list[common.objects.BarData] = []

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
                if bar_object.body_percentage >= 0.75:
                    strong_positive_bars_with_full_body_counter += 1
            else:
                negative_volume_sum += bar_object.volume
                negative_bars_counter += 1

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

        last_3_bars_profit_gain_avg = 0
        if len(one_minute_bars) > 3:
            last_3_bars_profit_gain_avg = sum(
                bar_object.high - bar_object.low
                for bar_object in one_minute_bars[:3]
            )/len(one_minute_bars[:3])

        entry_range = potential_confirmation_bar.high - potential_confirmation_bar.low

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
        feature_extension_from_vwap = (potential_confirmation_bar.close - potential_confirmation_bar.vwap)/potential_confirmation_bar.vwap
        feature_distance_from_highest_high = (potential_confirmation_bar.close - highest_high_one_minute_bar.high)/highest_high_one_minute_bar.high
        feature_entry_exaustion = entry_range/last_3_bars_profit_gain_avg if last_3_bars_profit_gain_avg > 0 else 0
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
        if (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.9:
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
            "feature_volume_sum_since_market_open": volume_sum_since_market_open,
            "feature_highest_volume_before_to_entry_bar_volume_ratio": feature_highest_volume_before_to_entry_bar_volume_ratio,
            "feature_highest_average_volume_before_to_entry_bar_average_volume_ratio": feature_highest_average_volume_before_to_entry_bar_average_volume_ratio,
            "feature_highest_average_volume_before_to_entry_bar_volume_ratio": feature_highest_average_volume_before_to_entry_bar_volume_ratio,
            "feature_macd_under_signal_line_counter": feature_macd_under_signal_line_counter,
            "feature_entry_bar_strengh_pct": strong_entry_bar_points / 11,
            "feature_ema_9_keeps_going_up_pct": ema_9_keeps_going_up_counter/total_bars,
            "feature_strong_bars_above_volume_average_pct": feature_strong_bars_above_volume_average_pct,
            "feature_strong_bars_above_volume_average_to_total_bars_pct": feature_strong_bars_above_volume_average_to_total_bars_pct,
            "feature_bars_above_volume_average_pct": feature_bars_above_volume_average_pct,
            "feature_strong_bars_has_continuation": feature_strong_bars_has_continuation,
            "feature_high_volume_bars_with_rejection_pct": feature_high_volume_bars_with_rejection_pct,
            "feature_extension_from_vwap": feature_extension_from_vwap,
            "feature_distance_from_highest_high": feature_distance_from_highest_high,
            "feature_entry_exaustion": feature_entry_exaustion,
            "feature_previous_bar_to_highest_high_pct": feature_previous_bar_to_highest_high_pct,
            "feature_bar_volume_to_volume_sum_since_market_open": potential_confirmation_bar.volume/(volume_sum_since_market_open - potential_confirmation_bar.volume),
            "feature_volume_average_to_bar_volume": potential_confirmation_bar.volume_average/potential_confirmation_bar.volume,
            "feature_volume_per_minute_to_bar_volume": round(volume_per_minute, 2)/potential_confirmation_bar.volume,
        }

        return features
