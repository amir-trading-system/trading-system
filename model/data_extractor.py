import datetime

import common


class DataExtractor:
    @staticmethod
    def overlapped_bars_since_market_open_pct(
        one_minute_timeframe_stock: common.objects.Stock,
        one_minute_bars: list[common.objects.BarData],
    ) -> float:
        overlapped_bars_counter = 0

        for bar_object in one_minute_bars:
            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )

            if (
                True
                and previous_bar is not None
                and bar_object.volume > bar_object.volume_average
                and previous_bar.low <= bar_object.open_value <= previous_bar.high
                and previous_bar.low <= bar_object.close <= previous_bar.high
            ):
                overlapped_bars_counter += 1

        return overlapped_bars_counter/len(one_minute_bars)

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
        positive_histograms_sum = 0
        negative_histograms_sum = 0

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
        bars_ema_above_vwap_counter = 0
        positive_bars_close_strong_counter = 0
        volume_average_goes_up_counter = 0
        volume_avergae_above_10000_counter = 0

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

            if bar_object.volume_average > 10000:
                volume_avergae_above_10000_counter += 1

            if bar_object.histogram > 0:
                positive_histograms_sum += bar_object.histogram
            else:
                negative_histograms_sum += abs(bar_object.histogram)

            if is_positive:
                positive_volume_sum += bar_object.volume
                positive_bars_counter += 1
                positive_movement += bar_object.close - bar_object.open_value
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_positive_bars += 1
                if bar_object.body_percentage >= 0.75:
                    strong_positive_bars_with_full_body_counter += 1
                if bar_object.bar_wick_percentage <= 0.1:
                    positive_bars_close_strong_counter += 1
            else:
                negative_volume_sum += bar_object.volume
                negative_bars_counter += 1
                negative_movement += bar_object.open_value - bar_object.close
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_negative_bars += 1

            if previous_bar is not None:
                if previous_bar.volume_average < bar_object.volume_average:
                    volume_average_goes_up_counter += 1

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

            if (
                True
                and bar_object.ema_9 > bar_object.vwap
                and bar_object.ema_20 > bar_object.vwap
                and bar_object.ema_9 >= bar_object.ema_20
            ):
                bars_ema_above_vwap_counter += 1

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
        feature_bars_with_lower_volume_average_pct = bars_with_lower_volume_average_counter/total_bars
        feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = bar_volume_close_to_entry_point_sum > bar_volume_close_to_market_open_sum
        feature_strong_bars_above_volume_average_pct = strong_bars_above_volume_average_counter/bars_above_volume_average_counter
        feature_high_volume_bars_with_rejection_pct = high_volume_bars_with_rejection_counter/bars_above_volume_average_counter
        volume_per_minute = volume_sum_since_market_open/minutes_since_market_open if minutes_since_market_open > 0 else 1

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

        volume_to_volume_average_ratio_since_highest_high = 0
        for bar_object in bars_since_highest_high:
            volume_to_volume_average_ratio_since_highest_high += bar_object.volume/bar_object.volume_average

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

        feature_volume_average_goes_up_pct = volume_average_goes_up_counter/total_bars
        feature_overlapped_bars_since_market_open_pct = DataExtractor.overlapped_bars_since_market_open_pct(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            one_minute_bars=one_minute_bars,
        )
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

        feature_crossed_highest_high = (
            True
            and potential_confirmation_bar.low < highest_high_one_minute_bar.high < potential_confirmation_bar.high
            and (potential_confirmation_bar.high - highest_high_one_minute_bar.high)/(potential_confirmation_bar.high - potential_confirmation_bar.low) > 0.3
            and potential_confirmation_bar.low/potential_confirmation_bar.open_value >= 0.95
            and potential_confirmation_bar.body_percentage > 0.5
            and volume_sum_since_market_open > 500000
            and not any(
                bar_object
                for bar_object in one_minute_bars[1:10]
                if abs(bar_object.close - bar_object.open_value) > potential_confirmation_bar.close - potential_confirmation_bar.open_value
                and bar_object.volume/potential_confirmation_bar.volume > 0.95
            )
        )

        highest_high_bar_since_market_open = None
        for bar_object in one_minute_bars[1:]:
            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )
            if (
                previous_bar is not None
                and next_bar is not None
                and bar_object.high >= previous_bar.high
                and bar_object.high > next_bar.high
                and bar_object.volume > bar_object.volume_average
            ):
                if (
                    highest_high_bar_since_market_open is None
                    or (
                        highest_high_bar_since_market_open is not None
                        and bar_object.high > highest_high_bar_since_market_open.high
                    )
                ):
                    highest_high_bar_since_market_open = bar_object

        feature_is_there_highest_high_after_market_open = highest_high_bar_since_market_open is not None
        feature_distance_from_highest_high_since_market_open = highest_high_bar_since_market_open.index if highest_high_bar_since_market_open is not None else 0
        feature_crossed_highest_high_since_market_open = (
            True
            and highest_high_bar_since_market_open is not None
            and potential_confirmation_bar.low < highest_high_bar_since_market_open.high < potential_confirmation_bar.close
            and highest_high_bar_since_market_open.index <= 60
            and (potential_confirmation_bar.close - highest_high_bar_since_market_open.high)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value) >= 0.25
        )

        features = {
            "feature_has_positive_more_than_negative_bars": positive_bars_counter > negative_bars_counter,
            "feature_price_minus_vwap_at_entry": potential_confirmation_bar.close - potential_confirmation_bar.vwap,
            "feature_histogram_negative_momentum_pct": feature_histogram_negative_momentum_pct,
            "feature_bars_with_at_least_50_pct_wick_pct": feature_bars_with_at_least_50_pct_wick_pct,
            "feature_bars_with_lower_volume_average_pct": feature_bars_with_lower_volume_average_pct,
            "feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open": feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open,
            "feature_entry_bar_strengh_pct": strong_entry_bar_points / 13,
            "feature_strong_bars_above_volume_average_pct": feature_strong_bars_above_volume_average_pct,
            "feature_high_volume_bars_with_rejection_pct": feature_high_volume_bars_with_rejection_pct,
            "feature_volume_per_minute_to_bar_volume": round(volume_per_minute, 2)/potential_confirmation_bar.volume,
            "feature_volume_per_minute_to_bar_volume_above_threshold": round(volume_per_minute, 2)/potential_confirmation_bar.volume > 0.2,
            "feature_bars_with_rejection_inside_entry_bar_range_pct": feature_bars_with_rejection_inside_entry_bar_range_pct,
            "feature_positive_vs_negative_volume": positive_volume_sum/negative_volume_sum if negative_volume_sum > 0 else 1,
            "feature_positive_vs_negative_movement": positive_movement/negative_movement if negative_movement > 0 else 1,
            "feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold": feature_volume_before_middle_point_vs_after_middle_point_pct > 0.2,
            "feature_bars_without_movement_pct_above_threshold": bars_without_movement_counter/total_bars > 0.02,
            "feature_entry_strength_vs_avg": (potential_confirmation_bar.high - potential_confirmation_bar.low)/last_10_bars_range_average,
            "feature_potential_bar_low_close_to_open": potential_confirmation_bar.low/potential_confirmation_bar.open_value >= 0.99,
            "feature_volume_average_goes_up_pct": feature_volume_average_goes_up_pct,
            "feature_overlapped_bars_since_market_open_pct": feature_overlapped_bars_since_market_open_pct,
            "feature_weak_bars_to_bars_since_highest_high_to_total_bars": feature_weak_bars_to_bars_since_highest_high_to_total_bars,
            "feature_crossed_highest_high": feature_crossed_highest_high,
            "feature_entry_bar_volume_average_above_threshold": potential_confirmation_bar.volume_average > 50000,
            "feature_volume_avergae_above_10000_pct_above_threshold": volume_avergae_above_10000_counter/total_bars >= 0.8,
            "feature_is_there_highest_high_after_market_open": feature_is_there_highest_high_after_market_open,
            "feature_distance_from_highest_high_since_market_open": feature_distance_from_highest_high_since_market_open,
            "feature_crossed_highest_high_since_market_open": feature_crossed_highest_high_since_market_open,
            "feature_entry_bar_lowest_wick_to_bar_body_pct": (potential_confirmation_bar.open_value - potential_confirmation_bar.low)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value)
        }

        return features
