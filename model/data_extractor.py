import copy
import datetime

import common


class DataExtractor:
    @staticmethod
    def safe_div(
        numerator: float,
        denominator: float,
        default: float = 0.0,
    ) -> float:
        if denominator is None or denominator == 0:
            return default
        return numerator / denominator

    @staticmethod
    def pct_diff(
        current: float,
        previous: float,
    ) -> float:
        if previous is None or previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100


    #pylint:disable=W0613
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
        positive_histograms_sum = 0
        negative_histograms_sum = 0
        positive_bars_counter = 0
        last_bars_positive_bars = 0
        last_bars_negative_bars = 0
        strong_positive_bars_with_full_body_counter = 0
        macd_under_signal_line_counter = 0
        ema_9_keeps_going_up_counter = 0
        strong_bars_counter = 0
        bars_after_strong_bars_that_continues_trend_counter = 0
        bars_with_rejection_inside_entry_bar_range: list[common.objects.BarData] = []
        bars_with_highest_volume: list[common.objects.BarData] = []
        bars_ema_above_vwap_counter = 0
        positive_bars_close_strong_counter = 0
        price_action_is_stuck_counter = 0
        highest_volume_average = 0
        bars_with_rejection_counter = 0
        positive_bars_above_volume_average_counter = 0
        bars_since_highest_high: list[common.objects.BarData] = []
        highest_volume_until_now = 0

        for bar_object in one_minute_bars:
            total_volume += bar_object.volume
            is_positive = bar_object.close > bar_object.open_value
            above_volume_average = bar_object.volume > bar_object.volume_average
            above_vwap = bar_object.close > bar_object.vwap
            above_9_ema = bar_object.close > bar_object.ema_9
            if bar_object.volume_average > highest_volume_average:
                highest_volume_average = bar_object.volume_average

            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )

            if (
                True
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.is_after_market_open
                and bar_object.index - potential_confirmation_bar.index < 10
                and bar_object.high > previous_bar.high
                and bar_object.high > next_bar.high
                and bar_object.volume > bar_object.volume_average
                and bar_object.volume > next_bar.volume
                and bar_object.volume > previous_bar.volume
                and bar_object.bar_wick_percentage > 0.1
            ):
                bars_with_rejection_counter += 1

            if (
                True
                and next_bar is not None
                and bar_object.index - potential_confirmation_bar.index < 10
                and not next_bar.is_positive
                and bar_object.is_positive
                and above_volume_average
                and above_9_ema
                and above_vwap
                and next_bar.volume > next_bar.volume_average
                and next_bar.close < bar_object.low
            ):
                bars_with_rejection_counter += 1

            if highest_high_one_minute_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time:
                bars_since_highest_high.append(bar_object)

            if (
                True
                and previous_bar is not None
                and bar_object.volume > bar_object.volume_average
            ):
                if (
                    True
                    and previous_bar.low <= bar_object.close <= previous_bar.high
                    and previous_bar.low <= bar_object.open_value <= previous_bar.high
                ):
                    price_action_is_stuck_counter += 1

            if bar_object.macd < bar_object.signal_line:
                macd_under_signal_line_counter += 1

            if bar_object.histogram > 0:
                positive_histograms_sum += bar_object.histogram
            else:
                negative_histograms_sum += abs(bar_object.histogram)

            if is_positive:
                positive_bars_counter += 1
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_positive_bars += 1
                if bar_object.body_percentage >= 0.75:
                    strong_positive_bars_with_full_body_counter += 1
                if bar_object.bar_wick_percentage <= 0.3 and bar_object.above_volume_average:
                    positive_bars_close_strong_counter += 1
                if bar_object.above_volume_average:
                    positive_bars_above_volume_average_counter += 1
            else:
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_negative_bars += 1

            if previous_bar is not None:
                if previous_bar.ema_9 < bar_object.ema_9:
                    ema_9_keeps_going_up_counter += 1

            if (
                True
                and above_volume_average
                and bar_object.close > bar_object.vwap
            ):
                bars_with_highest_volume.append(bar_object)

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
                and above_vwap
                and above_9_ema
                and bar_object.close > bar_object.ema_20
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high < bar_object.high
                and next_bar.high < bar_object.high
            ):
                bars_with_rejection_inside_entry_bar_range.append(bar_object)

            if (
                True
                and bar_object.ema_9 > bar_object.vwap
                and bar_object.ema_20 > bar_object.vwap
                and bar_object.ema_9 >= bar_object.ema_20
            ):
                bars_ema_above_vwap_counter += 1

            if (
                True
                and bar_object.index > potential_confirmation_bar.index
                and bar_object.volume > highest_volume_until_now
            ):
                highest_volume_until_now = bar_object.volume

        previous_bar_to_entry_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        highest_high_one_minute_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=potential_confirmation_bar,
        )

        feature_entry_volume_vs_total_volume = potential_confirmation_bar.volume/(total_volume - potential_confirmation_bar.volume) if (total_volume - potential_confirmation_bar.volume) > 0 else 0
        feature_entry_bar_price_action_to_total_price_pct = (potential_confirmation_bar.high - potential_confirmation_bar.low)/potential_confirmation_bar.close

        potential_resistances = copy.deepcopy(day_timeframe_stock.resistance_levels)
        potential_resistances.append(highest_high_one_minute_bar)
        crossed_resistance = [
            r_l
            for r_l in potential_resistances
            if potential_confirmation_bar.low < r_l.high < potential_confirmation_bar.close
        ]

        feature_distance_between_highest_high_to_entry_bar_high = 0
        if crossed_resistance:
            feature_distance_between_highest_high_to_entry_bar_high = (potential_confirmation_bar.high - crossed_resistance[0].high)/(potential_confirmation_bar.high - potential_confirmation_bar.low)

        feature_price_action_is_stuck_pct = price_action_is_stuck_counter/total_bars
        feature_entry_bar_price_action_pct_to_volume_pct = feature_entry_bar_price_action_to_total_price_pct/feature_entry_volume_vs_total_volume if feature_entry_volume_vs_total_volume > 0 else 0

        feature_volume_quality = (potential_confirmation_bar.volume/highest_volume_until_now) * feature_entry_bar_price_action_pct_to_volume_pct if highest_volume_until_now > 0 else 0
        entry_bar_buyers_vs_sellers_pct = (potential_confirmation_bar.close - potential_confirmation_bar.low)/(potential_confirmation_bar.high - potential_confirmation_bar.low)
        feature_positive_bars_above_volume_average_pct = positive_bars_above_volume_average_counter/positive_bars_counter
        feature_volume_multiply_price_action = feature_volume_quality * feature_entry_bar_price_action_pct_to_volume_pct

        features = {
            "highest_high_one_minute_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else datetime.datetime.fromtimestamp(0),
            "feature_price_action_is_stuck_pct": feature_price_action_is_stuck_pct,
            "feature_total_volume": total_volume,
            "feature_entry_bar_price_action_pct_to_volume_pct": feature_entry_bar_price_action_pct_to_volume_pct,
            "feature_distance_between_highest_high_to_entry_bar_high": feature_distance_between_highest_high_to_entry_bar_high,
            "feature_positive_bars_above_volume_average_pct": feature_positive_bars_above_volume_average_pct,
            "feature_volume_quality": feature_volume_quality,
            "feature_previous_historgam_to_current_histogram": previous_bar_to_entry_bar.histogram/potential_confirmation_bar.histogram if previous_bar_to_entry_bar is not None else 0,
            "feature_efficiency_balance": feature_entry_bar_price_action_pct_to_volume_pct/(1+feature_price_action_is_stuck_pct),
            "feature_trap_signal": entry_bar_buyers_vs_sellers_pct/(feature_volume_quality + 1e-6),
            "feature_clean_move": feature_entry_bar_price_action_pct_to_volume_pct * (1 - feature_price_action_is_stuck_pct),
            "feature_fake_momentum": feature_entry_bar_price_action_pct_to_volume_pct / (feature_positive_bars_above_volume_average_pct + 1e-6),
            "feature_structure_adjusted_strength": feature_volume_multiply_price_action * feature_distance_between_highest_high_to_entry_bar_high,
        }

        return features
