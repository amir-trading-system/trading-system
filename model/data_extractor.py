import datetime

import common


class DataExtractor:
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
        positive_volume_sum = 0
        negative_volume_sum = 0
        positive_histograms_sum = 0
        negative_histograms_sum = 0
        positive_bars_counter = 0
        negative_bars_counter = 0
        last_bars_positive_bars = 0
        last_bars_negative_bars = 0
        bars_with_at_least_50_pct_wick_counter = 0
        strong_positive_bars_with_full_body_counter = 0
        macd_under_signal_line_counter = 0
        ema_9_keeps_going_up_counter = 0
        strong_bars_counter = 0
        bars_after_strong_bars_that_continues_trend_counter = 0
        bars_with_rejection_inside_entry_bar_range: list[common.objects.BarData] = []
        bars_with_highest_volume: list[common.objects.BarData] = []
        bars_above_vwap_counter = 0
        bars_ema_above_vwap_counter = 0
        positive_bars_close_strong_counter = 0
        bars_with_rejection_since_market_open = 0
        bars_size_sum = 0
        bars_size_average = 0
        histogram_changed_directions_counter = 0
        strong_negative_bars_counter = 0
        price_action_is_stuck_counter = 0
        highest_volume_average = 0
        bars_with_rejection_counter = 0
        overlapped_bars_counter = 0
        bars_since_highest_high: list[common.objects.BarData] = []
        volume_to_volume_average_ratio_since_highest_high = 0

        for bar_object in one_minute_bars:
            if bar_object.bar_time < potential_confirmation_bar.bar_time:
                bars_size_sum += abs(bar_object.close - bar_object.open_value)
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
                and previous_bar is not None
                and previous_bar.low <= bar_object.open_value <= previous_bar.high
                and previous_bar.low <= bar_object.close <= previous_bar.high
            ):
                overlapped_bars_counter += 1

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

            if (
                previous_bar is not None
                and next_bar is not None
                and bar_object.histogram < previous_bar.histogram
                and bar_object.histogram < next_bar.histogram
            ):
                histogram_changed_directions_counter += 1

            if highest_high_one_minute_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time:
                bars_since_highest_high.append(bar_object)
                volume_to_volume_average_ratio_since_highest_high += bar_object.volume/bar_object.volume_average

            if (
                True
                and previous_bar is not None
                and bar_object.volume > bar_object.volume_average
            ):
                if (
                    previous_bar.high > bar_object.high
                    and bar_object.high/previous_bar.high >= 0.98
                ):
                    price_action_is_stuck_counter += 1
                if (
                    previous_bar.high < bar_object.high
                    and (
                        previous_bar.high/bar_object.high >= 0.98
                        or previous_bar.high/bar_object.close >= 0.98
                    )
                ):
                    price_action_is_stuck_counter += 1

            if bar_object.macd < bar_object.signal_line:
                macd_under_signal_line_counter += 1

            if (
                True
                and previous_bar is not None
                and bar_object.bar_wick_percentage >= 0.1
                and bar_object.volume > bar_object.volume_average
                and previous_bar.high < bar_object.high
            ):
                bars_with_rejection_since_market_open += 1

            if bar_object.bar_wick_percentage >= 0.5:
                bars_with_at_least_50_pct_wick_counter += 1

            if bar_object.histogram > 0:
                positive_histograms_sum += bar_object.histogram
            else:
                negative_histograms_sum += abs(bar_object.histogram)

            if is_positive:
                positive_volume_sum += bar_object.volume
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_positive_bars += 1
                if bar_object.body_percentage >= 0.75:
                    strong_positive_bars_with_full_body_counter += 1
                if bar_object.bar_wick_percentage <= 0.1:
                    positive_bars_close_strong_counter += 1
                if bar_object.close > bar_object.vwap:
                    positive_bars_counter += 1
            else:
                negative_volume_sum += bar_object.volume
                if bar_object.index - 5 < potential_confirmation_bar.index:
                    last_bars_negative_bars += 1
                if bar_object.close > bar_object.vwap:
                    negative_bars_counter += 1
                if (
                    True
                    and bar_object.high > bar_object.vwap
                    and above_volume_average
                    and bar_object.body_percentage > 0.3
                ):
                    strong_negative_bars_counter += 1

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

            if bar_object.close > bar_object.vwap:
                bars_above_vwap_counter += 1

            if (
                True
                and bar_object.ema_9 > bar_object.vwap
                and bar_object.ema_20 > bar_object.vwap
                and bar_object.ema_9 >= bar_object.ema_20
            ):
                bars_ema_above_vwap_counter += 1

        feature_bars_with_at_least_50_pct_wick_pct = bars_with_at_least_50_pct_wick_counter/total_bars

        previous_bar_to_entry_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )
        feature_overlapped_bars_since_market_open_pct = overlapped_bars_counter/len(one_minute_bars)

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

        feature_distance_from_highest_high_since_market_open = highest_high_bar_since_market_open.index - potential_confirmation_bar.index if highest_high_bar_since_market_open is not None else 0
        bars_size_average = bars_size_sum/(total_bars-1) if total_bars > 1 else 1
        feature_current_macd_to_previous = 0
        if previous_bar_to_entry_bar is not None:
            feature_current_macd_to_previous = potential_confirmation_bar.macd/previous_bar_to_entry_bar.macd

        previous_bar_is_highest = False
        if previous_bar_to_entry_bar is not None and previous_bar_to_entry_bar.is_after_market_open:
            relevant_bars = [b for b in one_minute_bars if b.bar_time < previous_bar_to_entry_bar.bar_time]
            if relevant_bars:
                previous_bar_is_highest = max(
                    b.high
                    for b in relevant_bars
                ) < previous_bar_to_entry_bar.high

        feature_entry_bar_shape_is_good = (
            True
            and previous_bar_to_entry_bar.is_after_market_open
            and not previous_bar_is_highest
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.ema_20 > potential_confirmation_bar.vwap
            and 0.95 < potential_confirmation_bar.ema_9/potential_confirmation_bar.open_value < 1.05
            and potential_confirmation_bar.body_percentage > 0.5
            and (potential_confirmation_bar.open_value - potential_confirmation_bar.low)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value) < 0.4
            and bars_with_rejection_counter < 3
        )
        feature_late_volume_spike = potential_confirmation_bar.volume/total_volume
        feature_entry_volume_vs_total_volume = potential_confirmation_bar.volume/(total_volume - potential_confirmation_bar.volume) if (total_volume - potential_confirmation_bar.volume) > 0 else 0
        feature_entry_bar_price_action_to_total_price_pct = (potential_confirmation_bar.high - potential_confirmation_bar.low)/potential_confirmation_bar.close

        features = {
            "feature_bars_with_at_least_50_pct_wick_pct": feature_bars_with_at_least_50_pct_wick_pct,
            "feature_positive_vs_negative_volume": positive_volume_sum/negative_volume_sum if negative_volume_sum > 0 else 1,
            "feature_overlapped_bars_since_market_open_pct": feature_overlapped_bars_since_market_open_pct,
            "feature_distance_from_highest_high_since_market_open": feature_distance_from_highest_high_since_market_open,
            "feature_entry_bar_lowest_wick_to_bar_body_pct": (potential_confirmation_bar.open_value - potential_confirmation_bar.low)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value) if potential_confirmation_bar.close - potential_confirmation_bar.open_value > 0 else 0,
            "feature_entry_bar_volume": potential_confirmation_bar.volume,
            "feature_distance_from_highest_high": highest_high_bar_since_market_open.index - potential_confirmation_bar.index if highest_high_bar_since_market_open is not None else 0,
            "feature_bars_with_rejection_since_market_open": bars_with_rejection_since_market_open/total_bars,
            "feature_entry_point_size_to_bars_size_average": (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/bars_size_average if bars_size_average else 0,
            "feature_histogram_changed_directions_pct": histogram_changed_directions_counter/total_bars,
            "feature_strong_negative_bars_pct": strong_negative_bars_counter/negative_bars_counter if negative_bars_counter > 0 else 0,
            "feature_price_action_is_stuck_pct": price_action_is_stuck_counter/total_bars,
            "feature_entry_bar_close_to_crossed_highest_high_pct": potential_confirmation_bar.close/highest_high_one_minute_bar.high,
            "feature_total_volume": total_volume,
            "feature_current_macd_to_previous": feature_current_macd_to_previous,
            "feature_entry_bar_shape_is_good": feature_entry_bar_shape_is_good,
            "feature_late_volume_spike": feature_late_volume_spike,
            "feature_late_momentum_score": feature_late_volume_spike/highest_high_one_minute_bar.index if highest_high_one_minute_bar else 0,
            "feature_entry_bar_price_action_to_total_price_pct": feature_entry_bar_price_action_to_total_price_pct,
            "feature_entry_volume_vs_total_volume": feature_entry_volume_vs_total_volume,
            "feature_entry_bar_price_action_pct_to_volume_pct": feature_entry_bar_price_action_to_total_price_pct/feature_entry_volume_vs_total_volume if feature_entry_volume_vs_total_volume > 0 else 0,
        }

        return features
