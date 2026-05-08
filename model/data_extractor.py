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

        previous_bar_already_crossed_highest_high = 1 if previous_bar.low < highest_high_one_minute_bar.high < previous_bar.close and previous_bar is not None else 0

        bars_movement = 0
        lowest_low_since_highest_high = 100
        total_bars_since_highest_high = len(bars_since_highest_high)
        breakout_attempts_during_pullback = 0
        for bar_object in bars_since_highest_high:
            bars_movement += bar_object.high - bar_object.close

            if bar_object.low < lowest_low_since_highest_high:
                lowest_low_since_highest_high = bar_object.low

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

        return {
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

        volume_sum = 0
        positive_volume = 0
        negative_volume = 0
        for bar_object in bars_since_highest_high:
            volume_sum += bar_object.volume

            if bar_object.is_positive:
                positive_volume += bar_object.volume
            else:
                negative_volume += bar_object.volume

        volume_average = 0
        if bars_since_highest_high:
            highest_volume_since_highest_high = max(
                bar_object.volume
                for bar_object in bars_since_highest_high
            )
            volume_average = volume_sum/total_bars_since_highest_high

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        entry_bar_volume_to_highest_volume_in_pullback = potential_confirmation_bar.volume/highest_volume_since_highest_high if highest_volume_since_highest_high > 0 else 1
        entry_bar_volume_to_volume_average = potential_confirmation_bar.volume/potential_confirmation_bar.volume_average
        entry_bar_volume_to_previous_bar_volume = potential_confirmation_bar.volume/previous_bar.volume if previous_bar is not None else 1

        return {
            "feature_entry_bar_volume_to_highest_volume_in_pullback": entry_bar_volume_to_highest_volume_in_pullback,
            "feature_entry_bar_volume_to_volume_average": entry_bar_volume_to_volume_average,
            "feature_entry_bar_volume_to_recent_bars_average": potential_confirmation_bar.volume/volume_average if volume_average else 1,
            "feature_entry_bar_volume_to_highest_high_volume": potential_confirmation_bar.volume/highest_high_one_minute_bar.volume,
            "feature_positive_vs_negative_volume_during_pullback": positive_volume/negative_volume if negative_volume > 0 else 1,
            "feature_entry_bar_volume_to_previous_bar_volume": entry_bar_volume_to_previous_bar_volume,
        }

    def macd_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        highest_high_one_minute_bar: common.objects.BarData,
        bars_since_highest_high: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> dict[str, float]:
        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        histogram_sum = 0
        highest_histogram_since_highest_high = 0
        lowest_histogram_since_highest_high = 100
        histogram_changed_to_positive_direction_count = 0
        histogram_changed_to_negative_direction_count = 0
        for bar_object in bars_since_highest_high:
            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )

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

    #pylint:disable=W0613
    def extract_features_from_symbol_data(
        self,
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        volume_sum_since_market_open: float,
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
        }
        complex_features = {
            "feature_weak_wick_volume_rejection": 1 if feature_upper_wick > 0.262 and feature_volume_to_previous <= 1.17 else 0,
            "feature_clean_breakout_efficiency": 1 if (
                breakout_structure_features["feature_entry_breakout_efficiency_from_ema_9"] >= 0.35
                and breakout_structure_features["feature_entry_breakout_efficiency_from_ema_9"] <= 0.80
                and breakout_structure_features["feature_entry_bar_body"] >= 0.75
                and breakout_structure_features["feature_entry_bar_upper_wick"] <= 0.15
            ) else 0,
            "feature_inefficient_breakout_extension": 1 if (
                breakout_structure_features["feature_entry_breakout_efficiency_from_ema_9"] < 0.20
                and breakout_structure_features["feature_entry_extension_pressure"] > 0.30
            ) else 0,
            "feature_strong_vwap_volume_reentry": 1 if (
                recent_days_structure_features["feature_current_day_vwap_to_recent_days"] > 2.28
                and breakout_structure_features["feature_entry_extension_pressure"] > 0.169
                and volume_structure_features["feature_entry_bar_volume_to_previous_bar_volume"] > 2.03
            ) else 0,
        }

        features = base_features | complex_features | recent_days_structure_features | breakout_structure_features | volume_structure_features | macd_structure_features | pre_market_structure_features

        return features

    def should_run_model_by_hard_rules(
        self,
        features_data: dict[str, float],
    ) -> bool:
        current_volume = features_data["feature_current_day_volume_to_recent_days_volume"]
        current_ema20 = features_data["feature_current_day_ema_20_to_recent_days_ema_20"]
        current_ema9_to_ema20 = features_data["feature_current_day_ema_9_to_ema_20"]
        current_vwap = features_data["feature_current_day_vwap_to_recent_days"]
        current_high_to_recent = features_data["feature_current_day_high_to_recent_days_highs"]
        current_high_to_previous = features_data["feature_current_day_high_to_previous_high"]
        gains_until_entry = features_data["feature_gains_until_entry_bar"]
        controlled_volume_quality = features_data["feature_controlled_volume_entry_quality"]
        entry_ema9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
        entry_extension_pressure = features_data["feature_entry_extension_pressure"]
        entry_volume_to_highest_high_volume = features_data["feature_entry_bar_volume_to_highest_high_volume"]
        pullback_pos_neg_volume = features_data["feature_positive_vs_negative_volume_during_pullback"]
        weak_wick_volume_rejection = features_data["feature_weak_wick_volume_rejection"]
        breakout_efficiency = features_data["feature_entry_breakout_efficiency_from_ema_9"]
        current_day_movement_to_recent_days = features_data["feature_current_day_movement_to_recent_days_movement"]
        entry_bar_upper_wick = features_data["feature_entry_bar_upper_wick"]

        # Reject: weak day context
        # Safe on current dataset: removed 0 positives, 13 false positives.
        if current_volume <= 1.114 and current_ema20 <= 1.363:
            return False

        # Reject: entry too extended
        # Changed extension threshold from 0.4078 -> 0.48.
        # Old version removed 2 positives. This version removed 0 positives.
        if entry_ema9_to_vwap > 1.091 and entry_extension_pressure > 0.48:
            return False

        # Reject: weak trend + weak controlled volume
        # Safe on current dataset: removed 0 positives, 14 false positives.
        if current_ema9_to_ema20 <= 1.261 and controlled_volume_quality <= 0.8753:
            return False

        # Reject: wick-volume rejection, but only if entry volume does not rescue it.
        # Old version removed 1 positive.
        # This version removed 0 positives and still caught the FP cases.
        if (
            weak_wick_volume_rejection
            and entry_volume_to_highest_high_volume <= 1.5
        ):
            return False

        # Reject: weak context + inefficient breakout + not enough relative volume.
        # Added current_volume > 2.0 to avoid rejecting one good positive case.
        if (
            current_vwap <= 1.36
            and breakout_efficiency <= 0.40
            and current_volume <= 145
            and current_volume > 2.0
        ):
            return False

        # Reject: weak current-day high context.
        # This replaces the bugged current_high_to_previous rule.
        # Uses feature_current_day_high_to_previous_high correctly.
        if (
            current_vwap <= 2.12
            and current_high_to_recent > 1.81
            and current_high_to_previous <= 1.40
            and gains_until_entry <= 0.70
            and breakout_efficiency <= 0.55
        ):
            return False

        # Reject: extended entry, but inefficient breakout
        # Safe on current dataset: removed 0 positives.
        if (
            breakout_efficiency <= 0.20
            and entry_ema9_to_vwap > 1.09
            and gains_until_entry > 0.60
        ):
            return False

        # Reject: very extended day, but weak breakout efficiency
        # Safe on current dataset: removed 0 positives.
        if (
            current_high_to_recent > 3.31
            and breakout_efficiency <= 0.40
            and gains_until_entry > 0.60
        ):
            return False

        # Reject: pullback demand failure
        # Changed volume threshold from 1.458 -> 1.0.
        # Old version removed 2 positives. This version removed 0 positives.
        if (
            entry_volume_to_highest_high_volume <= 1.0
            and pullback_pos_neg_volume <= 0
        ):
            return False

        # Reject: big current-day movement, but weak VWAP context
        if (
            current_vwap <= 1.42
            and current_day_movement_to_recent_days > 6.10
        ):
            return False

        # Reject: weak previous-high reclaim with high breakout-efficiency ratio
        if (
            current_high_to_previous <= 1.02
            and breakout_efficiency > 0.64
        ):
            return False

        # Reject: rejection wick with weak entry pressure
        if (
            entry_bar_upper_wick > 0.34
            and entry_extension_pressure <= 0.11
        ):
            return False

        return True
