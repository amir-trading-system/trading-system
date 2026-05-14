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
        entry_bar_open_to_ema_9 = potential_confirmation_bar.open_value/potential_confirmation_bar.ema_9
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
        bars_count_since_open = len(one_minute_bars)
        gain_profit_since_open = (potential_confirmation_bar.close - one_minute_bars[-1].open_value)/one_minute_bars[-1].open_value if len(one_minute_bars) > 0 else 0
        feature_profit_since_open_to_bars_count_since_open = gain_profit_since_open/bars_count_since_open if bars_count_since_open > 0 else 0


        return {
            "entry_bar_volume": potential_confirmation_bar.volume,
            "feature_entry_bar_close_to_highest_high": entry_bar_close_to_highest_high,
            "feature_entry_bar_body": entry_bar_body,
            "feature_entry_bar_upper_wick": entry_bar_upper_wick,
            "feature_entry_bar_lower_wick": entry_bar_lower_wick,
            "feature_entry_bar_low_to_ema_9": entry_bar_low_to_ema_9,
            "feature_entry_bar_open_to_ema_9": entry_bar_open_to_ema_9,
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
            "feature_profit_since_open_to_bars_count_since_open": feature_profit_since_open_to_bars_count_since_open,
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
            "feature_entry_bar_volume": potential_confirmation_bar.volume,
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
        current_histogram_is_bigger_than_previous = potential_confirmation_bar.histogram > previous_bar.histogram if previous_bar is not None and previous_bar.histogram > 0 else False
        entry_bar_histogram_to_highest_high = potential_confirmation_bar.histogram/highest_high_one_minute_bar.histogram if highest_high_one_minute_bar.histogram > 0 else 1
        entry_bar_histogram_to_highest_histogram = potential_confirmation_bar.histogram/highest_histogram_since_highest_high if highest_histogram_since_highest_high > 0 else 1
        entry_bar_histogram_to_lowest_histogram = potential_confirmation_bar.histogram/lowest_histogram_since_highest_high if lowest_histogram_since_highest_high > 0 else 1
        histogram_changed_to_positive_direction_vs_negative_pct = histogram_changed_to_positive_direction_count/histogram_changed_to_negative_direction_count if histogram_changed_to_negative_direction_count > 0 else 1

        return {
            "feature_entry_bar_macd_to_previous": entry_bar_macd_to_previous,
            "feature_current_histogram_is_bigger_than_previous": current_histogram_is_bigger_than_previous,
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
        minutes_since_market_open = features_data["feature_minutes_since_market_open"]
        entry_close_to_previous_bar_close = features_data["feature_entry_close_to_previous_bar_close"]
        entry_body_to_previous_bar_body = features_data["feature_entry_body_to_previous_bar_body"]
        clean_breakout_efficiency = features_data["feature_clean_breakout_efficiency"]
        current_day_ema_9_to_ema_20_distance_to_recent_days = features_data["feature_current_day_ema_9_to_ema_20_distance_to_recent_days"]
        entry_bar_volume_to_previous_bar_volume = features_data["feature_entry_bar_volume_to_previous_bar_volume"]
        entry_bar_macd_to_previous = features_data["feature_entry_bar_macd_to_previous"]
        failed_attempts_pressure = features_data["feature_failed_attempts_pressure"]
        entry_close_position_vs_previous_close_position = features_data["feature_entry_close_position_vs_previous_close_position"]
        entry_bar_open_to_ema_9 = features_data["feature_entry_bar_open_to_ema_9"]
        profit_since_open_to_bars_count_since_open = features_data["feature_profit_since_open_to_bars_count_since_open"]
        entry_close_strength_to_highest_high_close_strength = features_data["feature_entry_close_strength_to_highest_high_close_strength"]
        reclaim_close_strength_since_highest_high = features_data["feature_reclaim_close_strength_since_highest_high"]
        entry_bar_lower_wick = features_data["feature_entry_bar_lower_wick"]
        entry_close_to_previous_bar_high = features_data["feature_entry_close_to_previous_bar_high"]
        volume_without_macd_confirmation = features_data["feature_volume_without_macd_confirmation"]
        bars_above_volume_average_vs_under_since_highest_high = features_data["feature_bars_above_volume_average_vs_under_since_highest_high"]
        macd_recovery_age_quality = features_data["feature_macd_recovery_age_quality"]
        entry_bar_vwap_to_ema_20 = features_data["feature_entry_bar_vwap_to_ema_20"]
        failed_pressure_to_followthrough = features_data["feature_failed_pressure_to_followthrough"]
        current_day_vwap_to_recent_days = features_data["feature_current_day_vwap_to_recent_days"]
        pre_market_gains = features_data["feature_pre_market_gains"]
        entry_bar_ema_9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
        highest_high_to_entry_elapsed_minutes = features_data["feature_highest_high_to_entry_elapsed_minutes"]
        highest_high_quality = features_data["feature_highest_high_quality"]
        entry_followthrough_after_near_reclaim = features_data["feature_entry_followthrough_after_near_reclaim"]
        near_high_weak_followthrough = features_data["feature_near_high_weak_followthrough"]
        macd_recovery_followthrough_quality = features_data["feature_macd_recovery_followthrough_quality"]
        entry_bar_volume_to_volume_average = features_data["feature_entry_bar_volume_to_volume_average"]
        volume_since_lowest_low_to_entry_vs_since_highest_high = features_data["feature_volume_since_lowest_low_to_entry_vs_since_highest_high"]
        total_volume = features_data["total_volume"]
        current_day_ema_9_to_ema_20 = features_data["feature_current_day_ema_9_to_ema_20"]
        entry_close_to_lowest_low_recovery = features_data["feature_entry_close_to_lowest_low_recovery"]

        # Rescue: strong failed-attempt pressure, but day movement is still controlled
        # Use this as a rescue clause inside the rule that rejects this group.
        if (
            failed_attempts_pressure >= 0.8136693269
            and current_day_movement_to_recent_days_movement <= 1.9113661164
        ):
            return True

        # Rescue: weak recent trend / no post-high volume pattern,
        # but only for very low MACD-recovery/volume-above-average structure
        if (
            recent_bars_positive_bars_pct <= 0.40
            and bars_since_highest_high_to_bars_before <= 0.0041551565
        ):
            return True

        # Rescue: very strong broader EMA20 context,
        # and current-day low is deeply below EMA9
        if (
            current_ema20 >= 1.8320
            and current_day_low_to_ema_9 <= 0.5501
        ):
            return True

        # Rescue candidate: very strong current-day EMA structure,
        # but current-day low had a deep reset below EMA9
        if (
            current_day_low_to_ema_9 <= 0.7571
            and current_day_ema_9_to_ema_20 >= 1.1849
        ):
            return True

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

        # Reject: weak context + inefficient breakout + not enough relative volume
        # Rescue if gains into entry are still controlled and profit pace from open is low
        if (
            current_vwap <= 1.36
            and entry_breakout_efficiency_from_ema_9 <= 0.40
            and current_day_volume_to_recent_days_volume <= 145
            and current_day_volume_to_recent_days_volume > 2.0
            and not (
                gains_until_entry_bar <= 0.278
                and profit_since_open_to_bars_count_since_open <= 0.00130
            )
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
            and not (
                current_day_high_to_previous_high >= 1.319
                and entry_ema9_to_vwap <= 1.073
            )
        ):
            return False

        # Rescue valid positives where entry is not too far above old high
        # and body is not abnormally expanded versus recent bars
        if (
            current_high_to_recent > 3.31
            and entry_breakout_efficiency_from_ema_9 <= 0.40
            and gains_until_entry_bar > 0.60
            and not (
                entry_bar_close_to_highest_high <= 1.023
                and entry_body_to_recent_bars_body_average <= 5.55
            )
        ):
            return False

        # Reject: big current-day movement, but weak VWAP context
        if current_vwap <= 1.42 and current_day_movement_to_recent_days_movement > 6.10:
            return False

        # Reject: weak previous-high reclaim with high breakout-efficiency ratio
        if current_day_high_to_previous_high <= 1.02 and entry_breakout_efficiency_from_ema_9 > 0.64:
            return False

        # Additional rescue: controlled body versus recent candles
        if (
            entry_histogram_to_highest_histogram <= 0.417
            and entry_volume_to_highest_volume_in_pullback > 2.16
            and not (
                entry_bar_body >= 0.90
                and entry_close_strength_to_highest_high_close_strength >= 2.0
            )
            and not (
                entry_body_to_recent_bars_body_average <= 3.26
            )
        ):
            return False

        if (
            current_ema20 <= 0.988
            and entry_histogram_to_lowest_histogram > 1.28
            and not (
                entry_close_strength_to_highest_high_close_strength >= 1.27
                and entry_ema9_to_vwap <= 1.10
            )
        ):
            return False

        # Reject: elevated day structure, but inefficient entry breakout
        # Rescue if EMA9 is already meaningfully above VWAP
        if (
            current_day_low_to_ema_9 > 1.29
            and entry_breakout_efficiency_from_ema_9 <= 0.36
            and controlled_volume_entry_quality > 1.0
            and not (
                entry_ema9_to_vwap >= 1.118
            )
        ):
            return False

        # Reject: deep pullback, but weak entry body
        if price_movement_from_highest_high_to_lowest_low > 5 and entry_bar_body < 0.65:
            return False

        # Reject: weak current-day breakout context + entry candle loses EMA9
        if current_day_high_to_previous_high <= 1.28 and entry_bar_low_to_ema_9 <= 0.984:
            return False

        if (
            bars_since_highest_high_to_bars_before <= 0.011
            and entry_breakout_efficiency_from_ema_9 <= 0.27
            and not (
                entry_body_to_recent_bars_body_average <= 6.42
                and entry_bar_upper_wick <= 0.145
            )
        ):
            return False

        # Reject: no post-high volume rebuild + inefficient breakout
        # Rescue very fast continuation if entry body strongly improves over previous bar
        # and histogram is not weak versus the highest-high histogram
        if (
            volume_since_highest_high_to_volume_before <= 0.045
            and entry_breakout_efficiency_from_ema_9 <= 0.27
            and not (
                entry_body_to_previous_bar_body >= 20.0
                and entry_histogram_to_highest_histogram >= 1.0
                and highest_high_to_entry_elapsed_minutes <= 2
            )
        ):
            return False

        # Reject: previous bar had weak volume, and entry candle shows rejection
        if previous_bar_volume_to_its_previous_volume <= 0.49 and entry_bar_upper_wick >= 0.33:
            return False

        # Reject: previous bar already pushed above old high, but entry body is weak
        if previous_bar_high_to_highest_high >= 1.019 and entry_bar_body <= 0.586:
            return False

        # Reject: previous bar was not close to reclaiming high, and entry rejects
        # Rescue if recent trend is strong enough
        if (
            previous_bar_high_to_highest_high <= 0.973
            and entry_bar_upper_wick >= 0.343
            and not (
                recent_bars_up_trend_pct >= 0.70
            )
        ):
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

        # Reject: inefficient breakout + high EMA9/VWAP,
        # unless the entry candle itself is strong
        if (
            entry_breakout_efficiency_from_ema_9 <= 0.263
            and entry_ema9_to_vwap > 1.122
            and not (
                entry_bar_body >= 0.82
                and entry_close_strength_to_highest_high_close_strength >= 1.30
            )
        ):
            return False

        # Reject: weak volume-price efficiency + weak controlled volume
        # Rescue if there was meaningful post-high volume rebuild
        # and entry close quality is strong versus the highest-high candle
        if (
            entry_volume_price_efficiency <= 0.050
            and controlled_volume_entry_quality <= 0.852
            and not (
                volume_since_highest_high_to_volume_before >= 0.2138
                and entry_close_strength_to_highest_high_close_strength >= 1.69
            )
        ):
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

        if (
            emas_distances_to_recent_bars_ema_distances >= 1.017
            and entry_ema9_to_vwap >= 1.040
            and not (
                entry_body_to_recent_bars_body_average >= 5.50
                and entry_extension_pressure <= 0.17
            )
        ):
            return False

        # Reject: entry loses EMA9, but previous bar was already near old high
        if entry_bar_low_to_ema_9 <= 0.990 and previous_bar_close_to_highest_high >= 0.984:
            return False

        # Reject: early setup where previous bar was already near the old high,
        # but entry does not add enough follow-through over previous close
        if (
            minutes_since_market_open <= 23
            and previous_bar_close_to_highest_high >= 0.984
            and entry_close_to_previous_bar_close <= 1.095
        ):
            return False

        # Reject: very early setup, weak entry body versus previous bar,
        # but the candle still looks like a clean breakout
        if (
            minutes_since_market_open <= 23
            and entry_body_to_previous_bar_body <= 1.86
            and clean_breakout_efficiency >= 1.0
        ):
            return False

        # Reject: stretched EMA structure + volume spike, but weak MACD follow-through
        if (
            current_day_ema_9_to_ema_20_distance_to_recent_days >= 5.33
            and entry_bar_volume_to_previous_bar_volume >= 7.60
            and entry_bar_macd_to_previous <= 0.67
        ):
            return False

        # Reject: entry volume is only strong versus previous bar,
        # but weak versus the original highest-high volume
        if entry_bar_volume_to_previous_bar_volume >= 15.60 and entry_bar_volume_to_highest_high_volume <= 0.91:
            return False

        # Reject: stretched EMA structure + failed attempts + abnormal close-position shift
        if (
            current_day_ema_9_to_ema_20_distance_to_recent_days >= 4.60
            and failed_attempts_pressure >= 0.34
            and entry_close_position_vs_previous_close_position >= 2.30
        ):
            return False

        # Reject: entry opens below EMA9 and entry volume is weak vs recent bars
        if entry_bar_open_to_ema_9 <= 0.9885 and entry_bar_volume_to_recent_bars_average <= 2.14:
            return False

        if entry_ema9_to_vwap <= 1.0144 and entry_body_to_highest_high_body <= 1.445:
            return False

        if profit_since_open_to_bars_count_since_open >= 0.00775 and volume_since_highest_high_to_volume_before <= 0.0103:
            return False

        if entry_bar_open_to_ema_9 >= 1.007 and entry_close_position_vs_previous_close_position <= 0.68:
            return False

        # Reject: weak recent trend + weak previous-high context
        if (
            recent_bars_up_trend_pct <= 0.40
            and current_day_high_to_previous_high <= 1.0216
        ):
            return False

        # Reject: compressed EMA structure, but entry candle body is extremely strong
        if (
            emas_distances_to_recent_bars_ema_distances <= 0.119
            and entry_bar_body >= 0.986
        ):
            return False

        if (
            entry_close_to_previous_bar_close <= 1.0624
            and controlled_volume_entry_quality <= 0.7611
        ):
            return False

        if (
            price_movement_from_highest_high_to_lowest_low <= 0.2253
            and controlled_volume_entry_quality <= 1.1314
        ):
            return False

        # Reject: entry is extended, but candle shows large upper-wick rejection
        if (
            entry_bar_upper_wick >= 0.333333
            and entry_extension_pressure >= 0.325339
        ):
            return False

        # Reject: weak reclaim close after highest high,
        # and entry upper wick is unusually small versus recent upper wicks
        if (
            reclaim_close_strength_since_highest_high <= 0.110868
            and entry_upper_wick_to_recent_upper_wick_average <= 0.264035
        ):
            return False

        # Reject: shallow pullback, weak body versus previous bar,
        # and compressed EMA-distance structure
        if (
            pullback_depth_vs_pre_high_move <= 0.88375
            and entry_body_to_previous_bar_body <= 0.98432
            and emas_distances_to_recent_bars_ema_distances <= 0.140767
        ):
            return False

        # Reject: almost full-body candle after large post-high volume participation
        if (
            entry_bar_body >= 0.966085
            and volume_since_highest_high_to_volume_before >= 0.578934
            and entry_bar_lower_wick <= 0.015361
        ):
            return False

        if entry_close_to_previous_bar_high <= 1.102621092 and profit_since_open_to_bars_count_since_open >= 0.01616006036:
            return False

        if volume_without_macd_confirmation <= 1.19487729 and bars_above_volume_average_vs_under_since_highest_high <= 0:
            return False

        if current_day_movement_to_recent_days_movement >= 18.4136654 and bars_since_highest_high_to_bars_before <= 0.0112745098:
            return False

        if current_day_movement_to_recent_days_movement >= 9.548780488 and volume_since_highest_high_to_volume_before <= 0.01110606138:
            return False

        if macd_recovery_age_quality >= 17.66563587 and entry_bar_vwap_to_ema_20 <= 0.832889939:
            return False

        if failed_pressure_to_followthrough >= 0.4016287815 and entry_close_position_vs_previous_close_position >= 8.03125:
            return False

        if current_day_vwap_to_recent_days <= 1.227176821 and pre_market_gains >= 0.1671960138:
            return False

        if entry_body_to_recent_bars_body_average <= 1.63759 and entry_close_to_vwap >= 1.27141:
            return False

        if entry_upper_wick_to_recent_upper_wick_average <= 0 and bars_since_highest_high_to_bars_before <= 0.00269945:
            return False

        if (
            entry_body_to_previous_bar_body >= 69.0345
            and (
                entry_bar_ema_9_to_vwap >= 1.16935
                or entry_bar_vwap_to_ema_20 <= 0.885003
            )
        ):
            return False

        if highest_high_quality >= 14.5937 and volume_since_highest_high_to_volume_before <= 0.0111551:
            return False

        if (
            current_day_ema_9_to_ema_20_distance_to_recent_days >= 15.8314
            and (
                entry_followthrough_after_near_reclaim >= 1.46395
                or near_high_weak_followthrough <= 0.683098
                or entry_close_to_previous_bar_high >= 1.34121
                or entry_close_to_previous_bar_close >= 1.3729
                or pre_market_volume <= 210.48
            )
        ):
            return False

        if macd_recovery_followthrough_quality >= 38.3995 and volume_since_highest_high_to_volume_before <= 0.0265052:
            return False

        if (
            previous_bar_high_to_highest_high >= 1.005804598
            and (
                entry_bar_volume_to_previous_bar_volume >= 2.483333125
            )
        ):
            return False

        # Reject: previous bar was already near the high,
        # but entry close quality is weak and entry volume is not impressive vs average
        if (
            previous_bar_close_to_highest_high >= 0.97686
            and entry_close_position_vs_previous_close_position <= 0.79938
            and entry_bar_volume_to_volume_average <= 2.31401
        ):
            return False

        # Reject: previous bar was already near high,
        # reclaim strength is weak,
        # and entry volume is not strong versus the previous bar
        if (
            previous_bar_close_to_highest_high >= 0.99062
            and reclaim_close_strength_since_highest_high <= 0.29509
            and entry_bar_volume_to_previous_bar_volume <= 1.45341
        ):
            return False

        # Reject: high volume-price efficiency while histogram already moved positive
        if (
            entry_volume_price_efficiency >= 0.81739
            and histogram_changed_to_positive_direction_vs_negative_pct >= 2.0
            and volume_since_lowest_low_to_entry_vs_since_highest_high >= 0.86157
        ):
            return False

        if (
            entry_volume_price_efficiency <= 0.03799
            and current_day_ema_9_to_ema_20_distance_to_recent_days >= 9.24778
            and failed_attempts_pressure >= 0.14996
        ):
            return False

        # Reject: low premarket participation + weak follow-through + weak volume/MACD confirmation
        if (
            pre_market_volume <= 12626.2
            and entry_followthrough_after_near_reclaim <= 1.1097255811
            and volume_without_macd_confirmation <= 1.3859621588
        ):
            return False

        # Reject: entry is floating above EMA9, but bounce/follow-through is weak
        if (
            entry_bar_low_to_ema_9 >= 1.0093729767
            and gains_since_lowest_low <= 0.0738457243
            and entry_close_position_vs_previous_close_position <= 1.0
        ):
            return False

        # Reject: previous bar was not close enough to high, and entry shows rejection
        if (
            previous_bar_close_to_highest_high <= 0.9768057971
            and entry_close_to_previous_bar_high <= 1.0443794455
            and entry_bar_upper_wick >= 0.1618463677
        ):
            return False

        # Reject: high volume efficiency + high recent volume, but with upper-wick rejection
        if (
            entry_volume_price_efficiency >= 0.2663313036
            and entry_bar_volume_to_recent_bars_average >= 4.1439257575
            and entry_bar_upper_wick >= 0.1618463677
        ):
            return False

        # Reject: deep pullback versus pre-high move,
        # but entry body is weak versus recent candles
        if (
            entry_body_to_recent_bars_body_average <= 2.7161
            and pullback_depth_vs_pre_high_move >= 2.3676
        ):
            return False

        # Reject: weak daily EMA20 context,
        # and entry volume is weaker than previous bar
        if (
            current_ema20 <= 1.0059
            and entry_bar_volume_to_previous_bar_volume <= 0.6496
        ):
            return False

        # Reject: very large body versus highest-high body,
        # but weak volume/MACD confirmation
        if (
            volume_without_macd_confirmation <= 0.4503
            and entry_body_to_highest_high_body >= 21.0911
        ):
            return False

        # Reject: failed-pressure/fake-reclaim pattern,
        # while recent bars are not positive enough
        if (
            failed_pressure_to_followthrough >= 0.3708
            and recent_bars_positive_bars_pct <= 0.30
        ):
            return False

        # Reject: very high total-volume day with oversized entry volume vs average
        if (
            total_volume >= 21435696.25
            and entry_bar_volume_to_volume_average >= 6.1061
        ):
            return False

        # Reject: low total-volume name, but entry is already extended above VWAP/EMA structure
        if (
            total_volume <= 647365.35
            and entry_ema9_to_vwap >= 1.1237
        ):
            return False

        # Reject: almost no premarket participation and current-day move is not strong enough
        if (
            pre_market_volume <= 229.31
            and current_day_movement_to_recent_days_movement <= 4.4058
        ):
            return False

        # Reject: weak current-day VWAP context and weak volume from low into entry
        if (
            current_day_vwap_to_recent_days <= 1.3480
            and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.2413
        ):
            return False

        # Reject: shallow/no real pullback, while VWAP is still below EMA20
        if (
            pullback_depth_vs_pre_high_move <= 0.4873
            and entry_bar_vwap_to_ema_20 <= 0.8890
        ):
            return False

        # Reject: entry opens stretched above EMA9, but the pullback from high was tiny
        if (
            entry_bar_open_to_ema_9 >= 1.0316
            and price_movement_from_highest_high_to_lowest_low <= 0.22
        ):
            return False

        # Reject: MACD recovery looks old/extended, but entry MACD weakens versus previous bar
        if (
            macd_recovery_followthrough_quality >= 18.7867
            and entry_bar_macd_to_previous <= 0.8328
        ):
            return False

        # Reject: weak entry body, but stock already has fast profit pace from open
        if (
            entry_bar_body <= 0.3877
            and profit_since_open_to_bars_count_since_open >= 0.00455
        ):
            return False

        # Reject: wick-volume rejection still present on a strong EMA20 day
        if (
            weak_wick_volume_rejection
            and current_ema20 >= 1.2131
        ):
            return False

        # Reject: large move from highest high to lowest low,
        # but entry close quality is weak versus previous bar
        if (
            price_movement_from_highest_high_to_lowest_low >= 5.9525
            and entry_close_position_vs_previous_close_position <= 0.83161232
        ):
            return False

        # Reject: weak body, weak recovery from low,
        # and MACD recovery/follow-through quality is not mature
        if (
            entry_bar_body <= 0.4061
            and entry_close_to_lowest_low_recovery <= 1.1066
            and macd_recovery_followthrough_quality <= 13.9401
        ):
            return False

        if (
            entry_bar_upper_wick >= 0.06666666667
            and pullback_depth_vs_pre_high_move >= 4.36527928
            and entry_bar_volume_to_recent_bars_average <= 2.253715889
        ):
            return False

        if (
            reclaim_close_strength_since_highest_high <= 0.173553719
            and pullback_depth_vs_pre_high_move >= 1.687493832
            and entry_close_position_vs_previous_close_position >= 4.728543479
        ):
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
        feature_entry_followthrough_after_near_reclaim = breakout_structure_features["feature_entry_close_to_previous_bar_close"]/max(breakout_structure_features["feature_previous_bar_close_to_highest_high"], 0.0001)

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
            "feature_entry_followthrough_after_near_reclaim": breakout_structure_features["feature_entry_close_to_previous_bar_close"]/max(breakout_structure_features["feature_previous_bar_close_to_highest_high"], 0.0001),
            "feature_entry_volume_spike_without_high_context": volume_structure_features["feature_entry_bar_volume_to_previous_bar_volume"]/max(volume_structure_features["feature_entry_bar_volume_to_highest_high_volume"], 0.0001),
            "feature_failed_pressure_to_followthrough": breakout_structure_features["feature_failed_attempts_pressure"]/max(feature_entry_followthrough_after_near_reclaim, 0.0001),
            "feature_near_high_weak_followthrough": breakout_structure_features["feature_previous_bar_close_to_highest_high"]/max(breakout_structure_features["feature_entry_close_to_previous_bar_close"], 0.0001),
            "feature_macd_recovery_followthrough_quality": macd_structure_features["feature_distance_from_last_negative_macd_bar"] * macd_structure_features["feature_entry_bar_macd_to_previous"] * feature_entry_followthrough_after_near_reclaim,
            "feature_volume_confirmation_quality": volume_structure_features["feature_entry_bar_volume_to_highest_high_volume"]/max(volume_structure_features["feature_entry_bar_volume_to_previous_bar_volume"], 0.0001),
            "feature_fake_reclaim_pressure": breakout_structure_features["feature_previous_bar_close_to_highest_high"] * breakout_structure_features["feature_failed_attempts_pressure"]/max(breakout_structure_features["feature_entry_close_to_previous_bar_close"], 0.0001),
        }

        features = base_features | complex_features | recent_days_structure_features | breakout_structure_features | volume_structure_features | macd_structure_features | pre_market_structure_features

        feature_overall_legit_trade = {
            "feature_overall_legit_trade": self.feature_overall_legit_trade(
                features_data=features,
            ),
        }

        features = features | feature_overall_legit_trade

        return features
