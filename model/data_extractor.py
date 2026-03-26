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
        stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
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
        bars_above_vwap_counter = 0
        bars_with_lower_volume_average_counter = 0
        bars_with_highest_volume: list[common.objects.BarData] = []

        for bar_object in one_minute_bars:
            total_volume += bar_object.volume
            is_positive = bar_object.close > bar_object.open_value

            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )

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

            if (
                True
                and (
                    previous_bar is not None
                    and bar_object.histogram < previous_bar.histogram
                )
            ):
                bars_with_negative_momentum_histogram_counter += 1

            if bar_object.close > bar_object.vwap:
                bars_above_vwap_counter += 1

            if (
                True
                and previous_bar is not None
                and previous_bar.volume_average > bar_object.volume_average
            ):
                bars_with_lower_volume_average_counter += 1

            if (
                True
                and bar_object.volume > bar_object.volume_average
                and bar_object.close > bar_object.vwap
            ):
                bars_with_highest_volume.append(bar_object)

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

        feature_last_bars_buyers_coming_in = 0
        last_bars_positive_bars = 0
        last_bars_negative_bars = 0
        last_bars_positive_volume = 0
        last_bars_negative_volume = 0

        for bar_object in one_minute_bars[:10]:
            if bar_object.close > bar_object.open_value:
                last_bars_positive_bars += 1
                last_bars_positive_volume += bar_object.volume
            else:
                previous_bar = one_minute_timeframe_stock.previous_bar(
                    bar_object=bar_object,
                )
                if (
                    previous_bar is not None
                    and previous_bar.low < bar_object.low
                    and previous_bar.volume > bar_object.volume
                ):
                    last_bars_positive_bars += 1
                    last_bars_positive_volume += bar_object.volume
                else:
                    last_bars_negative_bars += 1
                    last_bars_negative_volume += bar_object.volume

        feature_histogram_negative_momentum_pct = bars_with_negative_momentum_histogram_counter/total_bars
        feature_bars_with_at_least_50_pct_wick_pct = bars_with_at_least_50_pct_wick_counter/total_bars
        feature_strong_positive_bars_with_full_body_pct = strong_positive_bars_with_full_body_counter/positive_bars_counter if positive_bars_counter > 0 else 0
        feature_minutes_since_market_open_to_total_market_minutes_pct = minutes_since_market_open/390
        feature_last_bars_buyers_coming_in = 1 if (
            True
            and last_bars_positive_bars > last_bars_negative_bars
            and last_bars_positive_volume > last_bars_negative_volume
        ) else 0
        feature_bars_with_lower_volume_average_pct = bars_with_lower_volume_average_counter/total_bars
        feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = bar_volume_close_to_entry_point_sum > bar_volume_close_to_market_open_sum

        features = {
            "feature_has_positive_more_than_negative_bars": positive_bars_counter > negative_bars_counter,
            "feature_has_more_positive_volume_than_negative": positive_volume_sum > negative_volume_sum,
            "feature_open_close_to_ema_9": 0.95 < potential_confirmation_bar.open_value/potential_confirmation_bar.ema_9 < 1.1,
            "feature_most_of_bars_above_vwap": bars_above_vwap_counter/total_bars > 0.5,
            "feature_pullback_sharpness": pullback_analysis["feature_pullback_sharpness"],
            "feature_pullback_depth": pullback_analysis["feature_pullback_depth"],
            "feature_number_of_negative_bars_in_pullback_pct": pullback_analysis["feature_number_of_negative_bars_in_pullback_pct"],
            "feature_price_minus_vwap_at_entry": potential_confirmation_bar.close - potential_confirmation_bar.vwap,
            "feature_pullback_to_trend_ratio": pullback_analysis["feature_pullback_to_trend_ratio"],
            "feature_histogram_negative_momentum_pct": feature_histogram_negative_momentum_pct,
            "feature_strong_positive_bars_with_full_body_pct": feature_strong_positive_bars_with_full_body_pct,
            "feature_minutes_since_market_open_to_total_market_minutes_pct": feature_minutes_since_market_open_to_total_market_minutes_pct,
            "feature_bars_with_at_least_50_pct_wick_pct": feature_bars_with_at_least_50_pct_wick_pct,
            "feature_last_bars_buyers_coming_in": feature_last_bars_buyers_coming_in,
            "feature_bars_with_lower_volume_average_pct": feature_bars_with_lower_volume_average_pct,
            "feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open": feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open,
        }

        return features
