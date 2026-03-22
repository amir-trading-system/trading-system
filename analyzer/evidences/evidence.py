import datetime

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
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> dict[str, float]:
        number_of_green_bars_last_5 = 0
        number_of_red_bars_last_5 = 0
        for bar_object in one_minute_bars[1:6]:
            if bar_object.close > bar_object.open_value:
                number_of_green_bars_last_5 += 1
            else:
                number_of_red_bars_last_5 += 1

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
            "broke_high_of_day_at_entry": potential_confirmation_bar.close >= highest_high_one_minute_bar.high,
            "vwap_slope_3": (potential_confirmation_bar.vwap - one_minute_bars[3].vwap) / one_minute_bars[3].vwap,
            "vwap_slope_5": (potential_confirmation_bar.vwap - one_minute_bars[5].vwap) / one_minute_bars[5].vwap,
            "ema9_minus_vwap_at_entry": potential_confirmation_bar.ema_9 - potential_confirmation_bar.vwap,
            "ema9_minus_ema20_at_entry": potential_confirmation_bar.ema_9 - potential_confirmation_bar.ema_20,
            "number_of_green_bars_last_5": number_of_green_bars_last_5,
            "number_of_red_bars_last_5": number_of_red_bars_last_5,
            "distance_from_premarket_high": ((potential_confirmation_bar.bar_time.hour - stock.pre_market_one_minute_highest_high_bar.bar_time.hour) * 60) + potential_confirmation_bar.bar_time.minute - stock.pre_market_one_minute_highest_high_bar.bar_time.minute if stock.pre_market_one_minute_highest_high_bar is not None else 0.0,
            "entry_bar_range_pct": (potential_confirmation_bar.high - potential_confirmation_bar.low)/ potential_confirmation_bar.close,
            "entry_bar_body_pct": potential_confirmation_bar.body_percentage,
            "upper_wick_pct_at_entry": potential_confirmation_bar.bar_wick,
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
            lowest_low_since_highest_high = min(
                bar_object.low
                for bar_object in bars_since_highest_high
            )
            lowest_low_bar = None

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
            symbol_statistics["pullback_sharpness"] = pullback_size/pullback_duration
            symbol_statistics["pullback_duration"] = pullback_duration
            symbol_statistics["pullback_depth"] = highest_high_one_minute_bar.high - lowest_low_bar.low
            symbol_statistics["number_of_negative_bars"] = number_of_negative_bars

        return symbol_statistics

    def compute_probability(
        self,
        symbol_statistics,
        older_positive_scores,
    ) -> float:
        score = self.compute_score(
            symbol_statistics=symbol_statistics,
        )
        better_than = sum(
            score >= s for s in older_positive_scores
        )
        probability = better_than/len(older_positive_scores)

        return probability * 100

    def compute_score(
        self,
        symbol_statistics: dict[str, float],
    ) -> float:
        ## converting each to float for retro check
        return (
            + 0.4 * float(symbol_statistics["negative_movement_since_market_open"])
            + 0.6 * float(symbol_statistics["movement_under_vwap_since_market_open"])
            + 0.5 * float(symbol_statistics["movement_under_volume_average_counter_since_market_open"])

            - 0.5 * float(symbol_statistics["positive_movement_since_market_open"])
            - 0.4 * float(symbol_statistics["movement_above_vwap_since_market_open"])
            - 0.3 * float(symbol_statistics["movement_above_volume_average_counter_since_market_open"])

            - 2.0 * float(symbol_statistics["highest_histogram_since_market_open"])
            + 1.5 * float(symbol_statistics["lowest_histogram_since_market_open"])

            + 0.8 * float(symbol_statistics["pullback_depth"])
            - 1.2 * float(symbol_statistics["pullback_sharpness"])
            + 0.3 * float(symbol_statistics["pullback_duration"])

            + 1.0 * float(symbol_statistics["entry_volume_spike_3"])
            + 0.8 * float(symbol_statistics["entry_volume_spike_5"])
        )

    def confirm(
        self,
        stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
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
            original_bar_to_confirm=original_bar_to_confirm,
            potential_confirmation_bar=potential_confirmation_bar,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
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
