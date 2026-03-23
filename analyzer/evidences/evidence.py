import datetime
from statistics import mean

from bisect import bisect_right
import numpy

import common

class Evidence:
    name: str = ""
    relevant_bars: list[common.objects.BarData] = []

    def is_potential_starting_bar(
        self,
        stock: common.objects.Stock,
        bar_object: common.objects.BarData,
    ) -> bool:
        base_condition = True
        previous_bar = stock.previous_bar(
            bar_object=bar_object,
        )
        if previous_bar is not None:
            base_condition = (
                True
                and base_condition
                and previous_bar is not None
                and bar_object.high > previous_bar.high
            )

        first_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.close > bar_object.ema_9
            and bar_object.close > bar_object.ema_20
            and bar_object.volume > bar_object.volume_average
            and bar_object.volume > 500000
            and bar_object.high > bar_object.vwap
            and bar_object.ema_9/bar_object.low >= 0.9
        )
        second_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.high > bar_object.vwap
            and bar_object.close > bar_object.ema_9
            and bar_object.histogram > 0
            and bar_object.volume/bar_object.volume_average > 7
            and max(
                stock.bars[bar_object.index:],
                key=lambda bar_obj: bar_obj.volume
            ) == bar_object
        )

        return first_option or second_option

    def get_starting_bar(
        self,
        stock: common.objects.Stock,
    ) -> common.objects.MilestoneBar | None:
        for bar_object in self.relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            potential_starting_bar = (
                True
                and self.is_potential_starting_bar(
                    stock=stock,
                    bar_object=bar_object
                )
                and (
                    not self.is_potential_starting_bar(
                        stock=stock,
                        bar_object=previous_bar,
                    ) if previous_bar is not None else True
                )
            )
            if potential_starting_bar:
                if len(self.relevant_bars[:10]) > 0:
                    potential_starting_bar = max(
                        [
                            bar_obj.high
                            for bar_obj in self.relevant_bars[:10]
                        ]
                    ) == bar_object.high

                return common.objects.MilestoneBar(
                    index=bar_object.index,
                    bar_object=bar_object,
                    bar_type=common.objects.MilestoneType.STARTING_BAR,
                    bar_time=bar_object.bar_time,
                    timeframe=bar_object.timeframe,
                )

    def get_top_bar(
        self,
        starting_bar: common.objects.BarData,
        current_bar: common.objects.BarData,
    ) -> common.objects.MilestoneBar | None:
        top_bar_options = [
            bar_object
            for bar_object in self.relevant_bars[:starting_bar.index]
            if (
                True
                and bar_object.index > current_bar.index
                and bar_object.high > starting_bar.high
                and len(self.relevant_bars[1:starting_bar.index]) > 0
                and bar_object.high == max(
                    [
                        bar_obj.high
                        for bar_obj in self.relevant_bars[:starting_bar.index]
                        if bar_obj.index > current_bar.index
                    ]
                )
            )
        ]
        if len(top_bar_options) > 0:
            top_bar = top_bar_options[0]
            return common.objects.MilestoneBar(
                index=top_bar.index,
                bar_object=top_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=top_bar.bar_time,
                timeframe=top_bar.timeframe,
            )

    def pre_process(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
    ) -> bool:
        self.relevant_bars = stock.bars[1:]
        if len(self.relevant_bars) == 0:
            return False

        stock.resistance_levels = self.get_resistance_levels(
            stock=stock,
            relevant_bars=self.relevant_bars,
            current_bar=current_bar,
        )

        return True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        raise NotImplementedError()

    def get_resistance_levels(
        self,
        stock: common.objects.Stock,
        relevant_bars: list[common.objects.BarData],
        current_bar: common.objects.BarData,
    ) -> list[common.objects.BarData]:
        resistance_levels: list[common.objects.BarData] = []
        for bar_object in relevant_bars[:current_bar.index+40]:
            if (
                bar_object.vwap is None
                or bar_object.ema_9 is None
                or bar_object.ema_20 is None
            ):
                continue

            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )

            high_pattern_one = (
                True
                and bar_object.high > bar_object.close
                and bar_object.high > bar_object.open_value
                and (bar_object.high - bar_object.close)/(bar_object.high - bar_object.low) >= 0.1
                and bar_object.high > bar_object.ema_9
                and bar_object.high > bar_object.ema_20
                and bar_object.high > bar_object.vwap
                and previous_bar is not None
                and previous_bar.high < bar_object.high
            )
            high_pattern_two = (
                True
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high < bar_object.high > next_bar.high
            )

            if (
                True
                and (high_pattern_one or high_pattern_two)
            ):
                resistance_level = [
                    r_l
                    for r_l in resistance_levels
                    if bar_object.high == r_l.high
                ]
                if not resistance_level:
                    resistance_levels.append(bar_object)

        resistance_levels = sorted(
            resistance_levels,
            key=lambda r_l: r_l.high,
        )
        temp_resistance_levels = [temp_r_l for temp_r_l in resistance_levels]
        for i, resistance_level in enumerate(temp_resistance_levels):
            if i+1 > len(resistance_levels) - 1:
                continue

            if resistance_level.high/resistance_levels[i+1].high >= 0.95:
                resistance_levels = [
                    r_l
                    for r_l in resistance_levels
                    if r_l.bar_time != resistance_level.bar_time
                ]

        return resistance_levels

    def crossed_resistance_level_strongly(
        self,
        resistance_levels: list[common.objects.BarData],
        highest_high_one_minute_bar: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        crossed_resistance_level_strongly: bool = False

        for resistance_level in resistance_levels:
            if (
                potential_confirmation_bar.low < resistance_level.high < potential_confirmation_bar.close
                and abs(resistance_level.high - potential_confirmation_bar.open_value) > 0
                and (potential_confirmation_bar.close - resistance_level.high)/abs(resistance_level.high - potential_confirmation_bar.open_value) >= 0.25
                and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
                and potential_confirmation_bar.volume > 10000
            ) and not any(
                resistance_level
                for resistance_level in resistance_levels
                if resistance_level.high >= potential_confirmation_bar.high
                and potential_confirmation_bar.high/resistance_level.high >= 0.8
            ) and not any(
                r_l
                for r_l in resistance_levels
                if resistance_level.high < r_l.high
                and resistance_level.index > r_l.index
            ):
                crossed_resistance_level_strongly = True
                break

        higher_resistance_levels_count = len(
            [
                r_l
                for r_l in resistance_levels
                if r_l.high > potential_confirmation_bar.high
            ]
        )

        if (
            True
            and not crossed_resistance_level_strongly
            and higher_resistance_levels_count/len(resistance_levels) <= 1
            and len(resistance_levels) > 1
            and potential_confirmation_bar.bar_time - datetime.timedelta(minutes=10) > highest_high_one_minute_bar.bar_time
            and potential_confirmation_bar.high - potential_confirmation_bar.low > 0.0
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.75
            and potential_confirmation_bar.close > highest_high_one_minute_bar.high
            and (potential_confirmation_bar.close - highest_high_one_minute_bar.high)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.4
            and not any(
                r_l
                for r_l in resistance_levels
                if potential_confirmation_bar.high/r_l.high >= 0.95
                and potential_confirmation_bar.high < r_l.high
            )
        ):
            crossed_resistance_level_strongly = True

        return crossed_resistance_level_strongly

    def symbol_statistics(
        self,
        stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        lowest_low_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, float]:
        number_of_green_bars_last_5 = 0
        number_of_red_bars_last_5 = 0
        for bar_object in one_minute_bars[1:6]:
            if bar_object.close > bar_object.open_value:
                number_of_green_bars_last_5 += 1
            else:
                number_of_red_bars_last_5 += 1

        third_bar = one_minute_timeframe_stock.bars[potential_confirmation_bar.index+3]
        fifth_bar = one_minute_timeframe_stock.bars[potential_confirmation_bar.index+5]

        symbol_statistics = {
            "positive_movement_since_market_open": 0.0,
            "negative_movement_since_market_open": 0.0,
            "movement_above_vwap_since_market_open": 0.0,
            "movement_under_vwap_since_market_open": 0.0,
            "movement_above_volume_average_counter_since_market_open": 0,
            "movement_under_volume_average_counter_since_market_open": 0,
            "highest_histogram_since_market_open": 0.0,
            "lowest_histogram_since_market_open": 1.0,
            "pullback_sharpness": 0.0,
            "pullback_duration": 0,
            "pullback_depth": 0.0,
            "histogram_at_entry": potential_confirmation_bar.histogram,
            "price_minus_vwap_at_entry": potential_confirmation_bar.close - potential_confirmation_bar.vwap,
            "entry_volume_spike_3": potential_confirmation_bar.volume/potential_confirmation_bar.volume_average_last_3 if potential_confirmation_bar.volume_average_last_3 is not None and potential_confirmation_bar.volume_average_last_3 != 0 else 0.0,
            "entry_volume_spike_5": potential_confirmation_bar.volume/potential_confirmation_bar.volume_average_last_3 if potential_confirmation_bar.volume_average_last_3 is not None and potential_confirmation_bar.volume_average_last_5 != 0 else 0.0,
            "minutes_since_market_open": ((potential_confirmation_bar.bar_time.hour - 9) * 60) + potential_confirmation_bar.bar_time.minute - 30,
            "distance_from_recent_high": (highest_high_one_minute_bar.high - potential_confirmation_bar.open_value) / highest_high_one_minute_bar.high,
            "distance_from_high_of_day": (original_bar_to_confirm.high - potential_confirmation_bar.close) / original_bar_to_confirm.high,
            "volume_trend": potential_confirmation_bar.volume_average_last_3/potential_confirmation_bar.volume_average_last_10,
            "number_of_negative_bars": 0,
            "broke_high_of_day_at_entry": 1 if potential_confirmation_bar.close >= highest_high_one_minute_bar.high else 0,
            "vwap_slope_3": (potential_confirmation_bar.vwap - third_bar.vwap) / third_bar.vwap,
            "vwap_slope_5": (potential_confirmation_bar.vwap - fifth_bar.vwap) / fifth_bar.vwap,
            "ema9_minus_vwap_at_entry": potential_confirmation_bar.ema_9 - potential_confirmation_bar.vwap,
            "ema9_minus_ema20_at_entry": potential_confirmation_bar.ema_9 - potential_confirmation_bar.ema_20,
            "number_of_green_bars_last_5": number_of_green_bars_last_5,
            "number_of_red_bars_last_5": number_of_red_bars_last_5,
            "distance_from_premarket_high": stock.pre_market_one_minute_highest_high_bar.index - potential_confirmation_bar.index if stock.pre_market_one_minute_highest_high_bar is not None else 0.0,
            "entry_bar_range_pct": (potential_confirmation_bar.high - potential_confirmation_bar.low)/ potential_confirmation_bar.close,
            "entry_bar_body_pct": potential_confirmation_bar.body_percentage,
            "upper_wick_pct_at_entry": potential_confirmation_bar.bar_wick,
            "volume_acceleration": potential_confirmation_bar.volume_average_last_3/potential_confirmation_bar.volume_average_last_10,
            "extension_vs_pullback": 0,
            "move_efficiency": 0,
            "pullback_to_trend_ratio": 0,
            "trend_cleanliness": 0,
            "pullback_structure_score": 0,
            "volume_confirmation_ratio": 0,
            "volume_trend_strength": 0,
            "volume_during_pullback": 0,
            "relative_position_in_range": 0,
            "distance_from_vwap_normalized": 0,
            "hod_proximity_score": 0,
            "momentum_alignment_score": 0,
            "momentum_strength": 0,
            "entry_conviction_score": 0,
            "entry_efficiency": 0,
            "failed_breakout_risk": 0,
            "late_move_indicator": 0,
            "early_vs_late_flag": 0,
            "volatility_regime": 0,
            "average_range_last_5": 0,
        }

        for bar_object in one_minute_bars:
            bar_movement = bar_object.high - bar_object.low
            if bar_object.close > bar_object.open_value:
                symbol_statistics["positive_movement_since_market_open"] += bar_movement
            if bar_object.close <= bar_object.open_value:
                symbol_statistics["negative_movement_since_market_open"] += bar_movement
            if bar_object.close > bar_object.vwap:
                symbol_statistics["movement_above_vwap_since_market_open"] += bar_movement
            if bar_object.close <= bar_object.vwap:
                symbol_statistics["movement_under_vwap_since_market_open"] += bar_movement
            if bar_object.volume > bar_object.volume_average:
                symbol_statistics["movement_above_volume_average_counter_since_market_open"] += 1
            if bar_object.volume <= bar_object.volume_average:
                symbol_statistics["movement_under_volume_average_counter_since_market_open"] += 1
            if bar_object.histogram > 0.0 and bar_object.histogram > symbol_statistics["highest_histogram_since_market_open"]:
                symbol_statistics["highest_histogram_since_market_open"] = bar_object.histogram
            if bar_object.histogram < 0.0 and bar_object.histogram < symbol_statistics["lowest_histogram_since_market_open"]:
                symbol_statistics["lowest_histogram_since_market_open"] = bar_object.histogram

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

            number_of_negative_bars = len(
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
            volume_during_pullback = sum(
                bar_object.volume
                for bar_object in pullback_bars
            )

            symbol_statistics["pullback_sharpness"] = pullback_size/pullback_duration
            symbol_statistics["pullback_duration"] = pullback_duration
            symbol_statistics["pullback_depth"] = highest_high_one_minute_bar.high - lowest_low_bar.low if lowest_low_bar is not None else 0.0
            symbol_statistics["number_of_negative_bars"] = number_of_negative_bars
            symbol_statistics["extension_vs_pullback"] = symbol_statistics["price_minus_vwap_at_entry"]/symbol_statistics["pullback_depth"] if symbol_statistics["pullback_depth"] > 0 else 0.0
            symbol_statistics["move_efficiency"] = symbol_statistics["positive_movement_since_market_open"]/symbol_statistics["minutes_since_market_open"] if symbol_statistics["minutes_since_market_open"] > 0 else 0
            symbol_statistics["pullback_to_trend_ratio"] = symbol_statistics["pullback_depth"]/symbol_statistics["positive_movement_since_market_open"] if symbol_statistics["positive_movement_since_market_open"] > 0 else 0
            symbol_statistics["trend_cleanliness"] = number_of_green_bars_last_5/(number_of_green_bars_last_5 + number_of_red_bars_last_5) if (number_of_green_bars_last_5 + number_of_red_bars_last_5) > 0 else 0
            symbol_statistics["pullback_structure_score"] = symbol_statistics["pullback_duration"]/symbol_statistics["number_of_negative_bars"] if symbol_statistics["number_of_negative_bars"] > 0 else 0.0
            symbol_statistics["volume_confirmation_ratio"] = symbol_statistics["entry_volume_spike_3"]/stock.volume_sum_since_4_am_today if stock.volume_sum_since_4_am_today > 0 else 0.0
            symbol_statistics["volume_trend_strength"] = symbol_statistics["volume_acceleration"]*symbol_statistics["volume_trend"]
            symbol_statistics["volume_during_pullback"] = volume_during_pullback
            symbol_statistics["relative_position_in_range"] = (potential_confirmation_bar.close - lowest_low_one_minute_bar.low)/(highest_high_one_minute_bar.high - lowest_low_one_minute_bar.low) if (highest_high_one_minute_bar.high - lowest_low_one_minute_bar.low) > 0 else 0.0
            symbol_statistics["distance_from_vwap_normalized"] = symbol_statistics["price_minus_vwap_at_entry"]/symbol_statistics["entry_bar_range_pct"] if symbol_statistics["entry_bar_range_pct"] > 0 else 0.0
            symbol_statistics["hod_proximity_score"] = symbol_statistics["distance_from_high_of_day"]/symbol_statistics["pullback_depth"] if symbol_statistics["pullback_depth"] > 0 else 0.0
            symbol_statistics["momentum_alignment_score"] = numpy.sign(symbol_statistics["histogram_at_entry"]) * numpy.sign(symbol_statistics["vwap_slope_5"]) * numpy.sign(symbol_statistics["ema9_minus_ema20_at_entry"])
            symbol_statistics["momentum_strength"] = abs(symbol_statistics["histogram_at_entry"]) * abs(symbol_statistics["vwap_slope_5"])
            symbol_statistics["entry_conviction_score"] = symbol_statistics["entry_bar_body_pct"] * (1 - symbol_statistics["upper_wick_pct_at_entry"])
            symbol_statistics["entry_efficiency"] = symbol_statistics["entry_bar_body_pct"] / symbol_statistics["entry_bar_range_pct"] if symbol_statistics["entry_bar_range_pct"] > 0 else 0.0
            symbol_statistics["failed_breakout_risk"] = symbol_statistics["number_of_negative_bars"] * symbol_statistics["distance_from_high_of_day"]
            symbol_statistics["late_move_indicator"] = symbol_statistics["minutes_since_market_open"] * symbol_statistics["distance_from_premarket_high"]
            symbol_statistics["early_vs_late_flag"] = 0 if symbol_statistics["minutes_since_market_open"] < 10 else 1
            symbol_statistics["average_range_last_5"] = mean(
                bar_object.high - bar_object.low
                for bar_object in one_minute_timeframe_stock.bars[1:6]
            )
            symbol_statistics["volatility_regime"] = symbol_statistics["entry_bar_range_pct"]/symbol_statistics["average_range_last_5"] if symbol_statistics["average_range_last_5"] > 0 else 0.0


        return symbol_statistics

    def compute_probability(
        self,
        symbol_statistics,
        older_positive_scores,
    ) -> float:
        score = self.compute_score(
            symbol_statistics=symbol_statistics,
        )
        idx = bisect_right(older_positive_scores, score)
        return round(100.0 * (idx + 1) / (len(older_positive_scores) + 1), 2)

    def clamp(
        self,
        value: float,
        low: float,
        high: float,
    ) -> float:
        return max(low, min(high, value))

    def compute_score(
        self,
        symbol_statistics: dict[str, float],
    ) -> float:
        score = 50.0

        vwap_slope_5 = float(symbol_statistics["vwap_slope_5"])
        volume_acceleration = float(symbol_statistics["volume_acceleration"])
        lowest_hist = float(symbol_statistics["lowest_histogram_since_market_open"])
        highest_hist = float(symbol_statistics["highest_histogram_since_market_open"])
        price_minus_vwap = float(symbol_statistics["price_minus_vwap_at_entry"])
        distance_from_vwap_normalized = float(symbol_statistics["distance_from_vwap_normalized"])
        pullback_depth = float(symbol_statistics["pullback_depth"])
        pullback_sharpness = float(symbol_statistics["pullback_sharpness"])
        minutes_since_open = float(symbol_statistics["minutes_since_market_open"])
        ema9_minus_ema20 = float(symbol_statistics["ema9_minus_ema20_at_entry"])
        distance_from_hod = float(symbol_statistics["distance_from_high_of_day"])
        momentum_strength = float(symbol_statistics["momentum_strength"])
        move_efficiency = float(symbol_statistics["move_efficiency"])
        volume_confirmation_ratio = float(symbol_statistics["volume_confirmation_ratio"])
        extension_vs_pullback = float(symbol_statistics["extension_vs_pullback"])

        # lower-priority modifiers
        upper_wick = float(symbol_statistics["upper_wick_pct_at_entry"])
        volume_trend = float(symbol_statistics["volume_trend"])
        entry_volume_spike_3 = float(symbol_statistics["entry_volume_spike_3"])
        entry_conviction_score = float(symbol_statistics["entry_conviction_score"])

        # -----------------------------------------
        # Minimal hard rejects only
        # -----------------------------------------
        if vwap_slope_5 <= 0:
            return 5.0

        score -= 25.0 * self.clamp((pullback_sharpness - 0.20), 0.0, 1.0)

        # -----------------------------------------
        # Trend quality
        # -----------------------------------------
        score += 250.0 * self.clamp(vwap_slope_5, 0.0, 0.05)

        # -----------------------------------------
        # Earlier session damage / overheating
        # These are penalties now, not hard rejects
        # -----------------------------------------
        score -= 18.0 * self.clamp((-lowest_hist - 0.03), 0.0, 1.0)
        score -= 16.0 * self.clamp((highest_hist - 0.06), 0.0, 1.0)

        # -----------------------------------------
        # Extension penalties
        # -----------------------------------------
        score -= 12.0 * self.clamp((price_minus_vwap - 0.5), 0.0, 1.0)
        score -= 3.5 * self.clamp(distance_from_vwap_normalized - 7.5, 0.0, 10.0)
        score -= 18.0 * self.clamp((ema9_minus_ema20 - 0.12), 0.0, 0.50)

        # -----------------------------------------
        # Pullback quality
        # -----------------------------------------
        score -= 14.0 * self.clamp((pullback_depth - 0.30), 0.0, 0.70)
        score -= 20.0 * self.clamp((pullback_sharpness - 0.14), 0.0, 0.50)

        # slight bonus for healthy pullback zone
        if 0.15 <= pullback_depth <= 0.38:
            score += 5.0

        if 0.2 < pullback_depth < 0.4 and pullback_sharpness < 0.18:
            score += 3.0

        score -= 8.0 * self.clamp((0.015 - highest_hist), 0.0, 0.02)

        if momentum_strength > 8.0:
            score -= 12.0

        score -= 10.0 * self.clamp((0.02 - move_efficiency), 0.0, 0.02)

        score -= 6.0 * self.clamp((0.2 - volume_confirmation_ratio), 0.0, 0.2)

        if momentum_strength > 8.0 and extension_vs_pullback > 1.8:
            score -= 7.0

        if (
            highest_hist < 0.015
            and move_efficiency < 0.02
        ):
            score -= 12.0

        # -----------------------------------------
        # Time-of-day
        # penalty, not hard reject
        # -----------------------------------------
        if minutes_since_open <= 120:
            score += 5.0
        elif minutes_since_open <= 180:
            score += 2.0
        elif minutes_since_open <= 200:
            score -= 5.0
        elif minutes_since_open <= 260:
            score -= 10.0
        else:
            score -= 15.0

        if (
            distance_from_vwap_normalized > 9.0
            and ema9_minus_ema20 > 0.15
        ):
            score -= 12.0

        # -----------------------------------------
        # Distance from HOD
        # -----------------------------------------
        if distance_from_hod < 0.05:
            score -= 6.0
        elif distance_from_hod <= 0.35:
            score += 4.0
        elif distance_from_hod <= 0.60:
            score += 1.0
        else:
            score -= 2.0

        # -----------------------------------------
        # Minor modifiers
        # -----------------------------------------
        score += 2.0 * self.clamp(volume_acceleration - 1.1, -0.5, 1.5)
        score += 1.5 * self.clamp(volume_trend - 1.0, -0.5, 1.0)
        score += 1.0 * self.clamp(entry_volume_spike_3 - 1.0, -0.5, 2.0)

        score -= 3.0 * self.clamp(upper_wick - 0.20, 0.0, 0.50)
        score += 2.0 * self.clamp(entry_conviction_score - 0.55, -0.5, 0.5)

        # -----------------------------------------
        # Interaction effects
        # -----------------------------------------
        if price_minus_vwap > 0.80 and pullback_depth > 0.40:
            score -= 6.0

        if highest_hist > 0.10 and pullback_sharpness > 0.20:
            score -= 6.0

        if minutes_since_open > 180 and distance_from_vwap_normalized > 9.0:
            score -= 5.0

        if (
            lowest_hist > -0.03
            and highest_hist < 0.08
            and pullback_depth < 0.35
            and pullback_sharpness < 0.18
        ):
            score += 6.0

        return max(0.0, min(score, 100.0))

    def confirm(
        self,
        stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        lowest_low_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        volume_sum_since_market_open: float,
    ) -> bool:
        current_bar_12_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=12,
        )

        if (
            potential_confirmation_bar.volume_average < 10000
            and potential_confirmation_bar.bar_time >= current_bar_12_00
        ):
            return False

        if not self._confirm(
            stock=stock,
            original_bar_to_confirm=original_bar_to_confirm,
            potential_confirmation_bar=potential_confirmation_bar,
            milestones=milestones,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            one_minute_bars=one_minute_bars,
            volume_sum_since_market_open=volume_sum_since_market_open,
        ):
            return False

        potential_confirmation_bar.price_movement_statistics = self.symbol_statistics(
            stock=stock,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            original_bar_to_confirm=original_bar_to_confirm,
            potential_confirmation_bar=potential_confirmation_bar,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            lowest_low_one_minute_bar=lowest_low_one_minute_bar,
            one_minute_bars=one_minute_bars,
        )

        if (
            True
            and potential_confirmation_bar.body_percentage < 0.5
            and potential_confirmation_bar.close < potential_confirmation_bar.high
            and potential_confirmation_bar.low < potential_confirmation_bar.open_value
        ):
            return False

        current_bar_09_30 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=9,
            minute=30,
        )
        current_bar_10_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=10,
        )

        today_04_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=4,
        )

        volume_sum_since_4_am_today = sum(
            bar_object.volume
            for bar_object in one_minute_timeframe_stock.bars
            if today_04_00 <= bar_object.bar_time <= potential_confirmation_bar.bar_time
        )
        stock.volume_sum_since_4_am_today = volume_sum_since_4_am_today

        if current_bar_09_30 <= potential_confirmation_bar.bar_time <= current_bar_10_00:
            return volume_sum_since_4_am_today > 5000000
        if potential_confirmation_bar.bar_time > current_bar_10_00:
            return (
                (potential_confirmation_bar.high - highest_high_one_minute_bar.high)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.3
                and highest_high_one_minute_bar.index - 1 > potential_confirmation_bar.index
            ) or (
                volume_sum_since_4_am_today > 2000000
            )

        return False

    def _confirm(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        volume_sum_since_market_open: float,
    ) -> bool:
        raise NotImplementedError()
