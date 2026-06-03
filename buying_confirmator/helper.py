#pylint: skip-file

import datetime

import common


class Helper:
    def __init__(
        self,
    ):
        pass

    def _safe_float(
        self,
        value,
        default: float | None = None,
    ) -> float | None:
        try:
            if value is None:
                return default

            value = float(value)

            if value != value:
                return default

            return value

        except Exception:
            return default

    def _get_today_bars_until_current(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[common.objects.BarData]:
        """
        Live-safe.

        one_minute_timeframe_stock.bars may have the current bar first,
        so always sort by bar_time and only keep bars up to current bar.
        """

        return sorted(
            [
                bar_object
                for bar_object in one_minute_timeframe_stock.bars
                if (
                    bar_object.bar_time.date() == potential_confirmation_bar.bar_time.date()
                    and bar_object.bar_time <= potential_confirmation_bar.bar_time
                )
            ],
            key=lambda bar_object: bar_object.bar_time,
        )

    def _get_bars_before_current(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[common.objects.BarData]:
        return sorted(
            [
                bar_object
                for bar_object in one_minute_timeframe_stock.bars
                if (
                    bar_object.bar_time.date() == potential_confirmation_bar.bar_time.date()
                    and bar_object.bar_time < potential_confirmation_bar.bar_time
                )
            ],
            key=lambda bar_object: bar_object.bar_time,
        )


    def _get_candle_quality_stats(
        self,
        bar_object: common.objects.BarData,
    ) -> tuple[float, float, float]:
        candle_range = bar_object.high - bar_object.low

        if candle_range <= 0:
            return 0.0, 0.0, 0.0

        body_pct = abs(bar_object.close - bar_object.open_value) / candle_range
        upper_wick_pct = (
            bar_object.high - max(bar_object.open_value, bar_object.close)
        ) / candle_range
        close_position_in_range = (bar_object.close - bar_object.low) / candle_range

        return body_pct, max(0.0, upper_wick_pct), close_position_in_range

    def _is_swing_high(
        self,
        bars: list[common.objects.BarData],
        index: int,
        width: int = 2,
    ) -> bool:
        if index < width or index + width >= len(bars):
            return False

        current_high = bars[index].high
        return all(
            current_high >= bars[other_index].high
            for other_index in range(index - width, index + width + 1)
            if other_index != index
        )

    def _is_demand_impulse_bar(
        self,
        bar_object: common.objects.BarData,
    ) -> bool:
        body_pct, _upper_wick_pct, close_position_in_range = self._get_candle_quality_stats(
            bar_object=bar_object,
        )

        if bar_object.volume_average <= 0:
            return False

        if bar_object.open_value <= 0:
            return False

        volume_vs_average_ratio = bar_object.volume / bar_object.volume_average
        bar_gain_pct = (bar_object.close - bar_object.open_value) / bar_object.open_value

        return (
            True
            and bar_object.close > bar_object.open_value
            and volume_vs_average_ratio >= 2.0
            and body_pct >= 0.55
            and close_position_in_range >= 0.75
            and bar_gain_pct >= 0.025
        )

    def _absorption_stats_for_demand_zone(
        self,
        bars: list[common.objects.BarData],
        zone_low: float,
        zone_high: float,
    ) -> tuple[int, int]:
        """
        Return (touch_count, failed_breakdown_count) for a demand zone.

        A failed breakdown means price temporarily trades below the demand
        zone, but closes back above the zone low. That was the strongest
        supply/demand property in the research export.
        """

        if zone_low <= 0 or zone_high <= zone_low:
            return 0, 0

        touch_count = 0
        failed_breakdown_count = 0

        for bar_object in bars:
            touches_zone = (
                bar_object.low <= zone_high * 1.025
                and bar_object.low >= zone_low * 0.98
            )

            if touches_zone:
                touch_count += 1

            if (
                bar_object.low < zone_low * 0.98
                and bar_object.close >= zone_low
            ):
                failed_breakdown_count += 1

        return touch_count, failed_breakdown_count

    def _matches_resistance_support_volume_break_retest_30(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        prior_max_gain_since_open_pct: float | None,
        current_close_to_vwap_pct: float | None,
        entry_volume_vs_average_ratio: float,
    ) -> bool:
        """
        Strict resistance -> support sequence from the research export.

        Required structure:
        previous swing-high resistance -> volume breakout above level ->
        retest of old resistance as support -> clean reclaim entry.
        """

        if prior_max_gain_since_open_pct is None or prior_max_gain_since_open_pct > 0.20:
            return False

        if current_close_to_vwap_pct is None or current_close_to_vwap_pct > 0.10:
            return False

        if entry_volume_vs_average_ratio < 3.0:
            return False

        if len(bars_before_current) < 25:
            return False

        lookback_start = max(0, len(bars_before_current) - 90)
        search_bars = bars_before_current + [potential_confirmation_bar]
        entry_index = len(search_bars) - 1

        swing_high_indices = [
            index
            for index in range(lookback_start, len(bars_before_current) - 3)
            if self._is_swing_high(search_bars, index=index, width=2)
        ]

        for level_index in swing_high_indices[-12:]:
            level_bar = search_bars[level_index]
            resistance_price = level_bar.high

            if resistance_price <= 0:
                continue

            breakout_index = None
            breakout_bar = None

            for index in range(level_index + 1, entry_index):
                candidate_bar = search_bars[index]

                if candidate_bar.volume_average <= 0:
                    continue

                breakout_close_above_level_pct = (
                    candidate_bar.close - resistance_price
                ) / resistance_price
                breakout_volume_vs_average = candidate_bar.volume / candidate_bar.volume_average

                if (
                    breakout_close_above_level_pct >= 0.05
                    and breakout_volume_vs_average >= 1.20
                ):
                    breakout_index = index
                    breakout_bar = candidate_bar
                    break

            if breakout_index is None or breakout_bar is None:
                continue

            retest_index = None
            retest_bar = None

            for index in range(breakout_index + 1, entry_index):
                candidate_bar = search_bars[index]

                if (
                    candidate_bar.low <= resistance_price * 1.012
                    and candidate_bar.low >= resistance_price * 0.975
                ):
                    retest_index = index
                    retest_bar = candidate_bar

            if retest_index is None or retest_bar is None:
                continue

            if entry_index - retest_index > 5:
                continue

            if potential_confirmation_bar.close < max(
                retest_bar.close,
                retest_bar.high * 0.995,
            ):
                continue

            return True

        return False

    def _matches_supply_demand_failed_breakdown_absorption_30(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        prior_max_gain_since_open_pct: float | None,
        current_close_to_vwap_pct: float | None,
    ) -> bool:
        """
        Strict supply/demand absorption sequence from the research export.

        Required structure:
        demand impulse -> many absorption touches into demand zone -> at least
        one failed breakdown -> reclaim entry close still near VWAP.
        """

        if prior_max_gain_since_open_pct is None or prior_max_gain_since_open_pct > 0.20:
            return False

        if current_close_to_vwap_pct is None or current_close_to_vwap_pct > 0.10:
            return False

        if len(bars_before_current) < 25:
            return False

        entry_bar = potential_confirmation_bar
        search_start = max(0, len(bars_before_current) - 75)

        demand_indices = [
            index
            for index in range(search_start, len(bars_before_current) - 2)
            if self._is_demand_impulse_bar(bar_object=bars_before_current[index])
        ]

        for demand_index in demand_indices[-8:]:
            demand_bar = bars_before_current[demand_index]
            zone_low = demand_bar.low
            zone_high = min(demand_bar.open_value, demand_bar.close)

            if zone_low <= 0 or zone_high <= zone_low:
                continue

            if entry_bar.close <= zone_high:
                continue

            absorption_bars = bars_before_current[demand_index + 1:]

            touch_count, failed_breakdown_count = self._absorption_stats_for_demand_zone(
                bars=absorption_bars,
                zone_low=zone_low,
                zone_high=zone_high,
            )

            if touch_count < 8:
                continue

            if failed_breakdown_count < 1:
                continue

            absorption_max_close = max(
                (bar_object.close for bar_object in absorption_bars),
                default=None,
            )

            if absorption_max_close is not None and entry_bar.close <= absorption_max_close * 0.995:
                continue

            return True

        return False


    def _matches_orb_quality_breakout_30(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        Strict opening-range breakout family from the theory research pass.

        This is the only 30% family allowed to fire during the first few
        regular-session minutes. It requires the first 1-3 minute range to be
        established, then a real accepted break above that range with strong
        volume and controlled risk to the opening-range low.
        """

        current_time = potential_confirmation_bar.bar_time.time()

        if not (
            datetime.time(9, 33)
            <= current_time
            <= datetime.time(9, 45)
        ):
            return False

        opening_range_bars = [
            bar_object
            for bar_object in bars_before_current
            if (
                bar_object.bar_time.date() == potential_confirmation_bar.bar_time.date()
                and datetime.time(9, 30) <= bar_object.bar_time.time() <= datetime.time(9, 32)
            )
        ]

        if len(opening_range_bars) < 2:
            return False

        opening_range_high = max(
            bar_object.high
            for bar_object in opening_range_bars
        )
        opening_range_low = min(
            bar_object.low
            for bar_object in opening_range_bars
        )

        if opening_range_high <= 0 or opening_range_low <= 0:
            return False

        candle_range = potential_confirmation_bar.high - potential_confirmation_bar.low
        if candle_range <= 0:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False

        close_position_in_range = (
            potential_confirmation_bar.close - potential_confirmation_bar.low
        ) / candle_range

        if close_position_in_range < 0.90:
            return False

        candle_body_pct = abs(
            potential_confirmation_bar.close - potential_confirmation_bar.open_value
        ) / candle_range

        if candle_body_pct < 0.55:
            return False

        upper_wick_pct = (
            potential_confirmation_bar.high
            - max(
                potential_confirmation_bar.open_value,
                potential_confirmation_bar.close,
            )
        ) / candle_range

        if upper_wick_pct > 0.10:
            return False

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        if volume_vs_average_ratio < 3.0:
            return False

        orb_break_pct = (
            potential_confirmation_bar.close - opening_range_high
        ) / opening_range_high

        if orb_break_pct < 0.02:
            return False

        orb_risk_pct = (
            potential_confirmation_bar.close - opening_range_low
        ) / potential_confirmation_bar.close

        if orb_risk_pct > 0.12:
            return False

        if potential_confirmation_bar.vwap <= 0:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.vwap:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_9:
            return False

        return True

    def _is_30pct_trend_shift_candidate_base(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> str | None:
        """
        30% trend-shift selector from the positive 30% trend-start study.

        This is intentionally broader than the 50% sniper patterns, but it
        should still represent a real intraday trend change. It accepts one of
        repeatable structures:
        1. strict opening-range breakout quality
        2. aligned higher-low continuation
        3. volume dry-up reclaim
        4. pre-20-bar rebuild continuation
        5. missed early rebuild expansion
        6. recent-high break with volume
        7. strict resistance/support and supply/demand sequences
        8. late volume-shock flat-base continuation
        """

        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        # ORB is the only early-session family that can be evaluated before
        # a full 20 bars exists. It must be checked before the generic
        # minimum-history guard.
        if self._matches_orb_quality_breakout_30(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            return "30pct_orb_quality_breakout"

        if len(bars_before_current) < 20:
            return False

        previous_bar = bars_before_current[-1]
        last_5_bars = bars_before_current[-5:]
        last_10_bars = bars_before_current[-10:]
        last_20_bars = bars_before_current[-20:]
        last_60_bars = bars_before_current[-60:]

        current_time = potential_confirmation_bar.bar_time.time()

        # For the 30% trend-shift experiment, do not allow generic
        # trend-shift alerts during the first market-open minutes.
        # Legit open entries should come from a dedicated open/premarket
        # support-reclaim detector, not from the broad 30% selector.
        if (
            datetime.time(9, 30)
            <= current_time
            < datetime.time(9, 35)
        ):
            return False

        candle_range = potential_confirmation_bar.high - potential_confirmation_bar.low
        if candle_range <= 0:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False

        close_position_in_range = (
            potential_confirmation_bar.close - potential_confirmation_bar.low
        ) / candle_range

        upper_wick_pct = (
            potential_confirmation_bar.high
            - max(
                potential_confirmation_bar.open_value,
                potential_confirmation_bar.close,
            )
        ) / candle_range

        candle_body_pct = abs(
            potential_confirmation_bar.close - potential_confirmation_bar.open_value
        ) / candle_range

        # Base buyer-control candle for all 30% trend-shift families.
        if close_position_in_range < 0.80:
            return False

        if upper_wick_pct > 0.20:
            return False

        if candle_body_pct < 0.45:
            return False

        if previous_bar.volume <= 0:
            return False

        volume_vs_previous_bar_ratio = (
            potential_confirmation_bar.volume / previous_bar.volume
        )

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        # Current trend alignment for all families.
        if potential_confirmation_bar.close <= potential_confirmation_bar.vwap:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_9:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_20:
            return False

        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.ema_20:
            return False

        current_close_to_vwap_pct = (
            potential_confirmation_bar.close - potential_confirmation_bar.vwap
        ) / potential_confirmation_bar.vwap if potential_confirmation_bar.vwap > 0 else None

        # Common previous-structure metrics.
        pre_10_close_above_vwap_count = sum(
            1
            for bar_object in last_10_bars
            if bar_object.close > bar_object.vwap
        )

        pre_10_close_above_ema9_count = sum(
            1
            for bar_object in last_10_bars
            if bar_object.close > bar_object.ema_9
        )

        pre_10_higher_or_flat_low_count = 0
        for index in range(1, len(last_10_bars)):
            previous_low = last_10_bars[index - 1].low
            current_low = last_10_bars[index].low
            if previous_low > 0 and current_low >= previous_low * 0.985:
                pre_10_higher_or_flat_low_count += 1

        volume_ratios_last_5 = [
            bar_object.volume / bar_object.volume_average
            for bar_object in last_5_bars
            if bar_object.volume_average > 0
        ]

        pre_5_bar_avg_volume_ratio = None
        if volume_ratios_last_5:
            pre_5_bar_avg_volume_ratio = sum(volume_ratios_last_5) / len(volume_ratios_last_5)

        volume_ratios_last_10 = [
            bar_object.volume / bar_object.volume_average
            for bar_object in last_10_bars
            if bar_object.volume_average > 0
        ]

        pre_10_bar_avg_volume_ratio = None
        if volume_ratios_last_10:
            pre_10_bar_avg_volume_ratio = sum(volume_ratios_last_10) / len(volume_ratios_last_10)

        volume_ratios_last_20 = [
            bar_object.volume / bar_object.volume_average
            for bar_object in last_20_bars
            if bar_object.volume_average > 0
        ]

        pre_20_bar_avg_volume_ratio = None
        if volume_ratios_last_20:
            pre_20_bar_avg_volume_ratio = sum(volume_ratios_last_20) / len(volume_ratios_last_20)

        pre_10_above_volume_average_count = sum(
            1
            for bar_object in last_10_bars
            if (
                bar_object.volume_average > 0
                and bar_object.volume / bar_object.volume_average >= 1.0
            )
        )

        pre_10_bar_gain_pct = None
        if last_10_bars[0].close > 0:
            pre_10_bar_gain_pct = (
                last_10_bars[-1].close - last_10_bars[0].close
            ) / last_10_bars[0].close

        current_ema_9_to_vwap_pct = None
        if potential_confirmation_bar.vwap > 0:
            current_ema_9_to_vwap_pct = (
                potential_confirmation_bar.ema_9 - potential_confirmation_bar.vwap
            ) / potential_confirmation_bar.vwap

        pre_20_bar_gain_pct = None
        if last_20_bars[0].close > 0:
            pre_20_bar_gain_pct = (
                last_20_bars[-1].close - last_20_bars[0].close
            ) / last_20_bars[0].close

        recent_20_high_bar = max(
            last_20_bars,
            key=lambda bar_object: bar_object.high,
        )
        recent_20_low_bar = min(
            last_20_bars,
            key=lambda bar_object: bar_object.low,
        )

        recent_20_high = recent_20_high_bar.high
        recent_20_low = recent_20_low_bar.low

        risk_to_recent_support_low_pct = None
        if potential_confirmation_bar.close > 0:
            risk_to_recent_support_low_pct = (
                potential_confirmation_bar.close - recent_20_low
            ) / potential_confirmation_bar.close

        # Very early regular-session bars with a deep support reference are
        # dangerous for a 30% target because the stop/last-low is too far
        # below the entry. This is meant to block early CODX-style alerts.
        if (
            current_time < datetime.time(9, 40)
            and risk_to_recent_support_low_pct is not None
            and risk_to_recent_support_low_pct > 0.12
        ):
            return False

        # Prior move since market open. A stock that already ran too far
        # before the entry often has poorer remaining 30% risk/reward unless
        # it is a very specific late flat-base volume shock.
        regular_bars_before_current = [
            bar_object
            for bar_object in bars_before_current
            if datetime.time(9, 30) <= bar_object.bar_time.time() <= datetime.time(16, 0)
        ]

        prior_max_gain_since_open_pct = None
        if regular_bars_before_current and regular_bars_before_current[0].open_value > 0:
            market_open_price = regular_bars_before_current[0].open_value
            prior_high_since_open = max(
                bar_object.high
                for bar_object in regular_bars_before_current
            )
            prior_max_gain_since_open_pct = (
                prior_high_since_open - market_open_price
            ) / market_open_price

        close_above_recent_20_high_pct = None
        pullback_from_recent_20_high_pct = None
        minutes_since_recent_20_high = None

        if recent_20_high > 0:
            close_above_recent_20_high_pct = (
                potential_confirmation_bar.close - recent_20_high
            ) / recent_20_high
            pullback_from_recent_20_high_pct = (
                recent_20_high - potential_confirmation_bar.low
            ) / recent_20_high
            minutes_since_recent_20_high = (
                potential_confirmation_bar.bar_time - recent_20_high_bar.bar_time
            ).total_seconds() / 60.0

        # ---------------------------------------------
        # 1. Aligned higher-low continuation, 30% target.
        # ---------------------------------------------
        aligned_higher_low_30 = (
            True
            and current_time < datetime.time(11, 0)
            and volume_vs_previous_bar_ratio >= 1.40
            and volume_vs_average_ratio >= 1.20
            and pre_10_higher_or_flat_low_count >= 7
            and pre_10_close_above_vwap_count >= 8
            and pre_10_close_above_ema9_count >= 5
            # Aligned trend continuation should not be an isolated one-bar
            # spike after dead volume / no prior buyer participation.
            and pre_10_bar_gain_pct is not None
            and pre_10_bar_gain_pct >= 0.02
            and (
                pre_10_bar_avg_volume_ratio is None
                or pre_10_bar_avg_volume_ratio >= 0.85
                or pre_10_above_volume_average_count >= 3
            )
            and current_close_to_vwap_pct is not None
            # Family-specific v5 filter: aligned entries should still be
            # close enough to VWAP/base. Stretched aligned bars were the
            # biggest source of 10-30% continuation false positives.
            and current_close_to_vwap_pct <= 0.10
            and upper_wick_pct <= 0.15
        )

        # ---------------------------------------------
        # 2. Volume dry-up reclaim.
        # ---------------------------------------------
        volume_dryup_reclaim_30 = (
            True
            and current_time < datetime.time(11, 30)
            and pre_5_bar_avg_volume_ratio is not None
            and pre_5_bar_avg_volume_ratio <= 0.85
            and volume_vs_previous_bar_ratio >= 1.60
            and volume_vs_average_ratio >= 1.20
            and pre_10_higher_or_flat_low_count >= 7
            and pre_10_close_above_vwap_count >= 5
            # Dry-up reclaim still needs some prior upward progress; otherwise
            # it can be a dead-stock pop with no real buyer context.
            and pre_10_bar_gain_pct is not None
            and pre_10_bar_gain_pct >= 0.04
            # Avoid stretched dry-up attempts unless the entry volume is strong
            # enough to justify the extension.
            and current_close_to_vwap_pct is not None
            # Family-specific v5 filter: dry-up reclaim can be a bit more
            # extended than aligned, but not a late stretched pop.
            and current_close_to_vwap_pct <= 0.18
            and (
                (
                    pullback_from_recent_20_high_pct is not None
                    and pullback_from_recent_20_high_pct >= 0.03
                )
                or (
                    minutes_since_recent_20_high is not None
                    and minutes_since_recent_20_high >= 5
                )
            )
        )

        # ---------------------------------------------
        # 3. Pre-20-bar rebuild continuation.
        # ---------------------------------------------
        pre20_rebuild_continuation_30 = (
            True
            and current_time < datetime.time(11, 30)
            and pre_20_bar_gain_pct is not None
            and pre_20_bar_gain_pct >= 0.08
            and pre_10_higher_or_flat_low_count >= 7
            # Rebuild continuation must already have VWAP control and should
            # not trigger while EMA9 is still below VWAP.
            and pre_10_close_above_vwap_count >= 7
            and current_ema_9_to_vwap_pct is not None
            and current_ema_9_to_vwap_pct >= 0.0
            # Family-specific v5 filter: rebuild entries need stronger
            # current participation, not only structure.
            and volume_vs_average_ratio >= 2.50
            and volume_vs_previous_bar_ratio >= 1.0
            and current_close_to_vwap_pct is not None
            and (
                current_close_to_vwap_pct <= 0.10
                or (
                    volume_vs_average_ratio >= 3.00
                    and volume_vs_previous_bar_ratio >= 1.60
                    and current_close_to_vwap_pct <= 0.16
                )
            )
        )

        # ---------------------------------------------
        # 4. Missed early rebuild expansion.
        # ---------------------------------------------
        # This family was mined from the broader 10%+ dataset to recover
        # high-quality 30% gainers that the stricter rebuild branch missed.
        # It requires an already-controlled VWAP rebuild, very clean close,
        # tight extension, and enough current volume, but it does not demand
        # the same strong volume threshold as the main rebuild family.
        missed_early_rebuild_expansion_30 = (
            True
            and current_time < datetime.time(11, 0)
            and pre_20_bar_gain_pct is not None
            and pre_20_bar_gain_pct >= 0.05
            and pre_10_higher_or_flat_low_count >= 7
            and pre_10_close_above_vwap_count >= 9
            and pre_10_close_above_ema9_count >= 5
            and current_ema_9_to_vwap_pct is not None
            and current_ema_9_to_vwap_pct >= 0.0
            and current_close_to_vwap_pct is not None
            and current_close_to_vwap_pct <= 0.12
            and close_position_in_range >= 0.95
            and upper_wick_pct <= 0.03
            and volume_vs_average_ratio >= 1.50
            and volume_vs_previous_bar_ratio >= 1.0
        )

        # ---------------------------------------------
        # 5. Recent high break with volume.
        # ---------------------------------------------
        recent_high_break_30 = (
            True
            and current_time < datetime.time(11, 30)
            and close_above_recent_20_high_pct is not None
            and close_above_recent_20_high_pct >= 0.04
            and pre_20_bar_gain_pct is not None
            and pre_20_bar_gain_pct >= 0.08
            # Family-specific v5 filter: recent-high break needs proof of
            # prior volume participation, not a single isolated breakout bar.
            and pre_20_bar_avg_volume_ratio is not None
            and pre_20_bar_avg_volume_ratio >= 0.85
            and current_close_to_vwap_pct is not None
            and current_close_to_vwap_pct <= 0.20
            and volume_vs_average_ratio >= 1.80
            and volume_vs_previous_bar_ratio >= 1.40
            and upper_wick_pct <= 0.15
        )

        # ---------------------------------------------
        # 6. Late volume-shock flat-base breakout.
        # ---------------------------------------------
        # This replaces the older broad midday rule. The broader midday rule
        # was too noisy. This late family requires a flat/resting base near
        # the recent high, then a true volume shock with a clean close.
        pre_5_bar_gain_pct = None
        if last_5_bars and last_5_bars[0].close > 0:
            pre_5_bar_gain_pct = (
                last_5_bars[-1].close - last_5_bars[0].close
            ) / last_5_bars[0].close

        late_volume_shock_flat_base_30 = (
            True
            and datetime.time(11, 0) <= current_time < datetime.time(12, 30)
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.close > potential_confirmation_bar.vwap
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
            and close_position_in_range >= 0.90
            and upper_wick_pct <= 0.10
            and candle_body_pct >= 0.65
            # The previous 5 bars should be flat/resting, not already
            # extending. This is the base before the volume shock.
            and pre_5_bar_gain_pct is not None
            and pre_5_bar_gain_pct <= 0.00
            # Current bar should be near/through the recent 20-bar high.
            and pullback_from_recent_20_high_pct is not None
            and pullback_from_recent_20_high_pct <= 0.02
            # Real late-session volume shock.
            and volume_vs_previous_bar_ratio >= 7.00
            # Avoid late insane extension.
            and current_close_to_vwap_pct is not None
            and current_close_to_vwap_pct <= 0.18
        )

        resistance_support_volume_break_retest_30 = self._matches_resistance_support_volume_break_retest_30(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
            prior_max_gain_since_open_pct=prior_max_gain_since_open_pct,
            current_close_to_vwap_pct=current_close_to_vwap_pct,
            entry_volume_vs_average_ratio=volume_vs_average_ratio,
        )

        supply_demand_failed_breakdown_absorption_30 = self._matches_supply_demand_failed_breakdown_absorption_30(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
            prior_max_gain_since_open_pct=prior_max_gain_since_open_pct,
            current_close_to_vwap_pct=current_close_to_vwap_pct,
        )

        matched_family = None

        if aligned_higher_low_30:
            matched_family = "30pct_aligned"
        elif volume_dryup_reclaim_30:
            matched_family = "30pct_dryup"
        elif pre20_rebuild_continuation_30:
            matched_family = "30pct_rebuild"
        elif missed_early_rebuild_expansion_30:
            matched_family = "30pct_missed_early_rebuild_expansion"
        elif recent_high_break_30:
            matched_family = "30pct_highbreak"
        elif resistance_support_volume_break_retest_30:
            matched_family = "30pct_resistance_support_volume_break_retest"
        elif supply_demand_failed_breakdown_absorption_30:
            matched_family = "30pct_supply_demand_failed_breakdown_absorption"
        elif late_volume_shock_flat_base_30:
            matched_family = "30pct_late_volume_shock_flat_base"

        if matched_family is None:
            return None

        # Actual-finder-output global quality gate.
        # Apply this only to the morning families. The late volume-shock
        # flat-base family has its own stricter base + volume-shock rules.
        if matched_family not in (
            
            "30pct_resistance_support_volume_break_retest",
            "30pct_supply_demand_failed_breakdown_absorption",
        ):
            if current_close_to_vwap_pct is None:
                return None

            if current_close_to_vwap_pct > 0.12:
                return None

            if upper_wick_pct > 0.10:
                return None

        # Do not chase stocks that already gained too much from the open
        # before the alert. The data showed 30%+ prior move before entry has
        # weaker remaining 30% profile. The late volume-shock flat-base family
        # is the only exception because it explicitly requires a fresh late
        # shock from a flat base.
        if (
            matched_family != "30pct_late_volume_shock_flat_base"
            and prior_max_gain_since_open_pct is not None
            and prior_max_gain_since_open_pct > 0.40
        ):
            return None

        return matched_family

    def _is_midday_proven_trend_expansion_30(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        LASE 12:16-style midday continuation:
        a proven intraday trend has already held VWAP/EMA structure, then
        a strong volume expansion candle appears after 11:30.
        """

        current_time = potential_confirmation_bar.bar_time.time()

        if not (
            datetime.time(11, 30)
            <= current_time
            < datetime.time(13, 0)
        ):
            return False

        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if len(bars_before_current) < 60:
            return False

        previous_bar = bars_before_current[-1]
        last_10_bars = bars_before_current[-10:]
        last_20_bars = bars_before_current[-20:]
        last_60_bars = bars_before_current[-60:]

        candle_range = potential_confirmation_bar.high - potential_confirmation_bar.low
        if candle_range <= 0:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False

        close_position_in_range = (
            potential_confirmation_bar.close - potential_confirmation_bar.low
        ) / candle_range

        upper_wick_pct = (
            potential_confirmation_bar.high
            - max(
                potential_confirmation_bar.open_value,
                potential_confirmation_bar.close,
            )
        ) / candle_range

        candle_body_pct = abs(
            potential_confirmation_bar.close - potential_confirmation_bar.open_value
        ) / candle_range

        if close_position_in_range < 0.90:
            return False

        if upper_wick_pct > 0.10:
            return False

        if candle_body_pct < 0.65:
            return False

        if previous_bar.volume <= 0:
            return False

        volume_vs_previous_bar_ratio = potential_confirmation_bar.volume / previous_bar.volume

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        if volume_vs_average_ratio < 3.00:
            return False

        if volume_vs_previous_bar_ratio < 2.00:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.vwap:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_9:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_20:
            return False

        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.ema_20:
            return False

        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.vwap:
            return False

        if potential_confirmation_bar.vwap <= 0:
            return False

        current_close_to_vwap_pct = (
            potential_confirmation_bar.close - potential_confirmation_bar.vwap
        ) / potential_confirmation_bar.vwap

        if current_close_to_vwap_pct > 0.20:
            return False

        pre_60_close_above_vwap_count = sum(
            1
            for bar_object in last_60_bars
            if bar_object.close > bar_object.vwap
        )

        if pre_60_close_above_vwap_count < 50:
            return False

        pre_60_ema9_above_vwap_count = sum(
            1
            for bar_object in last_60_bars
            if bar_object.ema_9 > bar_object.vwap
        )

        if pre_60_ema9_above_vwap_count < 50:
            return False

        return True

    def _get_previous_30pct_trend_shift_candidate_times(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        cooldown_minutes: int = 20,
        max_results: int = 1,
    ) -> list[datetime.datetime]:
        """Greedy first-valid-per-symbol/day limiter for the 30% trend-shift selector."""

        bars_until_current = self._get_today_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_bars = [
            bar_object
            for bar_object in bars_until_current
            if bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        accepted_times: list[datetime.datetime] = []

        for bar_object in previous_bars:
            if not self._is_30pct_trend_shift_candidate_base(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=bar_object,
            ):
                continue

            if accepted_times:
                minutes_since_last_accept = (
                    bar_object.bar_time - accepted_times[-1]
                ).total_seconds() / 60.0

                if minutes_since_last_accept < cooldown_minutes:
                    continue

            accepted_times.append(bar_object.bar_time)

            if len(accepted_times) >= max_results:
                break

        return accepted_times

    def is_30pct_trend_shift_candidate(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        30% trend-shift selector with live-safe limiter.

        Default behavior is first valid trend-shift alert per symbol/day.
        Exception: allow one additional midday proven-trend expansion after
        11:30, because LASE-style setups can form after a long controlled
        base even if an earlier morning alert already happened.
        """

        if not self._is_30pct_trend_shift_candidate_base(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            return False

        current_family = self._is_30pct_trend_shift_candidate_base(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        current_is_late_volume_shock_expansion = (
            current_family == "30pct_late_volume_shock_flat_base"
        )

        previous_accepted_times = self._get_previous_30pct_trend_shift_candidate_times(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            cooldown_minutes=20,
            max_results=2,
        )

        if not previous_accepted_times:
            return True

        if not current_is_late_volume_shock_expansion:
            return False

        minutes_since_last_accept = (
            potential_confirmation_bar.bar_time - previous_accepted_times[-1]
        ).total_seconds() / 60.0

        if minutes_since_last_accept < 20:
            return False

        bars_until_current = self._get_today_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_bars = [
            bar_object
            for bar_object in bars_until_current
            if bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        previous_late_volume_shock_expansions = [
            bar_object
            for bar_object in previous_bars
            if self._is_30pct_trend_shift_candidate_base(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=bar_object,
            ) == "30pct_late_volume_shock_flat_base"
        ]

        if previous_late_volume_shock_expansions:
            return False

        # Allow at most one regular first alert + one midday expansion.
        if len(previous_accepted_times) >= 2:
            return False

        return True

    def get_30pct_trend_shift_candidate_family(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> str | None:
        """
        Return the matched 30% sub-family for an accepted live signal.

        This includes the same first-alert / midday exception limiter as
        is_30pct_trend_shift_candidate(...), so it is safe for export/debug.
        """

        if not self.is_30pct_trend_shift_candidate(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            return None

        family = self._is_30pct_trend_shift_candidate_base(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        return family if isinstance(family, str) else None



    # =========================
    # Public 20% momentum entry-bar families
    # =========================

    def _safe_ratio(self, numerator: float | None, denominator: float | None) -> float | None:
        numerator = self._safe_float(numerator, None)
        denominator = self._safe_float(denominator, None)

        if numerator is None or denominator is None or denominator <= 0:
            return None

        return numerator / denominator

    def _minutes_from_open(self, bar_object: common.objects.BarData) -> int | None:
        market_open = datetime.datetime.combine(
            bar_object.bar_time.date(),
            datetime.time(9, 30),
        )
        return int((bar_object.bar_time - market_open).total_seconds() // 60)

    def _get_regular_session_bars_before_current(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[common.objects.BarData]:
        return [
            bar_object
            for bar_object in self._get_bars_before_current(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=potential_confirmation_bar,
            )
            if datetime.time(9, 30) <= bar_object.bar_time.time() <= datetime.time(16, 0)
        ]

    def _public_entry_common_candle_ok(
        self,
        potential_confirmation_bar: common.objects.BarData,
        min_volume_vs_average_ratio: float = 1.30,
        min_close_position_in_range: float = 0.60,
    ) -> bool:
        candle_range = potential_confirmation_bar.high - potential_confirmation_bar.low

        if candle_range <= 0:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False

        close_position_in_range = (
            potential_confirmation_bar.close - potential_confirmation_bar.low
        ) / candle_range

        if close_position_in_range < min_close_position_in_range:
            return False

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        if volume_vs_average_ratio < min_volume_vs_average_ratio:
            return False

        return True



    def _previous_n_bar_average_volume_ratio(
        self,
        bars_before_current: list[common.objects.BarData],
        n: int,
    ) -> float | None:
        """
        Average volume of the previous N regular-session bars divided by
        the current average volume baseline used by the most recent prior bar.

        This mirrors the exported pre_20_bar_avg_volume_ratio field closely
        enough for live filtering, and it is intentionally calculated only
        from bars that already exist before the entry bar.
        """

        if n <= 0 or not bars_before_current:
            return None

        previous_bars = bars_before_current[-n:]
        valid_volumes = [
            bar_object.volume
            for bar_object in previous_bars
            if bar_object.volume is not None and bar_object.volume >= 0
        ]

        if not valid_volumes:
            return None

        reference_bar = bars_before_current[-1]
        reference_volume_average = self._safe_float(
            getattr(reference_bar, "volume_average", None),
            None,
        )

        if reference_volume_average is None or reference_volume_average <= 0:
            return None

        return (sum(valid_volumes) / len(valid_volumes)) / reference_volume_average

    def _count_previous_strict_public_orb_breakouts_20(
        self,
        bars_before_current: list[common.objects.BarData],
        opening_range_minutes: int,
        opening_range_high: float,
    ) -> int:
        """
        Counts earlier strict ORB re-breaks before the current bar.

        This prevents late repeated ORB entries after the stock already had
        multiple breakout attempts. In the exported profile this behavior
        mapped to much cleaner rows where prior clean breakout count was low.
        """

        if opening_range_high <= 0:
            return 0

        breakout_level = opening_range_high * 1.002
        previous_bar = None
        previous_breakout_count = 0

        for bar_object in bars_before_current:
            minutes_from_open = self._minutes_from_open(bar_object)

            if minutes_from_open is None or minutes_from_open < opening_range_minutes:
                previous_bar = bar_object
                continue

            if previous_bar is None:
                previous_bar = bar_object
                continue

            if (
                previous_bar.close <= breakout_level
                and bar_object.close > breakout_level
                and self._public_entry_common_candle_ok(
                    potential_confirmation_bar=bar_object,
                    min_volume_vs_average_ratio=2.00,
                    min_close_position_in_range=0.80,
                )
            ):
                previous_breakout_count += 1

            previous_bar = bar_object

        return previous_breakout_count

    def _matches_public_orb_breakout_20(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        opening_range_minutes: int,
    ) -> bool:
        # EMA20-integrity version: keep only the cleaner ORB5 pattern.
        # ORB15 had similar same-session +20% behavior, but was weaker once
        # we demanded +20% before a future close below EMA20.
        if opening_range_minutes != 5:
            return False

        minutes_from_open = self._minutes_from_open(potential_confirmation_bar)

        if minutes_from_open is None or minutes_from_open < opening_range_minutes:
            return False

        if not self._public_entry_common_candle_ok(
            potential_confirmation_bar=potential_confirmation_bar,
            min_volume_vs_average_ratio=2.00,
            min_close_position_in_range=0.95,
        ):
            return False

        entry_close = self._safe_float(getattr(potential_confirmation_bar, "close", None), None)
        entry_ema20 = self._safe_float(getattr(potential_confirmation_bar, "ema_20", None), None)

        if entry_close is None or entry_close <= 0 or entry_ema20 is None or entry_ema20 <= 0:
            return False

        # Live-safe proxy for post-entry EMA20 integrity: require the entry bar
        # to already have meaningful cushion above EMA20. On breakout_profile(32),
        # close>=EMA20+6%, close_position>=0.95, pre20vol>=1.5 and ORB5 kept
        # 159 rows, 93.7% same-session +20% hit rate, and 62.3% reached +20%
        # before a future EMA20 close break.
        if entry_close < entry_ema20 * 1.06:
            return False

        bars_before_current = self._get_regular_session_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_20_bar_average_volume_ratio = self._previous_n_bar_average_volume_ratio(
            bars_before_current=bars_before_current,
            n=20,
        )

        # Keep the pre-entry volume expansion requirement. In the EMA20-integrity
        # version this stays paired with close >= EMA20 + 6% and close-position >= 0.95.
        if previous_20_bar_average_volume_ratio is None:
            return False

        if previous_20_bar_average_volume_ratio < 1.50:
            return False

        opening_range_bars = [
            bar_object
            for bar_object in bars_before_current
            if 0 <= self._minutes_from_open(bar_object) < opening_range_minutes
        ]

        if len(opening_range_bars) < max(2, min(opening_range_minutes, 5)):
            return False

        previous_bar = bars_before_current[-1] if bars_before_current else None
        if previous_bar is None:
            return False

        opening_range_high = max(bar_object.high for bar_object in opening_range_bars)

        if opening_range_high <= 0:
            return False

        previous_strict_orb_breakout_count = self._count_previous_strict_public_orb_breakouts_20(
            bars_before_current=bars_before_current,
            opening_range_minutes=opening_range_minutes,
            opening_range_high=opening_range_high,
        )

        if previous_strict_orb_breakout_count > 1:
            return False

        breakout_level = opening_range_high * 1.002

        return (
            potential_confirmation_bar.close > breakout_level
            and previous_bar.close <= breakout_level
        )

    def _matches_public_vwap_reclaim_20(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        if len(bars_before_current) < 3:
            return False

        previous_bar = bars_before_current[-1]

        if potential_confirmation_bar.vwap <= 0:
            return False

        if not self._public_entry_common_candle_ok(
            potential_confirmation_bar=potential_confirmation_bar,
            min_volume_vs_average_ratio=1.20,
            min_close_position_in_range=0.60,
        ):
            return False

        return (
            previous_bar.close <= previous_bar.vwap * 1.001
            and potential_confirmation_bar.close > potential_confirmation_bar.vwap * 1.002
        )

    def _matches_public_bull_flag_continuation_20(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        if len(bars_before_current) < 20:
            return False

        if not self._public_entry_common_candle_ok(
            potential_confirmation_bar=potential_confirmation_bar,
            min_volume_vs_average_ratio=1.20,
            min_close_position_in_range=0.60,
        ):
            return False

        last_20_bars = bars_before_current[-20:]
        recent_20_high_bar = max(last_20_bars, key=lambda bar_object: bar_object.high)
        recent_20_high = recent_20_high_bar.high

        if recent_20_high <= 0 or last_20_bars[0].close <= 0:
            return False

        pre_20_bar_gain_pct = (last_20_bars[-1].close - last_20_bars[0].close) / last_20_bars[0].close
        pullback_from_recent_20_high_pct = (recent_20_high - potential_confirmation_bar.low) / recent_20_high
        minutes_since_recent_20_high = (
            potential_confirmation_bar.bar_time - recent_20_high_bar.bar_time
        ).total_seconds() / 60.0

        return (
            pre_20_bar_gain_pct >= 0.20
            and pullback_from_recent_20_high_pct <= 0.30
            and minutes_since_recent_20_high <= 5
            and potential_confirmation_bar.close >= recent_20_high * 0.985
        )

    def _matches_public_ema_macd_continuation_20(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        if len(bars_before_current) < 3:
            return False

        if not self._public_entry_common_candle_ok(
            potential_confirmation_bar=potential_confirmation_bar,
            min_volume_vs_average_ratio=1.10,
            min_close_position_in_range=0.60,
        ):
            return False

        previous_bar = bars_before_current[-1]
        current_histogram = getattr(potential_confirmation_bar, "histogram", None)
        previous_histogram = getattr(previous_bar, "histogram", None)

        if current_histogram is None:
            current_histogram = getattr(potential_confirmation_bar, "macd_histogram", None)
        if previous_histogram is None:
            previous_histogram = getattr(previous_bar, "macd_histogram", None)

        return (
            potential_confirmation_bar.close > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
            and self._safe_float(getattr(potential_confirmation_bar, "macd", None), 0.0) > 0
            and self._safe_float(current_histogram, 0.0) > 0
            and self._safe_float(previous_histogram, 0.0) <= self._safe_float(current_histogram, 0.0)
        )

    def _matches_public_volume_breakout_20(
        self,
        bars_before_current: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        if len(bars_before_current) < 20:
            return False

        if not self._public_entry_common_candle_ok(
            potential_confirmation_bar=potential_confirmation_bar,
            min_volume_vs_average_ratio=1.50,
            min_close_position_in_range=0.65,
        ):
            return False

        recent_20_high = max(bar_object.high for bar_object in bars_before_current[-20:])

        if recent_20_high <= 0:
            return False

        previous_bar = bars_before_current[-1]
        breakout_level = recent_20_high * 1.002

        return (
            potential_confirmation_bar.close > breakout_level
            and previous_bar.close <= breakout_level
        )

    def get_public_20pct_momentum_entry_families(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[str]:
        """
        Public momentum entry-bar detector for the 20% continuation study.

        It detects first actionable entry bars, not every continuation bar:
        ORB5, ORB15, VWAP reclaim, bull-flag continuation, EMA/MACD
        continuation, and volume-confirmed recent-high breakout.
        """

        current_time = potential_confirmation_bar.bar_time.time()

        if not (datetime.time(9, 30) <= current_time <= datetime.time(16, 0)):
            return []

        bars_before_current = self._get_regular_session_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if not bars_before_current:
            return []

        matched_families: list[str] = []

        if self._matches_public_orb_breakout_20(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            opening_range_minutes=5,
        ):
            matched_families.append("20pct_public_orb5_breakout")

        if self._matches_public_orb_breakout_20(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            opening_range_minutes=15,
        ):
            matched_families.append("20pct_public_orb15_breakout")

        if self._matches_public_vwap_reclaim_20(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            matched_families.append("20pct_public_vwap_reclaim")

        if self._matches_public_bull_flag_continuation_20(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            matched_families.append("20pct_public_bull_flag_continuation")

        if self._matches_public_ema_macd_continuation_20(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            matched_families.append("20pct_public_ema_macd_continuation")

        if self._matches_public_volume_breakout_20(
            bars_before_current=bars_before_current,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            matched_families.append("20pct_public_volume_breakout")

        return matched_families

    def get_public_20pct_momentum_entry_family(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> str | None:
        matched_families = self.get_public_20pct_momentum_entry_families(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if not matched_families:
            return None

        # EMA20-integrity live proxy: ORB5 only. ORB15 is intentionally disabled
        # inside _matches_public_orb_breakout_20 for this version.
        if "20pct_public_orb5_breakout" in matched_families:
            return "20pct_public_orb5_breakout_ema20_integrity"

        return None

    def get_strict_public_orb_20pct_momentum_entry_family(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> str | None:
        """
        Backward-compatible name used by breakout_finder.

        The strict experiment keeps only ORB5 / ORB15 public momentum entries.
        This method intentionally delegates to get_public_20pct_momentum_entry_family(),
        whose current implementation already returns only strict ORB families.
        """

        return self.get_public_20pct_momentum_entry_family(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

    def is_strict_public_orb_20pct_momentum_entry_candidate(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        return self.get_strict_public_orb_20pct_momentum_entry_family(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        ) is not None

    def is_public_20pct_momentum_entry_candidate(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        return self.get_public_20pct_momentum_entry_family(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        ) is not None



    def _get_bars_until_current(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> list[common.objects.BarData]:
        """
        Return all 1-minute bars up to and including the candidate bar.
        Kept small and live-safe: it only uses bars already known at the candidate bar.
        """
        return [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if bar_object.bar_time <= potential_confirmation_bar.bar_time
        ]

    def _bar_close_position_in_range(
        self,
        bar_object: common.objects.BarData,
    ) -> float | None:
        candle_range = bar_object.high - bar_object.low
        if candle_range <= 0:
            return None
        return (bar_object.close - bar_object.low) / candle_range

    def _bar_gain_pct(
        self,
        bar_object: common.objects.BarData,
    ) -> float | None:
        if bar_object.open_value <= 0:
            return None
        return (bar_object.close / bar_object.open_value) - 1.0

    def _volume_vs_average_ratio(
        self,
        bar_object: common.objects.BarData,
    ) -> float | None:
        if bar_object.volume_average <= 0:
            return None
        return bar_object.volume / bar_object.volume_average

    def _matches_no_sellers_continuation_20pct_30min_entry(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        Live-safe EMA9-defended volatile continuation entry.

        This detector is designed for the pattern described by HKIT 2026-06-01
        around 10:08-10:10:
        - the previous 5 bars are already volatile, not dead tape
        - buyers are defending price around EMA9 / EMA20
        - EMA9 is above EMA20, and EMA9 is above VWAP
        - price stays above VWAP and the MACD histogram is positive
        - the signal bar is either a continuation break or a defended-pullback
          reclaim bar

        The future +10% within 30 minutes is measured by breakout_finder only;
        nothing below uses future bars.
        """

        current_time = potential_confirmation_bar.bar_time.time()
        if not (datetime.time(9, 35) <= current_time <= datetime.time(16, 0)):
            return False

        bars_until_current = self._get_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )
        if len(bars_until_current) < 11:
            return False

        previous_5_bars = bars_until_current[-6:-1]
        previous_10_bars = bars_until_current[-11:-1]
        previous_bar = previous_5_bars[-1]

        close_position_in_range = self._bar_close_position_in_range(potential_confirmation_bar)
        bar_gain_pct = self._bar_gain_pct(potential_confirmation_bar)
        volume_vs_average_ratio = self._volume_vs_average_ratio(potential_confirmation_bar)

        if close_position_in_range is None or bar_gain_pct is None or volume_vs_average_ratio is None:
            return False

        current_histogram = getattr(potential_confirmation_bar, "histogram", None)
        if current_histogram is None:
            current_histogram = getattr(potential_confirmation_bar, "macd_histogram", None)

        if (
            potential_confirmation_bar.close <= 0
            or potential_confirmation_bar.open_value <= 0
            or potential_confirmation_bar.ema_9 <= 0
            or potential_confirmation_bar.ema_20 <= 0
            or potential_confirmation_bar.vwap <= 0
        ):
            return False

        previous_10_high = max(bar_object.high for bar_object in previous_10_bars)
        if previous_10_high <= 0:
            return False

        pre_5_first_close = previous_5_bars[0].close
        if pre_5_first_close <= 0:
            return False

        pre_5_bar_gain_pct = (previous_5_bars[-1].close / pre_5_first_close) - 1.0
        current_plus_pre_5_gain_pct = (potential_confirmation_bar.close / pre_5_first_close) - 1.0

        previous_5_range_pcts = [
            ((bar_object.high - bar_object.low) / bar_object.open_value)
            for bar_object in previous_5_bars
            if bar_object.open_value > 0
        ]
        if len(previous_5_range_pcts) < 5:
            return False
        previous_5_average_range_pct = sum(previous_5_range_pcts) / len(previous_5_range_pcts)
        previous_5_max_range_pct = max(previous_5_range_pcts)

        previous_5_volume_ratios = [
            self._volume_vs_average_ratio(bar_object)
            for bar_object in previous_5_bars
            if self._volume_vs_average_ratio(bar_object) is not None
        ]
        if len(previous_5_volume_ratios) < 5:
            return False
        previous_5_average_volume_ratio = sum(previous_5_volume_ratios) / len(previous_5_volume_ratios)

        previous_5_close_above_ema9_count = sum(
            1
            for bar_object in previous_5_bars
            if bar_object.ema_9 > 0 and bar_object.close >= bar_object.ema_9 * 0.995
        )
        previous_5_low_defended_ema9_count = sum(
            1
            for bar_object in previous_5_bars
            if bar_object.ema_9 > 0 and bar_object.low >= bar_object.ema_9 * 0.975
        )
        previous_5_low_defended_ema20_count = sum(
            1
            for bar_object in previous_5_bars
            if bar_object.ema_20 > 0 and bar_object.low >= bar_object.ema_20 * 0.985
        )
        previous_5_close_above_vwap_count = sum(
            1
            for bar_object in previous_5_bars
            if bar_object.vwap > 0 and bar_object.close >= bar_object.vwap
        )
        previous_5_higher_or_flat_low_count = sum(
            1
            for index in range(1, len(previous_5_bars))
            if previous_5_bars[index].low >= previous_5_bars[index - 1].low * 0.98
        )

        close_breaks_previous_10_high = potential_confirmation_bar.close >= previous_10_high * 0.995
        high_breaks_previous_10_high = potential_confirmation_bar.high >= previous_10_high * 1.005
        defended_pullback_reclaim = (
            potential_confirmation_bar.close >= max(bar_object.close for bar_object in previous_5_bars) * 1.003
            and potential_confirmation_bar.close >= previous_bar.close * 1.025
            and close_position_in_range >= 0.85
        )

        # Current alignment: trend is above the important support stack.
        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False
        if potential_confirmation_bar.close < potential_confirmation_bar.ema_9 * 1.005:
            return False
        if potential_confirmation_bar.low < potential_confirmation_bar.ema_9 * 0.965:
            return False
        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.ema_20:
            return False
        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.vwap:
            return False
        if potential_confirmation_bar.close <= potential_confirmation_bar.vwap:
            return False
        if self._safe_float(current_histogram, 0.0) <= 0.0:
            return False

        # Environment: the 5 bars before are already volatile and buyer-defended.
        if previous_5_average_range_pct < 0.04:
            return False
        if previous_5_max_range_pct < 0.065:
            return False
        if previous_5_average_volume_ratio < 1.05:
            return False
        if previous_5_close_above_ema9_count < 4:
            return False
        if previous_5_low_defended_ema9_count < 4:
            return False
        if previous_5_low_defended_ema20_count < 4:
            return False
        if previous_5_close_above_vwap_count < 4:
            return False
        if previous_5_higher_or_flat_low_count < 2:
            return False

        # Buyers must already be walking it up, or the signal bar must turn the
        # defended pullback into a meaningful continuation leg.
        if pre_5_bar_gain_pct < 0.015 and current_plus_pre_5_gain_pct < 0.06:
            return False

        # Signal bar: either a new continuation high or a defended-pullback reclaim
        # like HKIT 10:08.
        if not (close_breaks_previous_10_high or high_breaks_previous_10_high or defended_pullback_reclaim):
            return False
        if volume_vs_average_ratio < 0.75 and potential_confirmation_bar.volume < 250000:
            return False
        if close_position_in_range < 0.68:
            return False

        return True



    def _matches_behavioral_buyer_control_phase_20pct_30min_entry(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        v5 base definition: movement started, then an internal resistance
        inside that movement becomes support on a pullback toward EMA9, while
        the pullback still closes above EMA9.

        This intentionally makes resistance->support the BASE trigger, not an
        optional confirmation.  Other behaviors only strengthen or weaken the
        setup:
        - active prior volume;
        - EMA9/EMA20 rising;
        - EMA9 expanding away from EMA20 and VWAP;
        - many bars printing higher highs;
        - sellers appear on pullbacks, but buyers defend EMA9 / the old level;
        - MACD histogram turns back up or re-accelerates near the entry.

        Live-safe: uses only bars up to and including the current bar.
        """

        current_time = potential_confirmation_bar.bar_time.time()
        if not (datetime.time(9, 35) <= current_time <= datetime.time(16, 0)):
            return False

        bars_until_current = self._get_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )
        if len(bars_until_current) < 12:
            return False

        current_index = len(bars_until_current) - 1
        current_bar = potential_confirmation_bar
        previous_bar = bars_until_current[-2]

        # Reset metadata for this evaluation.  It will be populated only if the
        # exact resistance/support/control sequence is validated below.
        self._last_behavioral_buyer_control_phase_20pct_30min_entry_context = None

        def safe(value, default=None):
            try:
                if value is None:
                    return default
                value = float(value)
                if value != value:
                    return default
                return value
            except Exception:
                return default

        def close_position(bar_object: common.objects.BarData) -> float | None:
            candle_range = safe(bar_object.high, 0.0) - safe(bar_object.low, 0.0)
            if candle_range <= 0:
                return None
            return (bar_object.close - bar_object.low) / candle_range

        def upper_wick_share(bar_object: common.objects.BarData) -> float | None:
            candle_range = safe(bar_object.high, 0.0) - safe(bar_object.low, 0.0)
            if candle_range <= 0:
                return None
            return (bar_object.high - max(bar_object.open_value, bar_object.close)) / candle_range

        def range_pct(bar_object: common.objects.BarData) -> float | None:
            if safe(bar_object.open_value, 0.0) <= 0:
                return None
            return (bar_object.high - bar_object.low) / bar_object.open_value

        def body_pct_of_price(bar_object: common.objects.BarData) -> float | None:
            if safe(bar_object.open_value, 0.0) <= 0:
                return None
            return abs(bar_object.close - bar_object.open_value) / bar_object.open_value

        def volume_ratio(bar_object: common.objects.BarData) -> float | None:
            if safe(bar_object.volume_average, 0.0) <= 0:
                return None
            return bar_object.volume / bar_object.volume_average

        def histogram_value(bar_object: common.objects.BarData) -> float | None:
            histogram = getattr(bar_object, "histogram", None)
            if histogram is None:
                histogram = getattr(bar_object, "macd_histogram", None)
            return safe(histogram, None)

        def ema9_ema20_gap(bar_object: common.objects.BarData) -> float | None:
            if safe(bar_object.ema_20, 0.0) <= 0:
                return None
            return (bar_object.ema_9 - bar_object.ema_20) / bar_object.ema_20

        def ema9_vwap_gap(bar_object: common.objects.BarData) -> float | None:
            if safe(bar_object.vwap, 0.0) <= 0:
                return None
            return (bar_object.ema_9 - bar_object.vwap) / bar_object.vwap

        def average(values: list[float | None]) -> float | None:
            cleaned = [value for value in values if value is not None and value == value]
            if not cleaned:
                return None
            return sum(cleaned) / len(cleaned)

        def true_count(values: list[bool]) -> int:
            return sum(1 for value in values if value)

        def is_constructive_close(bar_object: common.objects.BarData) -> bool:
            cp = close_position(bar_object)
            uw = upper_wick_share(bar_object)
            return (
                cp is not None
                and uw is not None
                and bar_object.close >= bar_object.open_value
                and cp >= 0.65
                and uw <= 0.35
            )

        # ------------------------------------------------------------------
        # 1) Find the movement start / demand ignition bar.
        # ------------------------------------------------------------------
        anchor_index = None
        start_index = max(1, current_index - 45)

        for index in range(start_index, current_index - 3):
            bar_object = bars_until_current[index]
            previous_object = bars_until_current[index - 1]
            before_anchor = bars_until_current[max(0, index - 5):index]

            cp = close_position(bar_object)
            uw = upper_wick_share(bar_object)
            br = body_pct_of_price(bar_object)
            rp = range_pct(bar_object)
            vr = volume_ratio(bar_object)
            previous_br = body_pct_of_price(previous_object)
            previous_rp = range_pct(previous_object)
            previous_vr = volume_ratio(previous_object)
            typical_range = average([range_pct(bar) for bar in before_anchor])
            typical_volume = average([volume_ratio(bar) for bar in before_anchor])

            if cp is None or uw is None or br is None or rp is None:
                continue

            ignition_score = 0

            # Strong close with little upper wick: the first clear demand bar.
            if bar_object.close > bar_object.open_value:
                ignition_score += 1
            if cp >= 0.78:
                ignition_score += 2
            if uw <= 0.22:
                ignition_score += 1

            # Price action expands versus immediate/past bars.
            if previous_br is not None and br > previous_br:
                ignition_score += 1
            if previous_rp is not None and rp > previous_rp:
                ignition_score += 1
            if typical_range is not None and rp > typical_range:
                ignition_score += 1

            # Volume expands versus average and/or previous tape.
            if vr is not None and vr >= 1.0:
                ignition_score += 1
            if vr is not None and previous_vr is not None and vr > previous_vr:
                ignition_score += 1
            if vr is not None and typical_volume is not None and vr > typical_volume:
                ignition_score += 1

            # It pushes through very near-term supply.
            previous_3_high = max(bar.high for bar in bars_until_current[max(0, index - 3):index])
            if bar_object.close >= previous_3_high:
                ignition_score += 1

            # v14 regression fix: do not accept weak opening/noise bars as the
            # movement anchor.  The anchor must itself be a visible demand-start
            # candle, like HKIT 09:46: green, strong close, little upper wick,
            # and preferably breaking nearby supply.  Also keep scanning and pick
            # the strongest/later valid anchor instead of the first one, because
            # early noisy bars can otherwise pollute the whole phase calculation.
            valid_ignition_anchor = (
                bar_object.close > bar_object.open_value
                and cp >= 0.75
                and uw <= 0.25
                and vr is not None
                and vr >= 1.0
                and bar_object.close >= previous_3_high
            )

            if ignition_score >= 6 and valid_ignition_anchor:
                if anchor_index is None:
                    anchor_index = index
                    anchor_score = ignition_score
                else:
                    # Prefer the later/equally strong demand-start bar so HKIT
                    # anchors near 09:46 instead of an earlier noisy candle.
                    if ignition_score >= anchor_score:
                        anchor_index = index
                        anchor_score = ignition_score

        if anchor_index is None:
            return False

        phase_bars = bars_until_current[anchor_index:current_index + 1]
        before_current_phase_bars = bars_until_current[anchor_index:current_index]
        if len(phase_bars) < 5 or len(phase_bars) > 42:
            return False

        previous_3_bars = bars_until_current[max(0, current_index - 3):current_index]
        previous_5_bars = bars_until_current[max(0, current_index - 5):current_index]
        previous_10_bars = bars_until_current[max(0, current_index - 10):current_index]
        if len(previous_5_bars) < 5:
            return False

        current_cp = close_position(current_bar)
        current_uw = upper_wick_share(current_bar)
        if current_cp is None or current_uw is None:
            return False

        # Current candle cannot be seller-controlled.  It may be a retest bar,
        # but it must close above EMA9 and not leave a heavy upper wick.
        if current_bar.close < current_bar.ema_9:
            return False
        if current_bar.ema_9 <= current_bar.ema_20:
            return False
        if current_bar.ema_9 <= current_bar.vwap and current_bar.close <= current_bar.vwap:
            return False
        if current_uw > 0.45:
            return False

        # ------------------------------------------------------------------
        # 2) BASE: previous resistance inside the movement became support on a
        #    pullback toward EMA9, and that pullback closed above EMA9.
        # ------------------------------------------------------------------
        resistance_support_found = False
        best_level = None
        best_anchor_bar = bars_until_current[anchor_index]
        best_resistance_bar = None
        best_break_bar = None
        best_support_bar = None
        best_conflict_high = None
        best_conflict_close_high = None
        best_minutes_since_retest = None
        valid_resistance_support_candidates = []

        # Search only inside the current movement, with preference to the last
        # roughly 10 bars.  This is the user's base definition.
        resistance_search_start = max(anchor_index + 1, current_index - 14)
        resistance_search_end = current_index - 2

        for resistance_index in range(resistance_search_start, resistance_search_end + 1):
            resistance_bar = bars_until_current[resistance_index]
            level = resistance_bar.high
            if level <= 0:
                continue

            # The level must have actually acted like meaningful resistance/supply
            # inside the movement.  Earlier versions treated almost any prior high
            # as resistance; that incorrectly allowed HKIT 10:03/10:05 to pass via
            # weak/older levels such as 09:53.
            #
            # For this pattern, the resistance bar should itself be a visible
            # supply/acceptance shelf: it closes strong enough near its high and
            # has active volume.  This keeps valid HKIT levels such as 09:55 and
            # 10:03, while excluding weak intermediate highs that are not the
            # resistance/support structure the user is defining.
            resistance_cp = close_position(resistance_bar)
            resistance_uw = upper_wick_share(resistance_bar)
            resistance_volume_ratio = volume_ratio(resistance_bar)
            level_was_resistance = (
                resistance_bar.close <= level * 1.005
                and resistance_cp is not None
                and resistance_cp >= 0.68
                and (resistance_uw is None or resistance_uw <= 0.36)
                and resistance_volume_ratio is not None
                and resistance_volume_ratio >= 1.20
            )
            if not level_was_resistance:
                continue

            # After the level was created, buyers broke/accepted above it.
            breakout_indices = []
            for break_index in range(resistance_index + 1, current_index):
                break_bar = bars_until_current[break_index]
                if (
                    break_bar.close >= level * 1.002
                    and is_constructive_close(break_bar)
                ):
                    breakout_indices.append(break_index)

            if not breakout_indices:
                continue

            # Then during a pullback, that old resistance is defended as support
            # while price also defends/closes above EMA9.
            # v17: the retest must be COMPLETED BEFORE the entry bar and the entry must come
            # after buyers had time to prove that the old resistance is support.
            # This fixes HKIT: 10:03 is only the resistance/break area, 10:07 is
            # the support proof, and 10:10 is the cleaner re-acceleration entry.
            for break_index in breakout_indices:
                for retest_index in range(break_index + 1, current_index):
                    retest_bar = bars_until_current[retest_index]
                    # v18: true resistance -> support must defend the same price zone.
                    # The prior versions were too loose because they allowed a bar that
                    # dipped far below the resistance level to count as support if it later
                    # closed back near/above the level.  That incorrectly validated cases like:
                    #   resistance 10:01 high -> support 10:03 low on HKIT
                    # where the low was far below the supposed support zone.
                    #
                    # A real support confirmation should either touch the old level from
                    # slightly above/slightly below, or hold above it, while closing above
                    # EMA9.  The low must NOT be materially below the old resistance.
                    # v19: strict true resistance -> support.
                    #
                    # The support bar must actually defend the old resistance zone.
                    # It is NOT enough that the bar later closes back above the level.
                    # If the low falls materially below the old resistance, this is a
                    # deeper pullback, not resistance becoming support.
                    #
                    # HKIT regression examples:
                    #   invalid: 10:01 high 4.92 -> 10:03 low 4.5001
                    #   invalid: 10:03 high 5.06 -> 10:05 low 4.7501
                    #   valid:   09:55 high 4.60 -> 10:04 low 4.66
                    #   valid:   10:03 high 5.06 -> 10:07 low 5.03
                    support_zone_low = level * 0.985
                    support_zone_high = level * 1.035

                    retest_low_defends_same_zone = (
                        retest_bar.low >= support_zone_low
                        and retest_bar.low <= support_zone_high
                    )
                    retest_close_reclaims_or_holds_zone = retest_bar.close >= level * 0.995
                    retest_toward_ema9 = retest_bar.low <= retest_bar.ema_9 * 1.06
                    retest_closes_above_ema9 = retest_bar.close >= retest_bar.ema_9
                    not_deep_ema20_break = retest_bar.close >= retest_bar.ema_20 * 0.99

                    if not (
                        retest_low_defends_same_zone
                        and retest_close_reclaims_or_holds_zone
                        and retest_toward_ema9
                        and retest_closes_above_ema9
                        and not_deep_ema20_break
                    ):
                        continue

                    # Current bar should be the buyer-control re-break AFTER the completed
                    # support proof. It should overcome the conflict/seller area created
                    # after the resistance breakout, not just close green while still inside
                    # that supply.  This matches HKIT:
                    #   10:03 resistance -> 10:07 support -> 10:09 sellers still exist ->
                    #   10:10 crosses the conflict area and buyers take control.
                    bars_since_retest = current_index - retest_index
                    try:
                        minutes_since_retest = (current_bar.bar_time - retest_bar.bar_time).total_seconds() / 60.0
                    except Exception:
                        minutes_since_retest = float(bars_since_retest)

                    conflict_bars = bars_until_current[break_index + 1:current_index]
                    conflict_high = max([level] + [bar.high for bar in conflict_bars])
                    recent_conflict_close_high = max([level] + [bar.close for bar in conflict_bars])

                    # v19: entry/control bar must close through the conflict/seller area.
                    # A high wick through supply is not enough.  This prevents bars like
                    # HKIT 10:09 from being treated as buyer-control; 10:10 qualifies
                    # because it closes above the 10:06/10:09 seller area.
                    current_breaks_conflict_area = (
                        current_bar.close >= conflict_high * 0.998
                        and current_bar.close >= recent_conflict_close_high
                        and current_cp >= 0.72
                    )
                    current_rebreaks_or_holds = (
                        current_bar.close >= level
                        and current_bar.close >= current_bar.ema_9
                        and current_breaks_conflict_area
                    )

                    if 1 <= minutes_since_retest <= 8 and current_rebreaks_or_holds:
                        valid_resistance_support_candidates.append(
                            {
                                "level": level,
                                "resistance_bar": resistance_bar,
                                "break_bar": bars_until_current[break_index],
                                "support_bar": retest_bar,
                                "conflict_high": conflict_high,
                                "conflict_close_high": recent_conflict_close_high,
                                "minutes_since_retest": minutes_since_retest,
                                "support_index": retest_index,
                                "resistance_index": resistance_index,
                                "break_index": break_index,
                                "pattern_type": "resistance_support_retest",
                            }
                        )

                # v23: double-down / higher-low absorption variant.
                #
                # NEXR shows a structure that is related to resistance->support,
                # but the cleaner read is not a single support retest.  The old
                # resistance is created first, buyers accept above it, then the
                # stock makes a new previous high. Sellers push it down twice,
                # but both pullback lows stay defended above/near the old
                # resistance and around EMA9.  The entry is the current bar
                # breaking above the previous high after that double-defense.
                #
                # NEXR example:
                #   10:11 high = old resistance (~1.85)
                #   10:13 high = previous highest high before entry (~2.01)
                #   10:14 low ~= first down (~1.88)
                #   10:16 low ~= second down / lowest low between 10:13 and 10:17 (~1.87)
                #   10:17 breaks 10:13 high and buyers take control.
                post_break_indices = list(range(break_index + 1, current_index))
                if len(post_break_indices) >= 4:
                    previous_high_index = max(
                        post_break_indices,
                        key=lambda candidate_index: bars_until_current[candidate_index].high,
                    )
                    previous_high_bar = bars_until_current[previous_high_index]

                    pullback_indices = list(range(previous_high_index + 1, current_index))
                    defended_pullback_indices = []
                    for pullback_index in pullback_indices:
                        pullback_bar = bars_until_current[pullback_index]

                        low_above_old_resistance_zone = pullback_bar.low >= level * 0.995
                        low_not_too_far_above_old_resistance = pullback_bar.low <= level * 1.09
                        pullback_defends_ema9 = (
                            pullback_bar.low <= pullback_bar.ema_9 * 1.045
                            and pullback_bar.close >= pullback_bar.ema_9 * 0.995
                        )
                        pullback_has_seller_pressure = (
                            pullback_bar.close < pullback_bar.open_value
                            or (
                                upper_wick_share(pullback_bar) is not None
                                and upper_wick_share(pullback_bar) >= 0.20
                            )
                        )

                        if (
                            low_above_old_resistance_zone
                            and low_not_too_far_above_old_resistance
                            and pullback_defends_ema9
                            and pullback_has_seller_pressure
                        ):
                            defended_pullback_indices.append(pullback_index)

                    if len(defended_pullback_indices) >= 2:
                        first_down_index = defended_pullback_indices[0]
                        second_down_index = defended_pullback_indices[-1]
                        first_down_bar = bars_until_current[first_down_index]
                        second_down_bar = bars_until_current[second_down_index]

                        first_low = first_down_bar.low
                        second_low = second_down_bar.low
                        lows_form_same_defended_zone = (
                            first_low > 0
                            and second_low > 0
                            and abs(second_low - first_low) / first_low <= 0.045
                            and second_low >= level * 0.995
                        )

                        # v27 strict double-down rule:
                        # The second down must be the final defended low before the entry.
                        # If any later bar makes a lower low before the entry, the double-down
                        # absorption structure is broken and this must not qualify.
                        # Example: NEXR valid structure has 10:14 low ~= 1.88,
                        # 10:16 low ~= 1.87, then no lower low before 10:17 breaks the high.
                        second_down_is_lowest_after_previous_high = (
                            second_low <= min(
                                bars_until_current[index].low
                                for index in pullback_indices
                            ) * 1.001
                        )
                        no_lower_low_after_second_down_before_entry = all(
                            bars_until_current[index].low >= second_low * 0.999
                            for index in range(second_down_index + 1, current_index)
                        )

                        try:
                            minutes_since_second_down = (
                                current_bar.bar_time - second_down_bar.bar_time
                            ).total_seconds() / 60.0
                        except Exception:
                            minutes_since_second_down = float(current_index - second_down_index)

                        current_breaks_previous_high = (
                            current_bar.close >= previous_high_bar.high * 0.998
                            and current_bar.high > previous_high_bar.high
                            and current_cp >= 0.72
                        )

                        if (
                            lows_form_same_defended_zone
                            and second_down_is_lowest_after_previous_high
                            and no_lower_low_after_second_down_before_entry
                            and 1 <= minutes_since_second_down <= 5
                            and current_breaks_previous_high
                        ):
                            valid_resistance_support_candidates.append(
                                {
                                    "level": level,
                                    "resistance_bar": resistance_bar,
                                    "break_bar": bars_until_current[break_index],
                                    "support_bar": second_down_bar,
                                    "conflict_high": previous_high_bar.high,
                                    "conflict_close_high": previous_high_bar.close,
                                    "minutes_since_retest": minutes_since_second_down,
                                    "support_index": second_down_index,
                                    "resistance_index": resistance_index,
                                    "break_index": break_index,
                                    "pattern_type": "double_down_defended_support_break",
                                    "pattern_priority": 3,
                                    "first_down_bar": first_down_bar,
                                    "previous_high_bar": previous_high_bar,
                                }
                            )
                if resistance_support_found:
                    break
            if resistance_support_found:
                break


        # v26: WOK late-day structures.
        #
        # These are additional validated support/control patterns from WOK
        # 2026-05-11.  They are intentionally separate from the original
        # HKIT/NEXR branches because the base behavior is not always one
        # exact resistance touch followed by one exact support retest.
        #
        # 1) multi_touch_resistance_support_control_break:
        #    A resistance shelf has multiple highs near the same level, then
        #    later two or more pullback lows defend that same zone near EMA9,
        #    and the current bar closes through the conflict/seller high.
        #    WOK examples:
        #      15:27/15:29 resistance -> 15:34/15:35 support -> 15:37 entry
        #      15:39 resistance -> 15:49/15:50/15:56 support -> 15:59 entry
        #
        # 2) two_support_after_breakup_high_break:
        #    After a fast breakout leg, price prints two defended pullbacks in
        #    the same area, then the current bar breaks the highest high formed
        #    after those supports.  WOK example:
        #      15:38/15:40 supports -> 15:45 breaks highest high.
        extra_candidate_start = max(1, current_index - 35)

        for resistance_index in range(extra_candidate_start, current_index - 3):
            resistance_bar = bars_until_current[resistance_index]
            level = resistance_bar.high
            if level <= 0:
                continue

            # The resistance should be a visible shelf/supply level, preferably
            # with another nearby high before the pullback support appears.
            nearby_resistance_touches = [
                index
                for index in range(max(anchor_index, resistance_index - 4), min(current_index, resistance_index + 4))
                if index != resistance_index
                and abs(bars_until_current[index].high - level) / level <= 0.025
            ]
            resistance_is_visible_shelf = len(nearby_resistance_touches) >= 1

            resistance_vr = volume_ratio(resistance_bar)
            resistance_cp = close_position(resistance_bar)
            if not (
                resistance_is_visible_shelf
                or (
                    resistance_vr is not None
                    and resistance_vr >= 1.0
                    and (
                        (
                            resistance_cp is not None
                            and resistance_cp >= 0.55
                        )
                        or (
                            upper_wick_share(resistance_bar) is not None
                            and upper_wick_share(resistance_bar) >= 0.25
                        )
                    )
                )
            ):
                continue

            # First, the shelf must actually break.  Supports that happened
            # before the break are ignored.  This prevents lower accepted prices
            # from being mislabeled as resistance just because later bars traded
            # above them.
            shelf_break_index = None
            for candidate_break_index in range(resistance_index + 1, current_index):
                candidate_break_bar = bars_until_current[candidate_break_index]
                if (
                    candidate_break_bar.close >= level * 1.035
                    and candidate_break_bar.high > level
                    and close_position(candidate_break_bar) is not None
                    and close_position(candidate_break_bar) >= 0.55
                ):
                    shelf_break_index = candidate_break_index
                    break

            if shelf_break_index is None:
                continue

            support_indices = []
            for support_index in range(shelf_break_index + 1, current_index):
                support_bar = bars_until_current[support_index]
                support_low_near_level = (
                    support_bar.low >= level * 0.965
                    and support_bar.low <= level * 1.035
                )
                support_holds_ema9 = (
                    support_bar.close >= support_bar.ema_9 * 0.985
                    and support_bar.low <= support_bar.ema_9 * 1.12
                )
                support_holds_or_reclaims_level = support_bar.close >= level * 0.985
                if support_low_near_level and support_holds_ema9 and support_holds_or_reclaims_level:
                    support_indices.append(support_index)

            if len(support_indices) >= 2:
                first_support_index = support_indices[0]
                last_support_index = support_indices[-1]
                last_support_bar = bars_until_current[last_support_index]
                conflict_bars = bars_until_current[last_support_index + 1:current_index]
                conflict_high = max([level] + [bar.high for bar in conflict_bars])
                conflict_close_high = max([level] + [bar.close for bar in conflict_bars])

                current_breaks_conflict = (
                    current_bar.close >= conflict_high * 0.995
                    and current_bar.close >= conflict_close_high * 0.995
                    and current_cp >= 0.60
                )
                try:
                    minutes_since_support = (current_bar.bar_time - last_support_bar.bar_time).total_seconds() / 60.0
                except Exception:
                    minutes_since_support = float(current_index - last_support_index)

                if current_breaks_conflict and 2 <= minutes_since_support <= 8:
                    valid_resistance_support_candidates.append(
                        {
                            "level": level,
                            "resistance_bar": resistance_bar,
                            "break_bar": bars_until_current[shelf_break_index],
                            "support_bar": last_support_bar,
                            "conflict_high": conflict_high,
                            "conflict_close_high": conflict_close_high,
                            "minutes_since_retest": minutes_since_support,
                            "support_index": last_support_index,
                            "resistance_index": resistance_index,
                            "break_index": shelf_break_index,
                            "pattern_type": "multi_touch_resistance_support_control_break",
                            "pattern_priority": 2,
                            "first_down_bar": bars_until_current[first_support_index],
                        }
                    )

        # WOK second entry type: two defended supports after a breakout leg,
        # then current bar breaks the highest high created after the first support.
        two_support_search_start = max(1, current_index - 14)
        for first_support_index in range(two_support_search_start, current_index - 3):
            first_support_bar = bars_until_current[first_support_index]
            for second_support_index in range(first_support_index + 1, current_index):
                second_support_bar = bars_until_current[second_support_index]
                first_low = first_support_bar.low
                second_low = second_support_bar.low
                if first_low <= 0 or second_low <= 0:
                    continue

                lows_same_defended_area = abs(second_low - first_low) / first_low <= 0.055
                both_defend_ema9 = (
                    first_support_bar.close >= first_support_bar.ema_9 * 0.985
                    and second_support_bar.close >= second_support_bar.ema_9 * 0.985
                    and first_support_bar.low <= first_support_bar.ema_9 * 1.12
                    and second_support_bar.low <= second_support_bar.ema_9 * 1.12
                )
                if not (lows_same_defended_area and both_defend_ema9):
                    continue

                high_window = bars_until_current[first_support_index + 1:current_index]
                if not high_window:
                    continue
                previous_high_bar = max(high_window, key=lambda bar: bar.high)
                current_breaks_previous_high = (
                    current_cp >= 0.60
                    and (
                        current_bar.close >= previous_high_bar.high * 1.015
                        or current_bar.high >= previous_high_bar.high * 1.05
                    )
                )
                try:
                    minutes_since_second_support = (current_bar.bar_time - second_support_bar.bar_time).total_seconds() / 60.0
                except Exception:
                    minutes_since_second_support = float(current_index - second_support_index)

                # v27 strict two-support/double-down rule:
                # The second support must be the final lowest defended low before entry.
                # If any later bar undercuts it before the entry, buyers did not fully defend
                # the double-down zone yet.
                second_support_is_lowest_defense = (
                    second_low <= min(
                        bars_until_current[index].low
                        for index in range(first_support_index + 1, current_index)
                    ) * 1.001
                )
                no_lower_low_after_second_support_before_entry = all(
                    bars_until_current[index].low >= second_low * 0.999
                    for index in range(second_support_index + 1, current_index)
                )

                if (
                    current_breaks_previous_high
                    and second_support_is_lowest_defense
                    and no_lower_low_after_second_support_before_entry
                    and 1 <= minutes_since_second_support <= 8
                ):
                    level = min(first_low, second_low)
                    valid_resistance_support_candidates.append(
                        {
                            "level": level,
                            "resistance_bar": previous_high_bar,
                            "break_bar": previous_high_bar,
                            "support_bar": second_support_bar,
                            "conflict_high": previous_high_bar.high,
                            "conflict_close_high": previous_high_bar.close,
                            "minutes_since_retest": minutes_since_second_support,
                            "support_index": second_support_index,
                            "resistance_index": first_support_index,
                            "break_index": shelf_break_index,
                            "pattern_type": "two_support_after_breakup_high_break",
                            "pattern_priority": 1,
                            "first_down_bar": first_support_bar,
                            "previous_high_bar": previous_high_bar,
                        }
                    )

        if valid_resistance_support_candidates:
            # v22: when more than one valid internal resistance/support structure
            # exists, prefer the most recent completed support retest.  This fixes
            # HKIT 10:10 export/selection: the old 09:55 -> 10:04 structure is
            # still valid, but the later 10:03 -> 10:07 structure is the actual
            # setup that produces the 10:10 buyer-control break.
            #
            # Tie-breakers prefer the more recent resistance and breakout, so the
            # chosen context is the structure closest to the entry bar rather than
            # the first old structure found in the movement.
            best_candidate = max(
                valid_resistance_support_candidates,
                key=lambda candidate: (
                    candidate.get("pattern_priority", 0),
                    candidate.get("conflict_high", 0.0),
                    candidate["support_index"],
                    candidate["resistance_index"],
                    candidate["break_index"],
                ),
            )

            resistance_support_found = True
            best_level = best_candidate["level"]
            best_resistance_bar = best_candidate["resistance_bar"]
            best_break_bar = best_candidate["break_bar"]
            best_support_bar = best_candidate["support_bar"]
            best_conflict_high = best_candidate["conflict_high"]
            best_conflict_close_high = best_candidate["conflict_close_high"]
            best_minutes_since_retest = best_candidate["minutes_since_retest"]

        if not resistance_support_found:
            return False

        # Store the actual validated structure.  This is intentionally separate
        # from the boolean match so research exports can show the exact
        # resistance/support/control sequence used by the detector.
        self._last_behavioral_buyer_control_phase_20pct_30min_entry_context = {
            "anchor_bar": best_anchor_bar,
            "resistance_bar": best_resistance_bar,
            "break_bar": best_break_bar,
            "support_bar": best_support_bar,
            "resistance_price": best_level,
            "conflict_high": best_conflict_high,
            "conflict_close_high": best_conflict_close_high,
            "minutes_since_support_retest": best_minutes_since_retest,
            "pattern_type": best_candidate.get("pattern_type"),
            "previous_high_bar": best_candidate.get("previous_high_bar"),
            "first_down_bar": best_candidate.get("first_down_bar"),
        }

        # ------------------------------------------------------------------
        # 3) Secondary behavior score.  These are not the base, but they confirm
        #    the movement is HKIT-like and not just a random level retest.
        # ------------------------------------------------------------------
        behavior_score = 0

        # Most bars before have active volume against volume average.
        previous_volume_ratios = [volume_ratio(bar) for bar in previous_10_bars]
        active_volume_count = true_count([
            value is not None and value >= 1.0
            for value in previous_volume_ratios
        ])
        strong_volume_count = true_count([
            value is not None and value >= 1.4
            for value in previous_volume_ratios
        ])
        if active_volume_count >= 5:
            behavior_score += 3
        elif active_volume_count >= 3:
            behavior_score += 1
        if strong_volume_count >= 3:
            behavior_score += 1

        # Both EMAs keep going up in previous bars.
        ema9_rising_count = true_count([
            phase_bars[index].ema_9 >= phase_bars[index - 1].ema_9
            for index in range(1, len(phase_bars))
        ])
        ema20_rising_count = true_count([
            phase_bars[index].ema_20 >= phase_bars[index - 1].ema_20
            for index in range(1, len(phase_bars))
        ])
        if ema9_rising_count >= max(3, int((len(phase_bars) - 1) * 0.60)):
            behavior_score += 2
        if ema20_rising_count >= max(3, int((len(phase_bars) - 1) * 0.55)):
            behavior_score += 2

        # EMA9 starts getting far from EMA20 and VWAP.
        early_phase = phase_bars[:max(3, len(phase_bars) // 3)]
        late_phase = phase_bars[-max(3, len(phase_bars) // 3):]
        early_ema_gap = average([ema9_ema20_gap(bar) for bar in early_phase])
        late_ema_gap = average([ema9_ema20_gap(bar) for bar in late_phase])
        early_vwap_gap = average([ema9_vwap_gap(bar) for bar in early_phase])
        late_vwap_gap = average([ema9_vwap_gap(bar) for bar in late_phase])
        if early_ema_gap is not None and late_ema_gap is not None and late_ema_gap > early_ema_gap:
            behavior_score += 3
        if early_vwap_gap is not None and late_vwap_gap is not None and late_vwap_gap > early_vwap_gap:
            behavior_score += 3

        # Many bars from previous bars get a higher high than their previous bar.
        higher_high_count = true_count([
            phase_bars[index].high > phase_bars[index - 1].high
            for index in range(1, len(phase_bars))
        ])
        if higher_high_count >= max(3, int((len(phase_bars) - 1) * 0.45)):
            behavior_score += 3

        # Sellers exist, but buyers defend the price / EMA9 / support.
        seller_presence_count = true_count([
            bar.close < bar.open_value
            or (
                upper_wick_share(bar) is not None
                and upper_wick_share(bar) >= 0.25
            )
            for bar in before_current_phase_bars
        ])
        ema9_defense_count = true_count([
            bar.ema_9 > 0
            and bar.low <= bar.ema_9 * 1.035
            and bar.close >= bar.ema_9
            for bar in before_current_phase_bars
        ])
        if seller_presence_count >= 1 and ema9_defense_count >= 1:
            behavior_score += 3

        # MACD histogram changes direction / re-accelerates near the entry.
        histogram_values = [
            histogram_value(bar)
            for bar in bars_until_current[max(0, current_index - 6):current_index + 1]
            if histogram_value(bar) is not None
        ]
        macd_turns_back_up = False
        if len(histogram_values) >= 4:
            current_hist = histogram_values[-1]
            previous_hist = histogram_values[-2]
            prior_histograms = histogram_values[:-1]
            had_pause = any(
                prior_histograms[index] <= prior_histograms[index - 1]
                for index in range(1, len(prior_histograms))
            )
            macd_turns_back_up = current_hist > 0 and current_hist > previous_hist and had_pause
            if macd_turns_back_up:
                behavior_score += 3

        # Current bar confirms the defended level with a constructive hold or
        # re-break.  It does not need to be an oversized power candle.
        if current_cp >= 0.70:
            behavior_score += 1
        if current_bar.close >= previous_bar.high or current_bar.high >= max(bar.high for bar in previous_5_bars):
            behavior_score += 2
        if best_level is not None and current_bar.low >= best_level * 0.97:
            behavior_score += 1

        # v7: trend-row profile after the resistance->support/EMA9 base.
        #
        # The v6 output was useful as a trend-base, but still too broad.  This
        # version keeps the base exactly as requested:
        # movement start -> internal resistance -> pullback toward EMA9 ->
        # old resistance/EMA9 defended -> close above EMA9.
        #
        # Then it requires the stronger "trend is being walked up" behavior:
        # active previous volume, both EMAs rising, EMA9 separating away from
        # EMA20/VWAP, many higher highs, sellers appearing but being defended,
        # and a fresh MACD/re-break continuation.
        phase_step_count = max(1, len(phase_bars) - 1)

        current_volume_ratio = volume_ratio(current_bar)
        previous_5_volume_ratios = [volume_ratio(bar) for bar in previous_5_bars]
        previous_10_bars = bars_until_current[max(0, current_index - 10):current_index]
        previous_10_volume_ratios = [volume_ratio(bar) for bar in previous_10_bars]
        previous_5_active_volume_count = true_count([
            value is not None and value >= 1.0
            for value in previous_5_volume_ratios
        ])
        previous_5_strong_volume_count = true_count([
            value is not None and value >= 1.4
            for value in previous_5_volume_ratios
        ])
        previous_10_active_volume_count = true_count([
            value is not None and value >= 1.0
            for value in previous_10_volume_ratios
        ])
        previous_10_strong_volume_count = true_count([
            value is not None and value >= 1.4
            for value in previous_10_volume_ratios
        ])

        previous_5_ranges = [range_pct(bar) for bar in previous_5_bars]
        previous_5_average_range = average(previous_5_ranges)
        previous_5_max_range = max(
            [value for value in previous_5_ranges if value is not None],
            default=None,
        )

        current_ema9_ema20_gap = ema9_ema20_gap(current_bar)
        current_ema9_vwap_gap = ema9_vwap_gap(current_bar)

        # v10: stronger buyer-arrival volume profile.
        # The v9 output was cleaner, but still included many rows where the
        # entry was only a decent trend continuation.  For the +20% target we
        # want the current bar to show fresh participation while the prior tape
        # was already active.  This encodes: most previous bars already had
        # high volume versus their average, and the current bar is still
        # clearly active, not a quiet drift bar.
        active_volume_ok = (
            previous_5_active_volume_count >= 4
            and previous_5_strong_volume_count >= 3
            and previous_10_active_volume_count >= 7
            and previous_10_strong_volume_count >= 4
            and current_volume_ratio is not None
            and current_volume_ratio >= 2.4
        )

        previous_tape_is_volatile_ok = (
            previous_5_average_range is not None
            and previous_5_max_range is not None
            and (
                previous_5_average_range >= 0.035
                or previous_5_max_range >= 0.075
            )
        )

        ema_rising_ok = (
            ema9_rising_count >= max(4, int(phase_step_count * 0.65))
            and ema20_rising_count >= max(4, int(phase_step_count * 0.60))
        )

        ema_expansion_ok = (
            early_ema_gap is not None
            and late_ema_gap is not None
            and late_ema_gap > early_ema_gap
            and early_vwap_gap is not None
            and late_vwap_gap is not None
            and late_vwap_gap > early_vwap_gap
            and current_ema9_ema20_gap is not None
            and current_ema9_ema20_gap > 0.025
            and current_ema9_vwap_gap is not None
            and current_bar.ema_9 > current_bar.ema_20
            and current_bar.ema_9 > current_bar.vwap
        )

        higher_highs_ok = higher_high_count >= max(4, int(phase_step_count * 0.48))

        sellers_defended_ok = (
            seller_presence_count >= 1
            and ema9_defense_count >= 1
            and current_bar.close >= current_bar.ema_9
            and (best_level is None or current_bar.close >= best_level * 0.99)
        )

        fresh_reacceleration_ok = (
            macd_turns_back_up
            or current_bar.close >= previous_bar.high
            or current_bar.high >= max(bar.high for bar in previous_5_bars)
        )

        # v9: current candle should show buyer expansion vs the previous bar.
        # This implements the behavior: close-open on the current bar is bigger
        # than the previous bar, so the entry is a fresh demand expansion and
        # not just another passive trend-row.
        current_real_body = current_bar.close - current_bar.open_value
        previous_real_body = previous_bar.close - previous_bar.open_value
        previous_abs_body = abs(previous_real_body)

        current_body_expands_vs_previous_ok = (
            current_real_body > 0
            and current_real_body > previous_abs_body
        )

        previous_3_abs_bodies = [
            abs(bar.close - bar.open_value)
            for bar in previous_3_bars
            if safe(bar.open_value, 0.0) > 0
        ]
        previous_3_average_abs_body = average(previous_3_abs_bodies)
        current_body_expands_vs_recent_tape_ok = (
            previous_3_average_abs_body is not None
            and current_real_body > previous_3_average_abs_body
        )

        # The current demand bar should expand in both price action and volume.
        # This avoids passive rows that are inside the trend but do not show a
        # new buyer decision point.
        current_volume_expands_vs_previous_ok = current_bar.volume > previous_bar.volume

        clean_current_bar_ok = (
            current_cp >= 0.72
            and current_uw <= 0.34
            and current_bar.close >= current_bar.open_value
            and current_volume_expands_vs_previous_ok
            and (
                current_body_expands_vs_previous_ok
                or current_body_expands_vs_recent_tape_ok
            )
        )

        # Avoid trend rows that are already too extended far above EMA9.  The
        # HKIT-style bars are strong, but the best continuation entries still
        # have EMA9/support close enough to matter as defense.
        close_to_ema9 = None
        if safe(current_bar.ema_9, 0.0) > 0:
            close_to_ema9 = (current_bar.close - current_bar.ema_9) / current_bar.ema_9

        not_too_far_from_ema9_ok = close_to_ema9 is not None and close_to_ema9 <= 0.22

        # v25: after the resistance/support or double-down defense is proven,
        # the actual entry bar should show that buyers took control by closing
        # meaningfully above EMA9. This keeps HKIT 10:05 / 10:10 and NEXR
        # 10:17, but removes many weak continuation rows that barely separate
        # from EMA9 before rolling back.
        current_close_has_control_above_ema9_ok = (
            close_to_ema9 is not None
            and close_to_ema9 >= 0.12
        )

        # v8: VWAP / volume-average wake-up behavior.
        # The idea is not an exact number; it is a phase-change:
        # before the move VWAP / volume average are relatively quiet, then in
        # the latest bars they start lifting because buyers are coming in.
        def pct_change(first_value: float, last_value: float) -> float | None:
            if first_value is None or first_value <= 0 or last_value is None:
                return None
            return (last_value - first_value) / first_value

        pre_wakeup_bars = bars_until_current[max(0, current_index - 30):max(0, current_index - 10)]
        recent_wakeup_bars = bars_until_current[max(0, current_index - 10):current_index + 1]

        vwap_wakes_up_ok = False
        volume_average_wakes_up_ok = False
        if len(pre_wakeup_bars) >= 5 and len(recent_wakeup_bars) >= 5:
            prior_vwap_move = pct_change(pre_wakeup_bars[0].vwap, pre_wakeup_bars[-1].vwap)
            recent_vwap_move = pct_change(recent_wakeup_bars[0].vwap, recent_wakeup_bars[-1].vwap)
            prior_volume_average_move = pct_change(pre_wakeup_bars[0].volume_average, pre_wakeup_bars[-1].volume_average)
            recent_volume_average_move = pct_change(recent_wakeup_bars[0].volume_average, recent_wakeup_bars[-1].volume_average)

            if prior_vwap_move is not None and recent_vwap_move is not None:
                vwap_wakes_up_ok = (
                    recent_vwap_move > 0
                    and recent_vwap_move > abs(prior_vwap_move) * 1.35
                )

            if prior_volume_average_move is not None and recent_volume_average_move is not None:
                volume_average_wakes_up_ok = (
                    recent_volume_average_move > 0
                    and recent_volume_average_move > abs(prior_volume_average_move) * 1.25
                )

        buyer_arrival_wakeup_ok = vwap_wakes_up_ok or volume_average_wakes_up_ok

        # v11: keep only the high-velocity buyer-arrival branch.
        # The v10 output finally had a good row count, but the remaining
        # failures were often merely good continuation/retest candles without
        # enough recent price progress or enough current buyer participation
        # for a 20% / 30-minute target.  This adds the behavior you are
        # describing: the tape was already walking up, EMA9 was separated,
        # and the current bar shows a fresh demand expansion with unusually
        # active volume.
        previous_5_progress_pct = None
        if previous_5_bars and safe(previous_5_bars[0].close, 0.0) > 0:
            previous_5_progress_pct = (previous_bar.close - previous_5_bars[0].close) / previous_5_bars[0].close

        previous_10_progress_pct = None
        if previous_10_bars and safe(previous_10_bars[0].close, 0.0) > 0:
            previous_10_progress_pct = (previous_bar.close - previous_10_bars[0].close) / previous_10_bars[0].close

        recent_walkup_progress_ok = (
            (previous_5_progress_pct is not None and previous_5_progress_pct >= 0.10)
            or (previous_10_progress_pct is not None and previous_10_progress_pct >= 0.14)
        )

        current_volume_is_exceptional_ok = (
            current_volume_ratio is not None
            and current_volume_ratio >= 4.0
        )

        current_ema9_is_meaningfully_separated_ok = (
            current_ema9_ema20_gap is not None
            and current_ema9_ema20_gap >= 0.055
        )

        high_velocity_buyer_arrival_ok = (
            current_volume_is_exceptional_ok
            and recent_walkup_progress_ok
            and current_ema9_is_meaningfully_separated_ok
        )

        # v13: completed-retest HKIT-regression branch.
        # Do NOT require exceptional current volume here.  In the anchor example
        # HKIT 10:05 / 10:10, the important behavior is not a single insane
        # volume bar. It is: movement already started, previous resistance became
        # support near EMA9, previous tape had active volume, EMA9/EMA20/VWAP
        # expansion is visible, many prior bars made higher highs, and MACD
        # histogram turns back up / re-accelerates on the entry bar.
        previous_20_bars = bars_until_current[max(0, current_index - 20):current_index]
        previous_20_progress_pct = None
        if previous_20_bars and safe(previous_20_bars[0].close, 0.0) > 0:
            previous_20_progress_pct = (previous_bar.close - previous_20_bars[0].close) / previous_20_bars[0].close

        previous_20_active_volume_count = true_count([
            volume_ratio(bar) is not None and volume_ratio(bar) >= 1.0
            for bar in previous_20_bars
        ])
        previous_20_higher_high_count = sum(
            1
            for left_bar, right_bar in zip(previous_20_bars, previous_20_bars[1:])
            if right_bar.high > left_bar.high
        )

        hkit_regression_archetype_ok = (
            # prior tape already walked up materially from the movement start
            (
                (previous_10_progress_pct is not None and previous_10_progress_pct >= 0.12)
                or (previous_20_progress_pct is not None and previous_20_progress_pct >= 0.30)
            )
            # many previous bars had active volume versus their own average
            and previous_10_active_volume_count >= 7
            and previous_20_active_volume_count >= 12
            # EMA structure is not just bullish; it is expanding
            and ema_rising_ok
            and ema_expansion_ok
            and current_ema9_ema20_gap is not None
            and current_ema9_ema20_gap >= 0.05
            and current_ema9_vwap_gap is not None
            and current_ema9_vwap_gap > 0
            # many bars before are making higher highs / price walking up
            and (higher_highs_ok or previous_20_higher_high_count >= 10)
            # sellers exist, but buyers defend EMA9 / support
            and sellers_defended_ok
            # this is the entry behavior you pointed out at HKIT 10:05 / 10:10
            and macd_turns_back_up
            and current_cp >= 0.72
            and current_uw <= 0.35
            and current_bar.close >= current_bar.ema_9
            and current_bar.close >= previous_bar.open_value
            # avoid passive tiny bars; demand should expand vs previous body/recent tape
            and (current_body_expands_vs_previous_ok or current_body_expands_vs_recent_tape_ok)
            # current volume should still be active, but not necessarily exceptional
            and current_volume_ratio is not None
            and current_volume_ratio >= 1.20
            and not_too_far_from_ema9_ok
            and behavior_score >= 13
        )

        # v24: real participation filter.
        #
        # AKAN 2026-05-21 exposed a weakness: it had high volume ratios only
        # because its volume average was tiny, but the actual share participation
        # was very weak compared with validated examples like HKIT and NEXR.
        # For this pattern we need real buyers participating, not only a ratio
        # spike over a small baseline.
        previous_5_average_share_volume = average([
            safe(bar.volume, None)
            for bar in previous_5_bars
        ])
        previous_10_average_share_volume = average([
            safe(bar.volume, None)
            for bar in previous_10_bars
        ])

        current_real_volume_participation_ok = (
            safe(current_bar.volume, 0.0) >= 250000
            or (
                safe(current_bar.volume, 0.0) >= 150000
                and previous_5_average_share_volume is not None
                and previous_5_average_share_volume >= 100000
                and previous_10_average_share_volume is not None
                and previous_10_average_share_volume >= 85000
            )
        )

        # v28: the WOK-style branches were still too broad.  They should
        # represent the actual buyer-control bar after the support structure,
        # not every late-trend continuation row.  Require the bar to expand as
        # a real green body and to separate from EMA9 enough that buyers have
        # visibly taken control.
        current_body_pct_of_open = None
        if safe(current_bar.open_value, 0.0) > 0:
            current_body_pct_of_open = (current_bar.close - current_bar.open_value) / current_bar.open_value

        wok_late_current_control_bar_ok = (
            current_cp >= 0.60
            and current_uw <= 0.45
            and current_bar.close > current_bar.open_value
            and current_bar.close >= current_bar.ema_9
            and close_to_ema9 is not None
            and close_to_ema9 >= 0.08
            and current_body_pct_of_open is not None
            and current_body_pct_of_open >= 0.08
            and current_volume_ratio is not None
            and current_volume_ratio >= 0.85
            and (
                current_body_expands_vs_previous_ok
                or current_body_expands_vs_recent_tape_ok
                or current_bar.close >= previous_bar.high
                or current_bar.high >= max(bar.high for bar in previous_5_bars)
            )
        )

        wok_late_support_control_pattern_ok = (
            best_candidate.get("pattern_type") in {
                "multi_touch_resistance_support_control_break",
                "two_support_after_breakup_high_break",
            }
            and current_real_volume_participation_ok
            and wok_late_current_control_bar_ok
            and previous_tape_is_volatile_ok
            and fresh_reacceleration_ok
        )

        return (
            resistance_support_found
            and current_real_volume_participation_ok
            and (
                (
                    current_close_has_control_above_ema9_ok
                    and previous_tape_is_volatile_ok
                    and fresh_reacceleration_ok
                    and clean_current_bar_ok
                    and buyer_arrival_wakeup_ok
                    and (
                        (
                            active_volume_ok
                            and ema_rising_ok
                            and ema_expansion_ok
                            and higher_highs_ok
                            and sellers_defended_ok
                            and not_too_far_from_ema9_ok
                            and high_velocity_buyer_arrival_ok
                            and behavior_score >= 15
                        )
                        or hkit_regression_archetype_ok
                    )
                )
                or wok_late_support_control_pattern_ok
            )
        )


    def get_last_behavioral_buyer_control_phase_20pct_30min_entry_context(self) -> dict | None:
        return getattr(
            self,
            "_last_behavioral_buyer_control_phase_20pct_30min_entry_context",
            None,
        )

    def get_behavioral_buyer_control_phase_20pct_30min_entry_family(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> str | None:
        if self._matches_behavioral_buyer_control_phase_20pct_30min_entry(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        ):
            return "resistance_support_or_double_down_ema9_trend_quality_v28_wok_body_ema9_control_20pct_30min_entry"
        return None

    def get_buyer_conviction_20pct_30min_entry_family(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> str | None:
        behavioral_family = self.get_behavioral_buyer_control_phase_20pct_30min_entry_family(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )
        if behavioral_family:
            return behavioral_family

        return None

    def is_buyer_conviction_20pct_30min_entry_candidate(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        return self.get_buyer_conviction_20pct_30min_entry_family(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        ) is not None

    def bar_has_potential(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> tuple[bool, str]:
        """
        Current live signal gate for the 30% experiment.

        Old 20%/50% pattern families were intentionally removed.
        The only active strategy is the 30% trend-shift candidate logic.
        """

        matched_family = self.get_buyer_conviction_20pct_30min_entry_family(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if matched_family:
            return True, matched_family

        return False, "bar has no v26 WOK/HKIT/NEXR support-control 20pct/30min entry potential"

