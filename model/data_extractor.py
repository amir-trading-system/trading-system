import datetime

import common

class DataExtractor:
    def recent_days_structure_features(
        self,
        day_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> dict[str, float]:
        current_day = day_timeframe_stock.bars[0]
        previous_day = day_timeframe_stock.bars[1]
        recent_days = day_timeframe_stock.bars[1:10]
        total_days = len(recent_days)

        volume_sum = 0
        ema_9_sum = 0
        ema_20_sum = 0
        vwap_sum = 0
        movement_sum = 0
        ema_9_to_ema_20_distance_sum = 0
        highs_sum = 0

        for day in recent_days:
            volume_sum += day.volume
            ema_9_sum += day.ema_9
            ema_20_sum += day.ema_20
            vwap_sum += day.vwap
            movement_sum += day.high - day.low
            ema_9_to_ema_20_distance_sum += day.ema_9 - day.ema_20
            highs_sum += day.high

        recent_days_volume_average = volume_sum/total_days
        ema_9_average = ema_9_sum/total_days
        ema_20_average = ema_20_sum/total_days
        movement_average = movement_sum/total_days
        ema_9_to_ema_20_distance_average = ema_9_to_ema_20_distance_sum/total_days
        highs_average = highs_sum/total_days
        vwap_average = vwap_sum/total_days

        current_day_volume_to_recent_days_volume = current_day.volume/recent_days_volume_average if recent_days_volume_average > 0 else 1
        current_day_ema_9_to_recent_days_ema_9 = current_day.ema_9/ema_9_average if ema_9_average > 0 else 1
        current_day_ema_20_to_recent_days_ema_20 = current_day.ema_20/ema_20_average if ema_20_average > 0 else 1
        current_day_movement_to_recent_days_movement = (potential_confirmation_bar.high - current_day.low)/movement_average if movement_average > 0 else 1
        current_day_ema_9_to_ema_20_distance_to_recent_days = (current_day.ema_9 - current_day.ema_20)/ema_9_to_ema_20_distance_average if ema_9_to_ema_20_distance_average > 0 else 1
        current_day_high_to_recent_days_highs = potential_confirmation_bar.high/highs_average if highs_average > 0 else 1
        current_day_vwap_to_recent_days = current_day.vwap/vwap_average if vwap_average > 0 else 1
        current_day_low_to_ema_9 = current_day.low/current_day.ema_9 if current_day.ema_9 > 0 else 1
        current_day_ema_9_to_ema_20 = current_day.ema_9/current_day.ema_20 if current_day.ema_20 > 0 else 1
        current_day_high_to_previous_high = potential_confirmation_bar.high/previous_day.high if previous_day.high > 0 else 1
        gains_until_entry_bar = (potential_confirmation_bar.close - previous_day.close)/previous_day.close if previous_day is not None and previous_day.high > 0 else 1
        controlled_volume_entry_quality = current_day_volume_to_recent_days_volume/ (1.0 + gains_until_entry_bar)

        return {
            "feature_current_day_volume_to_recent_days_volume": current_day_volume_to_recent_days_volume,
            "feature_current_day_ema_9_to_recent_days_ema_9": current_day_ema_9_to_recent_days_ema_9,
            "feature_current_day_ema_20_to_recent_days_ema_20": current_day_ema_20_to_recent_days_ema_20,
            "feature_current_day_vwap_to_recent_days": current_day_vwap_to_recent_days,
            "feature_current_day_movement_to_recent_days_movement": current_day_movement_to_recent_days_movement,
            "feature_current_day_ema_9_to_ema_20_distance_to_recent_days": current_day_ema_9_to_ema_20_distance_to_recent_days,
            "feature_current_day_high_to_recent_days_highs": current_day_high_to_recent_days_highs,
            "feature_current_day_low_to_ema_9": current_day_low_to_ema_9,
            "feature_current_day_ema_9_to_ema_20": current_day_ema_9_to_ema_20,
            "feature_current_day_high_to_previous_high": current_day_high_to_previous_high,
            "feature_gains_until_entry_bar": gains_until_entry_bar,
            "feature_controlled_volume_entry_quality": controlled_volume_entry_quality,
        }

    def breakout_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        bars_since_highest_high: list[common.objects.BarData],
        highest_high_one_minute_bar: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, float]:
        entry_bar_close_to_highest_high = potential_confirmation_bar.close/highest_high_one_minute_bar.high
        entry_bar_body = potential_confirmation_bar.body_percentage
        entry_bar_upper_wick = potential_confirmation_bar.bar_wick_percentage
        entry_bar_lower_wick = potential_confirmation_bar.bar_lower_wick_percentage
        entry_bar_low_to_ema_9 = potential_confirmation_bar.low/potential_confirmation_bar.ema_9
        entry_bar_ema_9_to_ema_20 = potential_confirmation_bar.ema_9/potential_confirmation_bar.ema_20
        entry_bar_ema_9_to_vwap = potential_confirmation_bar.ema_9/potential_confirmation_bar.vwap
        distance_from_highest_high = highest_high_one_minute_bar.index - potential_confirmation_bar.index
        price_action_from_highest_high = potential_confirmation_bar.high - highest_high_one_minute_bar.high
        price_action_from_ema_9 = potential_confirmation_bar.high - potential_confirmation_bar.ema_9

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        two_bars_back = one_minute_timeframe_stock.previous_bar(
            bar_object=previous_bar,
        ) if previous_bar is not None else None

        previous_bar_volume_to_its_previous_volume = two_bars_back.volume/previous_bar.volume if two_bars_back is not None and previous_bar is not None else 0
        previous_bar_high_to_highest_high = previous_bar.high/highest_high_one_minute_bar.high if previous_bar is not None and highest_high_one_minute_bar is not None else 0
        previous_bar_close_to_highest_high = previous_bar.close/highest_high_one_minute_bar.high if previous_bar is not None and highest_high_one_minute_bar is not None else 0
        previous_bar_already_crossed_highest_high = 1 if previous_bar.low < highest_high_one_minute_bar.high < previous_bar.close and previous_bar is not None else 0

        bars_movement = 0
        lowest_low_since_highest_high = 100
        lowest_low_bar = None
        total_bars_since_highest_high = len(bars_since_highest_high)
        breakout_attempts_during_pullback = 0
        body_size_of_pullback_bars = 0
        bar_wick_of_pullback_bars = 0
        total_volume_since_highest_high = 0
        for bar_object in bars_since_highest_high:
            total_volume_since_highest_high += bar_object.volume
            bars_movement += bar_object.high - bar_object.close
            body_size_of_pullback_bars += abs(bar_object.close - bar_object.open_value)
            if bar_object.is_positive:
                bar_wick_of_pullback_bars += (bar_object.high - bar_object.close)/(bar_object.high - bar_object.low) if (bar_object.high - bar_object.low) > 0 else 0
            else:
                bar_wick_of_pullback_bars += (bar_object.high - bar_object.open_value)/(bar_object.high - bar_object.low) if (bar_object.high - bar_object.low) > 0 else 0

            if bar_object.low < lowest_low_since_highest_high:
                lowest_low_since_highest_high = bar_object.low
                lowest_low_bar = bar_object

            if (
                True
                and bar_object.high/highest_high_one_minute_bar.high > 0.99
                and bar_object.volume > bar_object.volume_average
            ):
                breakout_attempts_during_pullback += 1

        bars_movement_average = 0
        if bars_since_highest_high:
            bars_movement_average = bars_movement/total_bars_since_highest_high

        entry_bar_movement_recent_bars_average = (potential_confirmation_bar.high - potential_confirmation_bar.low)/bars_movement_average if bars_movement_average > 0 else 1
        entry_extension_pressure = entry_bar_ema_9_to_vwap / (entry_bar_movement_recent_bars_average + 1e-6)
        crossed_at_least_one_bar_from_recent_bars = any(
            bar_object
            for bar_object in bars_since_highest_high[1:6]
            if potential_confirmation_bar.low < bar_object.high < potential_confirmation_bar.close
        )

        volume_since_lowest_low = 0
        if lowest_low_bar is not None:
            bars_since_lowest_low = [
                bar_object
                for bar_object in bars_since_highest_high
                if bar_object.index <= lowest_low_bar.index
            ]
            if bars_since_lowest_low:
                volume_since_lowest_low = sum(
                    bar_object.volume
                    for bar_object in bars_since_lowest_low
                )

        last_10_bars = one_minute_bars[1:11]
        keep_up_trend_bars = 0
        positive_bars = 0
        ema_9_to_ema_20_distances = 0
        for bar_object in last_10_bars:
            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object
            )
            ema_9_to_ema_20_distances += bar_object.ema_9 - bar_object.ema_20
            if (
                True
                and previous_bar is not None
                and previous_bar.low < bar_object.low
            ):
                keep_up_trend_bars += 1

            if bar_object.is_positive:
                positive_bars += 1

        feature_recent_bars_up_trend_pct = keep_up_trend_bars/len(last_10_bars)
        feature_recent_bars_positive_bars_pct = positive_bars/len(last_10_bars)

        body_size_of_pullback_bars_average = body_size_of_pullback_bars/len(bars_since_highest_high) if len(bars_since_highest_high) > 0 else 0
        bar_wick_of_pullback_bars_average = bar_wick_of_pullback_bars/len(bars_since_highest_high) if len(bars_since_highest_high) > 0 else 0
        entry_body_to_recent_bars_body_average = abs(potential_confirmation_bar.close - potential_confirmation_bar.open_value)/body_size_of_pullback_bars_average if body_size_of_pullback_bars_average > 0 else 1
        entry_upper_wick_to_recent_upper_wick_average = potential_confirmation_bar.bar_wick_percentage/bar_wick_of_pullback_bars_average if bar_wick_of_pullback_bars_average > 0 else 1
        pullback_depth_vs_pre_high_move = (highest_high_one_minute_bar.high - lowest_low_since_highest_high) / (highest_high_one_minute_bar.high - highest_high_one_minute_bar.ema_9) if highest_high_one_minute_bar is not None else 0

        highest_high_body = (
            abs(highest_high_one_minute_bar.close - highest_high_one_minute_bar.open_value)
            if highest_high_one_minute_bar is not None
            else 0
        )
        entry_body = potential_confirmation_bar.close - potential_confirmation_bar.open_value
        feature_entry_body_to_highest_high_body = (
            entry_body / highest_high_body
            if highest_high_one_minute_bar is not None and highest_high_body != 0
            else 0
        )

        entry_range = potential_confirmation_bar.high - potential_confirmation_bar.low
        entry_close_strength = (
            (potential_confirmation_bar.close - potential_confirmation_bar.low) / entry_range
            if entry_range != 0
            else 0
        )
        highest_high_range = (
            highest_high_one_minute_bar.high - highest_high_one_minute_bar.low
            if highest_high_one_minute_bar is not None
            else 0
        )
        highest_high_close_strength = (
            (highest_high_one_minute_bar.close - highest_high_one_minute_bar.low) / highest_high_range
            if highest_high_one_minute_bar is not None and highest_high_range != 0
            else 0
        )
        feature_entry_close_strength_to_highest_high_close_strength = (
            entry_close_strength / highest_high_close_strength
            if highest_high_one_minute_bar is not None and highest_high_close_strength != 0
            else 0
        )
        entry_close_strength = (potential_confirmation_bar.close - potential_confirmation_bar.low) / (potential_confirmation_bar.high - potential_confirmation_bar.low) if (potential_confirmation_bar.high - potential_confirmation_bar.low) > 0 else 0
        previous_close_strength = (previous_bar.close - previous_bar.low) / (previous_bar.high - previous_bar.low) if previous_bar is not None and (previous_bar.high - previous_bar.low) > 0 else 0

        feature_entry_close_position_vs_previous_close_position = entry_close_strength / previous_close_strength if previous_close_strength > 0 else 1
        feature_lowest_low_to_entry_elapsed_minutes = lowest_low_bar.index - potential_confirmation_bar.index if lowest_low_bar is not None else 0
        feature_entry_close_to_lowest_low_recovery = (potential_confirmation_bar.close - lowest_low_bar.low) / (highest_high_one_minute_bar.high - lowest_low_bar.low) if highest_high_one_minute_bar is not None and lowest_low_bar is not None and (highest_high_one_minute_bar.high - lowest_low_bar.low) > 0 else 1

        return {
            "entry_bar_volume": potential_confirmation_bar.volume,
            "feature_entry_bar_close_to_highest_high": entry_bar_close_to_highest_high,
            "feature_entry_bar_body": entry_bar_body,
            "feature_entry_bar_upper_wick": entry_bar_upper_wick,
            "feature_entry_bar_lower_wick": entry_bar_lower_wick,
            "feature_entry_bar_low_to_ema_9": entry_bar_low_to_ema_9,
            "feature_entry_bar_ema_9_to_ema_20": entry_bar_ema_9_to_ema_20,
            "feature_entry_bar_ema_9_to_vwap": entry_bar_ema_9_to_vwap,
            "feature_distance_from_highest_high": distance_from_highest_high,
            "feature_entry_bar_movement_recent_bars_average": entry_bar_movement_recent_bars_average,
            "feature_entry_extension_pressure": entry_extension_pressure,
            "feature_breakout_attempts_during_pullback": breakout_attempts_during_pullback,
            "feature_entry_breakout_efficiency_from_ema_9": price_action_from_highest_high/price_action_from_ema_9 if price_action_from_ema_9 > 0 else 0,
            "feature_previous_bar_already_crossed_highest_high": previous_bar_already_crossed_highest_high,
            "feature_crossed_at_least_one_bar_from_recent_bars": crossed_at_least_one_bar_from_recent_bars,
            "feature_failed_attempts_pressure": breakout_attempts_during_pullback * entry_extension_pressure,
            "feature_price_movement_from_highest_high_to_lowest_low": highest_high_one_minute_bar.high - lowest_low_since_highest_high if highest_high_one_minute_bar is not None else 0,
            "feature_previous_bar_volume_to_its_previous_volume": previous_bar_volume_to_its_previous_volume,
            "feature_previous_bar_high_to_highest_high": previous_bar_high_to_highest_high,
            "feature_previous_bar_close_to_highest_high": previous_bar_close_to_highest_high,
            "feature_entry_close_to_previous_bar_high": potential_confirmation_bar.close/previous_bar.high if previous_bar is not None else 1,
            "feature_reclaim_close_strength_since_highest_high": (potential_confirmation_bar.close - highest_high_one_minute_bar.high) / (potential_confirmation_bar.high - potential_confirmation_bar.low) if highest_high_one_minute_bar is not None and (potential_confirmation_bar.high - potential_confirmation_bar.low) > 0 else 0,
            "feature_entry_body_to_recent_bars_body_average": entry_body_to_recent_bars_body_average,
            "feature_entry_upper_wick_to_recent_upper_wick_average": entry_upper_wick_to_recent_upper_wick_average,
            "feature_pullback_depth_vs_pre_high_move": pullback_depth_vs_pre_high_move,
            "feature_bars_since_lowest_low_to_entry": lowest_low_bar.index - potential_confirmation_bar.index if lowest_low_bar is not None else 0,
            "feature_volume_since_lowest_low_to_entry_vs_since_highest_high": volume_since_lowest_low/total_volume_since_highest_high if total_volume_since_highest_high > 0 else 0,
            "feature_entry_close_to_vwap": potential_confirmation_bar.close/potential_confirmation_bar.vwap,
            "feature_entry_body_to_highest_high_body": feature_entry_body_to_highest_high_body,
            "feature_entry_close_strength_to_highest_high_close_strength": feature_entry_close_strength_to_highest_high_close_strength,
            "feature_recent_bars_up_trend_pct": feature_recent_bars_up_trend_pct,
            "feature_entry_close_to_previous_bar_close": potential_confirmation_bar.close/previous_bar.close if previous_bar is not None else 1,
            "feature_entry_body_to_previous_bar_body": (potential_confirmation_bar.close - potential_confirmation_bar.open_value) / abs(previous_bar.close - previous_bar.open_value) if previous_bar is not None and abs(previous_bar.close - previous_bar.open_value) > 0 else 1,
            "feature_entry_close_position_vs_previous_close_position": feature_entry_close_position_vs_previous_close_position,
            "feature_highest_high_to_entry_elapsed_minutes": highest_high_one_minute_bar.index - potential_confirmation_bar.index if highest_high_one_minute_bar is not None else 0,
            "feature_lowest_low_to_entry_elapsed_minutes": feature_lowest_low_to_entry_elapsed_minutes,
            "feature_entry_close_to_lowest_low_recovery": feature_entry_close_to_lowest_low_recovery,
            "feature_reclaim_speed_from_lowest_low": feature_entry_close_to_lowest_low_recovery/feature_lowest_low_to_entry_elapsed_minutes if feature_lowest_low_to_entry_elapsed_minutes > 0 else 0,
            "feature_gains_since_lowest_low": (potential_confirmation_bar.high - lowest_low_bar.low)/lowest_low_bar.low if lowest_low_bar is not None else 0,
            "feature_recent_bars_positive_bars_pct": feature_recent_bars_positive_bars_pct,
            "feature_entry_bar_vwap_to_ema_20": potential_confirmation_bar.vwap/potential_confirmation_bar.ema_20 if potential_confirmation_bar.ema_20 > 0 else 1,
            "feature_emas_distances_to_recent_bars_ema_distances": (potential_confirmation_bar.ema_9-potential_confirmation_bar.ema_20)/ema_9_to_ema_20_distances if ema_9_to_ema_20_distances > 0 else 1,
        }

    def volume_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        highest_high_one_minute_bar: common.objects.BarData,
        bars_since_highest_high: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> dict[str, float]:
        highest_volume_since_highest_high = 0
        total_bars_since_highest_high = len(bars_since_highest_high)
        volume_since_highest_high = 0
        volume_before_highest_high = 0
        bars_before_highest_high = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if (
                bar_object.is_after_market_open
                or bar_object.is_opening_bar
            )
            and highest_high_one_minute_bar is not None
            and bar_object.bar_time < highest_high_one_minute_bar.bar_time
        ]
        if bars_before_highest_high:
            volume_before_highest_high = sum(
                bar_object.volume
                for bar_object in bars_before_highest_high
            )

        positive_volume = 0
        negative_volume = 0
        bars_above_volume_average = 0
        bars_under_volume_average = 0
        for bar_object in bars_since_highest_high:
            volume_since_highest_high += bar_object.volume

            if bar_object.is_positive:
                positive_volume += bar_object.volume
            else:
                negative_volume += bar_object.volume

            if 0.98 <= bar_object.volume/bar_object.volume_average:
                bars_above_volume_average += 1
            else:
                bars_under_volume_average += 1

        volume_average = 0
        if bars_since_highest_high:
            highest_volume_since_highest_high = max(
                bar_object.volume
                for bar_object in bars_since_highest_high
            )
            volume_average = volume_since_highest_high/total_bars_since_highest_high

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        entry_bar_volume_to_highest_volume_in_pullback = potential_confirmation_bar.volume/highest_volume_since_highest_high if highest_volume_since_highest_high > 0 else 1
        entry_bar_volume_to_volume_average = potential_confirmation_bar.volume/potential_confirmation_bar.volume_average
        entry_bar_volume_to_previous_bar_volume = potential_confirmation_bar.volume/previous_bar.volume if previous_bar is not None else 1
        entry_bar_volume_to_highest_high_volume = potential_confirmation_bar.volume/highest_high_one_minute_bar.volume
        positive_vs_negative_volume_during_pullback = positive_volume/negative_volume if negative_volume > 0 else 1

        return {
            "feature_entry_bar_volume_to_highest_volume_in_pullback": entry_bar_volume_to_highest_volume_in_pullback,
            "feature_entry_bar_volume_to_volume_average": entry_bar_volume_to_volume_average,
            "feature_entry_bar_volume_to_recent_bars_average": potential_confirmation_bar.volume/volume_average if volume_average else 1,
            "feature_entry_bar_volume_to_highest_high_volume": entry_bar_volume_to_highest_high_volume,
            "feature_positive_vs_negative_volume_during_pullback": positive_vs_negative_volume_during_pullback,
            "feature_entry_bar_volume_to_previous_bar_volume": entry_bar_volume_to_previous_bar_volume,
            "feature_volume_since_highest_high_to_volume_before": volume_since_highest_high/volume_before_highest_high if volume_before_highest_high > 0 else 1,
            "feature_bars_since_highest_high_to_bars_before": len(bars_since_highest_high)/len(bars_before_highest_high),
            "feature_bars_above_volume_average_vs_under_since_highest_high": bars_above_volume_average/bars_under_volume_average if bars_under_volume_average > 0 else 1,
        }

    def macd_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        highest_high_one_minute_bar: common.objects.BarData,
        bars_since_highest_high: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, float]:
        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        histogram_sum = 0
        highest_histogram_since_highest_high = 0
        lowest_histogram_since_highest_high = 100
        histogram_changed_to_positive_direction_count = 0
        histogram_changed_to_negative_direction_count = 0
        positive_histogram_count = 0
        negative_histogram_count = 0
        for bar_object in bars_since_highest_high:
            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )

            if previous_bar is not None:
                if (
                    True
                    and bar_object.histogram > previous_bar.histogram
                    and bar_object.histogram > 0
                ):
                    positive_histogram_count += 1
                else:
                    negative_histogram_count += 1

            histogram_sum += bar_object.histogram
            if bar_object.histogram > highest_histogram_since_highest_high:
                highest_histogram_since_highest_high = bar_object.histogram
            if bar_object.histogram < lowest_histogram_since_highest_high:
                lowest_histogram_since_highest_high = bar_object.histogram

            if (
                True
                and previous_bar is not None
                and next_bar is not None
            ):
                if previous_bar.histogram < bar_object.histogram > next_bar.histogram:
                    histogram_changed_to_negative_direction_count += 1
                if previous_bar.histogram > bar_object.histogram < next_bar.histogram:
                    histogram_changed_to_positive_direction_count += 1

        distance_from_last_negative_macd_bar = 0
        for bar_object in one_minute_bars[1:]:
            if bar_object.macd > bar_object.signal_line:
                distance_from_last_negative_macd_bar += 1
            else:
                break

        entry_bar_macd_to_previous = potential_confirmation_bar.macd/previous_bar.macd if previous_bar is not None and previous_bar.macd > 0 else 1
        entry_bar_histogram_to_previous = potential_confirmation_bar.histogram/previous_bar.histogram if previous_bar is not None and previous_bar.histogram > 0 else 1
        entry_bar_histogram_to_highest_high = potential_confirmation_bar.histogram/highest_high_one_minute_bar.histogram if highest_high_one_minute_bar.histogram > 0 else 1
        entry_bar_histogram_to_highest_histogram = potential_confirmation_bar.histogram/highest_histogram_since_highest_high if highest_histogram_since_highest_high > 0 else 1
        entry_bar_histogram_to_lowest_histogram = potential_confirmation_bar.histogram/lowest_histogram_since_highest_high if lowest_histogram_since_highest_high > 0 else 1
        histogram_changed_to_positive_direction_vs_negative_pct = histogram_changed_to_positive_direction_count/histogram_changed_to_negative_direction_count if histogram_changed_to_negative_direction_count > 0 else 1

        return {
            "feature_entry_bar_macd_to_previous": entry_bar_macd_to_previous,
            "feature_entry_bar_histogram_to_previous": entry_bar_histogram_to_previous,
            "feature_entry_bar_histogram_to_highest_high": entry_bar_histogram_to_highest_high,
            "feature_entry_bar_histogram_to_highest_histogram": entry_bar_histogram_to_highest_histogram,
            "feature_entry_bar_histogram_to_lowest_histogram": entry_bar_histogram_to_lowest_histogram,
            "feature_histogram_changed_to_positive_direction_vs_negative_pct": histogram_changed_to_positive_direction_vs_negative_pct,
            "feature_uptrend_histogram_vs_downtrend_since_highest_high": positive_histogram_count/negative_histogram_count if negative_histogram_count > 0 else 1,
            "feature_distance_from_last_negative_macd_bar": distance_from_last_negative_macd_bar,
        }

    def pre_market_structure_features(
        self,
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> dict[str, float]:
        same_day_04_am = datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=4,
        )
        same_day_09_29 = datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=9,
            minute=29,
        )

        pre_market_bars = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if same_day_04_am <= bar_object.bar_time <= same_day_09_29
        ]

        pre_market_volume = 0
        for bar_object in pre_market_bars:
            pre_market_volume += bar_object.volume

        previous_day = None
        if len(day_timeframe_stock.bars) > 0:
            previous_day = day_timeframe_stock.bars[1]

        pre_market_gains = 0
        if pre_market_bars:
            pre_market_gains = (pre_market_bars[0].close - previous_day.close)/previous_day.close if previous_day is not None else 1

        return {
            "feature_pre_market_gains": pre_market_gains,
            "feature_pre_market_volume": pre_market_volume,
        }

    def feature_overall_legit_trade(
        self,
        features_data: dict[str, float],
    ) -> bool:
        current_day_volume_to_recent_days_volume = features_data["feature_current_day_volume_to_recent_days_volume"]
        current_ema20 = features_data["feature_current_day_ema_20_to_recent_days_ema_20"]
        current_vwap = features_data["feature_current_day_vwap_to_recent_days"]
        current_high_to_recent = features_data["feature_current_day_high_to_recent_days_highs"]
        current_day_high_to_previous_high = features_data["feature_current_day_high_to_previous_high"]
        gains_until_entry_bar = features_data["feature_gains_until_entry_bar"]
        controlled_volume_entry_quality = features_data["feature_controlled_volume_entry_quality"]
        entry_ema9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
        entry_extension_pressure = features_data["feature_entry_extension_pressure"]
        entry_volume_to_highest_high_volume = features_data["feature_entry_bar_volume_to_highest_high_volume"]
        weak_wick_volume_rejection = features_data["feature_weak_wick_volume_rejection"]
        entry_breakout_efficiency_from_ema_9 = features_data["feature_entry_breakout_efficiency_from_ema_9"]
        current_day_movement_to_recent_days_movement = features_data["feature_current_day_movement_to_recent_days_movement"]
        entry_bar_upper_wick = features_data["feature_entry_bar_upper_wick"]
        entry_histogram_to_highest_histogram = features_data["feature_entry_bar_histogram_to_highest_histogram"]
        entry_volume_to_highest_volume_in_pullback = features_data["feature_entry_bar_volume_to_highest_volume_in_pullback"]
        entry_histogram_to_lowest_histogram = features_data["feature_entry_bar_histogram_to_lowest_histogram"]
        entry_volume_price_efficiency = features_data["feature_entry_volume_price_efficiency"]
        current_day_low_to_ema_9 = features_data["feature_current_day_low_to_ema_9"]
        entry_bar_close_to_highest_high = features_data["feature_entry_bar_close_to_highest_high"]
        price_movement_from_highest_high_to_lowest_low = features_data["feature_price_movement_from_highest_high_to_lowest_low"]
        entry_bar_body = features_data["feature_entry_bar_body"]
        entry_bar_low_to_ema_9 = features_data["feature_entry_bar_low_to_ema_9"]
        bars_since_highest_high_to_bars_before = features_data["feature_bars_since_highest_high_to_bars_before"]
        volume_since_highest_high_to_volume_before = features_data["feature_volume_since_highest_high_to_volume_before"]
        previous_bar_volume_to_its_previous_volume = features_data["feature_previous_bar_volume_to_its_previous_volume"]
        previous_bar_high_to_highest_high = features_data["feature_previous_bar_high_to_highest_high"]
        entry_bar_volume_to_highest_high_volume = features_data["feature_entry_bar_volume_to_highest_high_volume"]
        histogram_changed_to_positive_direction_vs_negative_pct = features_data["feature_histogram_changed_to_positive_direction_vs_negative_pct"]
        entry_bar_volume_to_recent_bars_average = features_data["feature_entry_bar_volume_to_recent_bars_average"]
        entry_upper_wick_to_recent_upper_wick_average = features_data["feature_entry_upper_wick_to_recent_upper_wick_average"]
        entry_body_to_highest_high_body = features_data["feature_entry_body_to_highest_high_body"]
        previous_bar_close_to_highest_high = features_data["feature_previous_bar_close_to_highest_high"]
        pullback_depth_vs_pre_high_move = features_data["feature_pullback_depth_vs_pre_high_move"]
        recent_bars_up_trend_pct = features_data["feature_recent_bars_up_trend_pct"]
        entry_body_to_recent_bars_body_average = features_data["feature_entry_body_to_recent_bars_body_average"]
        pre_market_volume = features_data["feature_pre_market_volume"]
        entry_close_to_vwap = features_data["feature_entry_close_to_vwap"]
        entry_bar_histogram_to_previous = features_data["feature_entry_bar_histogram_to_previous"]
        gains_since_lowest_low = features_data["feature_gains_since_lowest_low"]
        recent_bars_positive_bars_pct = features_data["feature_recent_bars_positive_bars_pct"]
        emas_distances_to_recent_bars_ema_distances = features_data["feature_emas_distances_to_recent_bars_ema_distances"]

        # Reject: entry too extended
        # Changed extension threshold from 0.4078 -> 0.48.
        # Old version removed 2 positives. This version removed 0 positives.
        if entry_ema9_to_vwap > 1.122 and entry_extension_pressure > 0.428:
            return False

        # Reject: wick-volume rejection, but only if entry volume does not rescue it.
        # Old version removed 1 positive.
        # This version removed 0 positives and still caught the FP cases.
        if weak_wick_volume_rejection and entry_volume_to_highest_high_volume <= 1.5:
            return False

        # Reject: weak context + inefficient breakout + not enough relative volume.
        # Added current_volume > 2.0 to avoid rejecting one good positive case.
        if (
            current_vwap <= 1.36
            and entry_breakout_efficiency_from_ema_9 <= 0.40
            and current_day_volume_to_recent_days_volume <= 145
            and current_day_volume_to_recent_days_volume > 2.0
        ):
            return False

        # Reject: weak current-day high context.
        # This replaces the bugged current_high_to_previous rule.
        # Uses feature_current_day_high_to_previous_high correctly.
        if (
            current_vwap <= 2.12
            and current_high_to_recent > 1.81
            and current_day_high_to_previous_high <= 1.40
            and gains_until_entry_bar <= 0.70
            and entry_breakout_efficiency_from_ema_9 <= 0.55
        ):
            return False

        # Reject: very extended day, but weak breakout efficiency
        # Safe on current dataset: removed 0 positives.
        if (
            current_high_to_recent > 3.31
            and entry_breakout_efficiency_from_ema_9 <= 0.40
            and gains_until_entry_bar > 0.60
        ):
            return False

        # Reject: big current-day movement, but weak VWAP context
        if current_vwap <= 1.42 and current_day_movement_to_recent_days_movement > 6.10:
            return False

        # Reject: weak previous-high reclaim with high breakout-efficiency ratio
        if current_day_high_to_previous_high <= 1.02 and entry_breakout_efficiency_from_ema_9 > 0.64:
            return False

        if entry_histogram_to_highest_histogram <= 0.417 and entry_volume_to_highest_volume_in_pullback > 2.16:
            return False

        if current_ema20 <= 0.988 and entry_histogram_to_lowest_histogram > 1.28:
            return False

        # Reject: elevated day structure, but inefficient entry breakout
        if (
            current_day_low_to_ema_9 > 1.29
            and entry_breakout_efficiency_from_ema_9 <= 0.36
            and controlled_volume_entry_quality > 1.0
        ):
            return False

        # Reject: deep pullback, but weak entry body
        if price_movement_from_highest_high_to_lowest_low > 5 and entry_bar_body < 0.65:
            return False

        # Reject: weak current-day breakout context + entry candle loses EMA9
        if current_day_high_to_previous_high <= 1.28 and entry_bar_low_to_ema_9 <= 0.984:
            return False

        if bars_since_highest_high_to_bars_before <= 0.011 and entry_breakout_efficiency_from_ema_9 <= 0.27:
            return False

        if volume_since_highest_high_to_volume_before <= 0.045 and entry_breakout_efficiency_from_ema_9 <= 0.27:
            return False

        # Reject: previous bar had weak volume, and entry candle shows rejection
        if previous_bar_volume_to_its_previous_volume <= 0.49 and entry_bar_upper_wick >= 0.33:
            return False

        # Reject: previous bar already pushed above old high, but entry body is weak
        if previous_bar_high_to_highest_high >= 1.019 and entry_bar_body <= 0.586:
            return False

        # Reject: previous bar was not close to reclaiming high, and entry rejects
        if previous_bar_high_to_highest_high <= 0.973 and entry_bar_upper_wick >= 0.343:
            return False

        # Reject: previous bar already pushed above old high,
        # and histogram already moved strongly in positive direction
        if previous_bar_high_to_highest_high >= 1.010 and histogram_changed_to_positive_direction_vs_negative_pct >= 1.04:
            return False

        # Reject: active current-day move, but entry is already too extended
        if current_day_movement_to_recent_days_movement >= 1.30 and entry_extension_pressure >= 0.68:
            return False

        # Reject: entry volume spike is large versus highest-high volume,
        # but not truly strong versus recent bars
        if entry_bar_volume_to_recent_bars_average <= 5.80 and entry_bar_volume_to_highest_high_volume >= 5.60:
            return False

        # Reject: entry candle shows abnormal rejection
        # and the entry body is weak compared with the highest-high candle
        if entry_upper_wick_to_recent_upper_wick_average >= 2.13 and entry_body_to_highest_high_body <= 1.17:
            return False

        # Reject: previous bar already closed very close to old high,
        # but entry comes with almost no real rebuild after the highest high
        if previous_bar_close_to_highest_high >= 0.997 and bars_since_highest_high_to_bars_before <= 0.002:
            return False

        # Reject: very shallow pullback versus the pre-high move,
        # while the current day volume is already extremely expanded
        if pullback_depth_vs_pre_high_move <= 0.42 and current_day_volume_to_recent_days_volume >= 72:
            return False

        # Reject: weak recent uptrend, but entry is already stretched above old high
        if (
            recent_bars_up_trend_pct <= 0.50
            and (
                entry_bar_close_to_highest_high >= 1.091
                or entry_breakout_efficiency_from_ema_9 >= 0.886
            )
        ):
            return False

        # Reject: deep pullback, but entry body is not strong enough versus recent bars
        if entry_body_to_recent_bars_body_average <= 3.0 and pullback_depth_vs_pre_high_move >= 2.82:
            return False

        # Reject: low premarket volume + weak gains into entry
        if gains_until_entry_bar <= 0.347 and pre_market_volume <= 2242:
            return False

        # Reject: almost no rebuild after highest high + not enough current-day volume context
        if current_day_volume_to_recent_days_volume <= 4.25 and bars_since_highest_high_to_bars_before <= 0.00163:
            return False

        # Reject: histogram expands, but price is not strong enough above VWAP
        if entry_close_to_vwap <= 1.13 and entry_bar_histogram_to_previous >= 4.70:
            return False

        if entry_breakout_efficiency_from_ema_9 <= 0.263 and entry_ema9_to_vwap > 1.122:
            return False

        if entry_volume_price_efficiency <= 0.050 and controlled_volume_entry_quality <= 0.852:
            return False

        # Reject: almost no bounce from pullback low,
        # and entry volume is weak versus highest pullback volume
        if gains_since_lowest_low <= 0.047 and entry_volume_to_highest_volume_in_pullback <= 1.09:
            return False

        if gains_since_lowest_low <= 0.05 and current_day_movement_to_recent_days_movement >= 7.5:
            return False

        # Reject: many recent positive bars, but entry candle still loses EMA9
        if recent_bars_positive_bars_pct >= 0.77 and entry_bar_low_to_ema_9 <= 0.995:
            return False

        # Reject: EMA distance is unusually expanded vs recent bars,
        # and entry is already extended from VWAP
        if emas_distances_to_recent_bars_ema_distances >= 1.017 and entry_ema9_to_vwap >= 1.040:
            return False

        return True

    #pylint:disable=W0613
    def extract_features_from_symbol_data(
        self,
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, any]:
        bars_since_highest_high = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if highest_high_one_minute_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        total_volume = sum(
            bar_object.volume
            for bar_object in one_minute_bars
        )

        recent_days_structure_features = self.recent_days_structure_features(
            day_timeframe_stock=day_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )
        breakout_structure_features = self.breakout_structure_features(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            bars_since_highest_high=bars_since_highest_high,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=one_minute_bars,
        )
        volume_structure_features = self.volume_structure_features(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            bars_since_highest_high=bars_since_highest_high,
            potential_confirmation_bar=potential_confirmation_bar,
        )
        macd_structure_features = self.macd_structure_features(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            bars_since_highest_high=bars_since_highest_high,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=one_minute_bars,
        )
        pre_market_structure_features = self.pre_market_structure_features(
            day_timeframe_stock=day_timeframe_stock,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        feature_upper_wick = breakout_structure_features["feature_entry_bar_upper_wick"]
        feature_volume_to_previous = volume_structure_features["feature_entry_bar_volume_to_previous_bar_volume"]

        base_features = {
            "highest_high_one_minute_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else datetime.datetime.fromtimestamp(0),
            "total_volume": total_volume,
            "feature_entry_bar_volume_to_total_volume": breakout_structure_features["entry_bar_volume"]/total_volume if total_volume > 0 else 1,
        }

        highest_high_bar_body = abs(highest_high_one_minute_bar.close - highest_high_one_minute_bar.open_value) / highest_high_one_minute_bar.open_value if highest_high_one_minute_bar is not None else 0
        highest_high_bar_wick = highest_high_one_minute_bar.high - highest_high_one_minute_bar.close if highest_high_one_minute_bar is not None and highest_high_one_minute_bar.is_positive else 0
        if highest_high_bar_wick == 0:
            highest_high_bar_wick = highest_high_one_minute_bar.high - highest_high_one_minute_bar.open_value if highest_high_one_minute_bar is not None and not highest_high_one_minute_bar.is_positive else 0

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        feature_clean_breakout_efficiency = 1 if (
            breakout_structure_features["feature_entry_breakout_efficiency_from_ema_9"] >= 0.35
            and breakout_structure_features["feature_entry_breakout_efficiency_from_ema_9"] <= 0.80
            and breakout_structure_features["feature_entry_bar_body"] >= 0.75
            and breakout_structure_features["feature_entry_bar_upper_wick"] <= 0.15
        ) else 0
        feature_entry_rejection_pressure = breakout_structure_features["feature_entry_bar_upper_wick"] / max(breakout_structure_features["feature_entry_bar_body"], 0.01)
        feature_pullback_health = (
            volume_structure_features["feature_positive_vs_negative_volume_during_pullback"]
            * volume_structure_features["feature_entry_bar_volume_to_highest_high_volume"]
        ) * max(breakout_structure_features["feature_breakout_attempts_during_pullback"] + 1, 1)

        complex_features = {
            "feature_weak_wick_volume_rejection": 1 if feature_upper_wick > 0.262 and feature_volume_to_previous <= 1.17 else 0,
            "feature_clean_breakout_efficiency": feature_clean_breakout_efficiency,
            "feature_inefficient_breakout_extension": 1 if (
                breakout_structure_features["feature_entry_breakout_efficiency_from_ema_9"] < 0.20
                and breakout_structure_features["feature_entry_extension_pressure"] > 0.30
            ) else 0,
            "feature_strong_vwap_volume_reentry": 1 if (
                recent_days_structure_features["feature_current_day_vwap_to_recent_days"] > 2.28
                and breakout_structure_features["feature_entry_extension_pressure"] > 0.169
                and volume_structure_features["feature_entry_bar_volume_to_previous_bar_volume"] > 2.03
            ) else 0,
            "feature_volume_without_macd_confirmation": volume_structure_features["feature_entry_bar_volume_to_highest_volume_in_pullback"]/ max(macd_structure_features["feature_entry_bar_histogram_to_highest_histogram"], 0.01),
            "feature_entry_volume_price_efficiency": (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/max(volume_structure_features["feature_entry_bar_volume_to_volume_average"], 0.01),
            "feature_highest_high_quality": (
                highest_high_bar_body
                * highest_high_one_minute_bar.close
                * (highest_high_one_minute_bar.volume/highest_high_one_minute_bar.volume_average)
            ) / max(highest_high_bar_wick + 0.01, 0.01),
            "feature_pullback_health": feature_pullback_health,
            "feature_previous_bar_breakout_quality": (
                breakout_structure_features["feature_previous_bar_already_crossed_highest_high"]
                and previous_bar.bar_wick_percentage > 0.25
                and potential_confirmation_bar.body_percentage < previous_bar.body_percentage
            ) if previous_bar is not None else 0,
            "feature_minutes_since_market_open": ((potential_confirmation_bar.bar_time.hour - 9) * 60) + potential_confirmation_bar.bar_time.minute - 30,
            "feature_entry_rejection_pressure": feature_entry_rejection_pressure,
            "feature_late_chase_after_high": (
                breakout_structure_features["feature_distance_from_highest_high"] <= 3
                and breakout_structure_features["feature_entry_bar_movement_recent_bars_average"] > 20
                and breakout_structure_features["feature_crossed_at_least_one_bar_from_recent_bars"] == 0
            ),
            "feature_clean_reentry_confirmation": (
                feature_clean_breakout_efficiency == 1
                and feature_entry_rejection_pressure <= 0.15
                and feature_pullback_health > 2.0
            ),
            "feature_macd_recovery_age_quality": macd_structure_features["feature_distance_from_last_negative_macd_bar"] * macd_structure_features["feature_entry_bar_macd_to_previous"],
        }

        features = base_features | complex_features | recent_days_structure_features | breakout_structure_features | volume_structure_features | macd_structure_features | pre_market_structure_features

        feature_overall_legit_trade = {
            "feature_overall_legit_trade": self.feature_overall_legit_trade(
                features_data=features,
            ),
        }

        features = features | feature_overall_legit_trade

        return features
