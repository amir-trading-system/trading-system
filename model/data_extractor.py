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
        highest_high_one_minute_bar: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
    ) -> dict[str, float]:
        entry_bar_close_to_highest_high = potential_confirmation_bar.close/highest_high_one_minute_bar.high
        entry_bar_body = potential_confirmation_bar.body_percentage
        entry_bar_upper_wick = potential_confirmation_bar.bar_wick_percentage
        entry_bar_lower_wick = potential_confirmation_bar.bar_lower_wick_percentage
        entry_bar_volume_to_volume_average = potential_confirmation_bar.volume/potential_confirmation_bar.volume_average
        entry_bar_low_to_ema_9 = potential_confirmation_bar.low/potential_confirmation_bar.ema_9
        entry_bar_ema_9_to_ema_20 = potential_confirmation_bar.ema_9/potential_confirmation_bar.ema_20
        entry_bar_ema_9_to_vwap = potential_confirmation_bar.ema_9/potential_confirmation_bar.vwap
        distance_from_highest_high = highest_high_one_minute_bar.index - potential_confirmation_bar.index

        bars_since_highest_high = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if highest_high_one_minute_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        volume_sum = 0
        bars_movement = 0
        positive_volume = 0
        negative_volume = 0
        lowest_low_since_highest_high = 100
        total_bars_since_highest_high = len(bars_since_highest_high)
        breakout_attempts_during_pullback = 0
        for bar_object in bars_since_highest_high:
            volume_sum += bar_object.volume
            bars_movement += bar_object.high - bar_object.close

            if bar_object.low < lowest_low_since_highest_high:
                lowest_low_since_highest_high = bar_object.low

            if bar_object.is_positive:
                positive_volume += bar_object.volume
            else:
                negative_volume += bar_object.volume

            if (
                True
                and bar_object.high/highest_high_one_minute_bar.high > 0.99
                and bar_object.volume > bar_object.volume_average
            ):
                breakout_attempts_during_pullback += 1

        volume_average = 0
        bars_movement_average = 0
        if bars_since_highest_high:
            volume_average = volume_sum/total_bars_since_highest_high
            bars_movement_average = bars_movement/total_bars_since_highest_high

        entry_bar_movement_recent_bars_average = (potential_confirmation_bar.high - potential_confirmation_bar.low)/bars_movement_average if bars_movement_average > 0 else 1
        entry_extension_pressure = entry_bar_ema_9_to_vwap / (entry_bar_movement_recent_bars_average + 1e-6)

        return {
            "feature_entry_bar_close_to_highest_high": entry_bar_close_to_highest_high,
            "feature_entry_bar_body": entry_bar_body,
            "feature_entry_bar_upper_wick": entry_bar_upper_wick,
            "feature_entry_bar_lower_wick": entry_bar_lower_wick,
            "feature_entry_bar_volume_to_volume_average": entry_bar_volume_to_volume_average,
            "feature_entry_bar_low_to_ema_9": entry_bar_low_to_ema_9,
            "feature_entry_bar_ema_9_to_ema_20": entry_bar_ema_9_to_ema_20,
            "feature_entry_bar_ema_9_to_vwap": entry_bar_ema_9_to_vwap,
            "feature_distance_from_highest_high": distance_from_highest_high,
            "feature_entry_bar_volume_to_recent_bars_average": potential_confirmation_bar.volume/volume_average if volume_average else 1,
            "feature_entry_bar_movement_recent_bars_average": entry_bar_movement_recent_bars_average,
            "feature_entry_extension_pressure": entry_extension_pressure,
            "feature_entry_bar_volume_to_highest_high_volume": potential_confirmation_bar.volume/highest_high_one_minute_bar.volume,
            "feature_positive_vs_negative_volume_during_pullback": positive_volume/negative_volume if negative_volume > 0 else 1,
            "feature_breakout_attempts_during_pullback": breakout_attempts_during_pullback,
        }

    def volume_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ):
        pass

    def macd_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ):
        pass

    def pre_market_structure_features(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ):
        pass

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
        recent_days_structure_features = self.recent_days_structure_features(
            day_timeframe_stock=day_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )
        breakout_structure_features = self.breakout_structure_features(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        base_features = {
            "highest_high_one_minute_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else datetime.datetime.fromtimestamp(0),
        }

        features = base_features | recent_days_structure_features | breakout_structure_features

        return features

    def should_run_model_by_hard_rules(
        self,
        features_data: dict[str,float],
    ) -> bool:
        current_volume = features_data["feature_current_day_volume_to_recent_days_volume"]
        current_ema20 = features_data["feature_current_day_ema_20_to_recent_days_ema_20"]
        current_ema9_to_ema20 = features_data["feature_current_day_ema_9_to_ema_20"]

        controlled_volume_quality = features_data["feature_controlled_volume_entry_quality"]

        entry_ema9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
        entry_extension_pressure = features_data["feature_entry_extension_pressure"]

        entry_volume_to_highest_high_volume = features_data["feature_entry_bar_volume_to_highest_high_volume"]
        pullback_pos_neg_volume = features_data["feature_positive_vs_negative_volume_during_pullback"]

        # Reject: weak day context
        if current_volume <= 1.114 and current_ema20 <= 1.363:
            return False

        # Reject: entry too extended
        if entry_ema9_to_vwap > 1.091 and entry_extension_pressure > 0.4078:
            return False

        # Reject: weak trend + weak controlled volume
        if current_ema9_to_ema20 <= 1.261 and controlled_volume_quality <= 0.8753:
            return False

        # Reject: pullback demand failure
        if (
            entry_volume_to_highest_high_volume <= 1.458
            and pullback_pos_neg_volume <= 0
        ):
            return False

        return True
