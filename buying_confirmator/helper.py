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

    def _get_candle_close_position_in_range(
        self,
        bar_object: common.objects.BarData,
    ) -> float:
        candle_range = bar_object.high - bar_object.low

        if candle_range <= 0:
            return 0.0

        return (bar_object.close - bar_object.low) / candle_range


    def _get_upper_wick_pct_of_range(
        self,
        bar_object: common.objects.BarData,
    ) -> float:
        candle_range = bar_object.high - bar_object.low

        if candle_range <= 0:
            return 0.0

        return (
            bar_object.high - max(
                bar_object.open_value,
                bar_object.close,
            )
        ) / candle_range

    def _bar_has_good_breakout_candle_quality(
        self,
        bar_object: common.objects.BarData,
    ) -> bool:
        if bar_object.close <= bar_object.open_value:
            return False

        close_position_in_range = self._get_candle_close_position_in_range(
            bar_object=bar_object,
        )

        if close_position_in_range < 0.80:
            return False

        upper_wick_pct = self._get_upper_wick_pct_of_range(
            bar_object=bar_object,
        )

        if upper_wick_pct > 0.20:
            return False

        return True

    def _find_live_resistance_breakout_context(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        lookback_minutes: int = 30,
        min_pullback_from_resistance_pct: float = 0.05,
        min_breakout_close_above_resistance_pct: float = 0.04,
    ) -> dict | None:
        """
        Finds the best live-safe resistance context before the current bar.

        This does NOT look into the future.

        It tries to find:
        - prior resistance in the last 30 minutes
        - price pulled back at least 5% from it
        - no prior close above that resistance before current bar
        - current bar closes at least 4% above resistance
        """

        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if len(bars_before_current) < 3:
            return None

        lookback_start_time = potential_confirmation_bar.bar_time - datetime.timedelta(
            minutes=lookback_minutes,
        )

        lookback_bars = [
            bar_object
            for bar_object in bars_before_current
            if lookback_start_time <= bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        if len(lookback_bars) < 3:
            return None

        best_context = None
        best_score = None

        for resistance_bar in lookback_bars[:-1]:
            resistance_price = self._safe_float(
                resistance_bar.high,
                None,
            )

            if resistance_price is None or resistance_price <= 0:
                continue

            bars_after_resistance = [
                bar_object
                for bar_object in lookback_bars
                if bar_object.bar_time > resistance_bar.bar_time
            ]

            if not bars_after_resistance:
                continue

            lowest_low_bar_since_resistance = min(
                bars_after_resistance,
                key=lambda bar_object: bar_object.low,
            )

            pullback_from_resistance_pct = (
                resistance_price - lowest_low_bar_since_resistance.low
            ) / resistance_price

            if pullback_from_resistance_pct < min_pullback_from_resistance_pct:
                continue

            # Very important: if price already closed above this resistance
            # before the current bar, then current bar is not the first real break.
            prior_close_above_resistance = any(
                bar_object.close > resistance_price
                for bar_object in bars_after_resistance
            )

            if prior_close_above_resistance:
                continue

            breakout_close_above_resistance_pct = (
                potential_confirmation_bar.close - resistance_price
            ) / resistance_price

            if breakout_close_above_resistance_pct < min_breakout_close_above_resistance_pct:
                continue

            minutes_since_resistance = (
                potential_confirmation_bar.bar_time - resistance_bar.bar_time
            ).total_seconds() / 60.0

            # Prefer decisive break + real pullback + not too stale.
            score = (
                breakout_close_above_resistance_pct * 100.0
                + pullback_from_resistance_pct * 50.0
                - minutes_since_resistance * 0.02
            )

            if best_score is None or score > best_score:
                best_score = score
                best_context = {
                    "resistance_bar": resistance_bar,
                    "resistance_price": resistance_price,
                    "lowest_low_bar_since_resistance": lowest_low_bar_since_resistance,
                    "pullback_from_resistance_pct": pullback_from_resistance_pct,
                    "breakout_close_above_resistance_pct": breakout_close_above_resistance_pct,
                    "minutes_since_resistance": minutes_since_resistance,
                }

        return best_context

    def _previous_live_breakout_failed_support_low(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        max_prior_breakouts_to_check: int = 1,
        support_low_tolerance_pct: float = 0.003,
    ) -> bool:
        """
        Live-safe.

        Checks whether the previous detected trend-start breakout already failed
        by breaking below its support low before the current bar.

        This uses only bars before current bar.
        """

        bars_until_current = self._get_today_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_bars = [
            bar_object
            for bar_object in bars_until_current
            if bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        prior_contexts: list[dict] = []

        for bar_object in previous_bars:
            # Avoid recursion into previous-failure check.
            context = self._find_live_resistance_breakout_context(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=bar_object,
                lookback_minutes=30,
                min_pullback_from_resistance_pct=0.05,
                min_breakout_close_above_resistance_pct=0.04,
            )

            if context is None:
                continue

            if bar_object.bar_time.time() >= datetime.time(12, 0):
                continue

            if not self._bar_has_good_breakout_candle_quality(
                bar_object=bar_object,
            ):
                continue

            prior_contexts.append(
                {
                    "bar": bar_object,
                    "context": context,
                }
            )

        if not prior_contexts:
            return False

        # Check only the latest prior breakout by default.
        prior_contexts = sorted(
            prior_contexts,
            key=lambda item: item["bar"].bar_time,
        )

        prior_contexts = prior_contexts[-max_prior_breakouts_to_check:]

        for item in prior_contexts:
            prior_breakout_bar = item["bar"]
            prior_context = item["context"]
            support_low_bar = prior_context["lowest_low_bar_since_resistance"]
            support_low = support_low_bar.low

            invalidation_price = support_low * (1 - support_low_tolerance_pct)

            bars_after_prior_breakout_until_current = [
                bar_object
                for bar_object in previous_bars
                if prior_breakout_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
            ]

            broke_support_low = any(
                bar_object.low < invalidation_price
                for bar_object in bars_after_prior_breakout_until_current
            )

            if broke_support_low:
                return True

        return False

    def _count_live_trend_start_breakouts_before_current(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> int:
        """
        Counts prior strong trend-start breakouts before the current bar.
        Live-safe, but can be a little expensive because it rescans prior bars.
        """

        bars_until_current = self._get_today_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_bars = [
            bar_object
            for bar_object in bars_until_current
            if bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        count = 0

        for bar_object in previous_bars:
            if bar_object.bar_time.time() >= datetime.time(12, 0):
                continue

            context = self._find_live_resistance_breakout_context(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=bar_object,
                lookback_minutes=30,
                min_pullback_from_resistance_pct=0.05,
                min_breakout_close_above_resistance_pct=0.04,
            )

            if context is None:
                continue

            if not self._bar_has_good_breakout_candle_quality(
                bar_object=bar_object,
            ):
                continue

            count += 1

        return count


    def _get_pre_bar_max_close_to_vwap_pct(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        lookback_bars: int = 5,
    ) -> float | None:
        """
        Live-safe.

        Calculates the maximum close-to-VWAP percentage in the previous N bars.

        Example:
            0.10 means one of the previous bars closed 10% above VWAP.

        We use this to avoid breakout/trend-start bars where price was already
        too extended above VWAP before the current trigger.
        """

        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_bars = bars_before_current[-lookback_bars:]

        close_to_vwap_values: list[float] = []

        for bar_object in previous_bars:
            close = self._safe_float(
                bar_object.close,
                None,
            )
            vwap = self._safe_float(
                bar_object.vwap,
                None,
            )

            if close is None or vwap is None or vwap <= 0:
                continue

            close_to_vwap_values.append(
                (close - vwap) / vwap
            )

        if not close_to_vwap_values:
            return None

        return max(close_to_vwap_values)

    def _minutes_since_previous_live_trend_start_breakout(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        max_previous_close_to_vwap_pct: float = 0.10,
    ) -> float | None:
        """
        Live-safe.

        Finds the most recent previous strong live trend-start breakout and
        returns how many minutes ago it happened.

        This is used to avoid repeated quick re-pop entries, like cases where
        a second breakout fires only a few minutes after the first one without
        enough time to build a new base/reset.
        """

        bars_until_current = self._get_today_bars_until_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        previous_bars = [
            bar_object
            for bar_object in bars_until_current
            if bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        previous_breakout_times: list[datetime.datetime] = []

        for bar_object in previous_bars:
            if bar_object.bar_time.time() >= datetime.time(12, 0):
                continue

            context = self._find_live_resistance_breakout_context(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=bar_object,
                lookback_minutes=30,
                min_pullback_from_resistance_pct=0.05,
                min_breakout_close_above_resistance_pct=0.04,
            )

            if context is None:
                continue

            if not self._bar_has_good_breakout_candle_quality(
                bar_object=bar_object,
            ):
                continue

            pre_5_bar_max_close_to_vwap_pct = self._get_pre_bar_max_close_to_vwap_pct(
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=bar_object,
                lookback_bars=5,
            )

            if pre_5_bar_max_close_to_vwap_pct is None:
                continue

            if pre_5_bar_max_close_to_vwap_pct > max_previous_close_to_vwap_pct:
                continue

            previous_breakout_times.append(
                bar_object.bar_time,
            )

        if not previous_breakout_times:
            return None

        previous_breakout_time = max(previous_breakout_times)

        return (
            potential_confirmation_bar.bar_time - previous_breakout_time
        ).total_seconds() / 60.0

    def has_good_live_trend_start_context(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        Main live-safe trend-start filter.

        Based on the best profile from the exported data:

        - before noon
        - early in the sequence
        - no previous failed support break
        - current bar decisively closes above resistance
        - resistance had a real pullback before the break
        - strong candle quality
        - previous 5 bars were not too extended above VWAP
        - current bar close is not too extended above VWAP
        """

        # Best profile was before noon.
        if potential_confirmation_bar.bar_time.time() >= datetime.time(12, 0):
            return False

        # Candle quality.
        if not self._bar_has_good_breakout_candle_quality(
            bar_object=potential_confirmation_bar,
        ):
            return False

        context = self._find_live_resistance_breakout_context(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            lookback_minutes=30,
            min_pullback_from_resistance_pct=0.05,
            min_breakout_close_above_resistance_pct=0.04,
        )

        if context is None:
            return False

        # 20% target refinement:
        # The best profile came from setups where the resistance/pullback
        # structure had enough depth and enough time to mature.
        if context["pullback_from_resistance_pct"] < 0.08:
            return False

        if context["minutes_since_resistance"] < 10:
            return False

        # Strong volume confirmation.
        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if not bars_before_current:
            return False

        previous_bar = bars_before_current[-1]

        if previous_bar.volume <= 0:
            return False

        volume_vs_previous_bar_ratio = (
            potential_confirmation_bar.volume / previous_bar.volume
        )

        if volume_vs_previous_bar_ratio < 1.8:
            return False

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        if volume_vs_average_ratio < 1.8:
            return False

        # Early sequence filter.
        clean_breakout_count_today_before_current = self._count_live_trend_start_breakouts_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        # Strong helper profile from the export was best with:
        # clean_breakout_count_today_before_current <= 3.
        # This allows only the first 4 trend-start setups of the day:
        # 0 = first, 1 = second, 2 = third, 3 = fourth.
        if clean_breakout_count_today_before_current > 3:
            return False

        previous_clean_breakout_failed_support_low = self._previous_live_breakout_failed_support_low(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if previous_clean_breakout_failed_support_low:
            return False

        # Stronger version: avoid triggers where the stock was already too
        # extended above VWAP in the previous 5 bars.
        # From the profile, <= 10% was the cleanest version.
        pre_5_bar_max_close_to_vwap_pct = self._get_pre_bar_max_close_to_vwap_pct(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            lookback_bars=5,
        )

        if pre_5_bar_max_close_to_vwap_pct is None:
            return False

        if pre_5_bar_max_close_to_vwap_pct > 0.10:
            return False

        # 20% target refinement:
        # Avoid trigger candles that close too far above VWAP.
        # The profile showed <= 18% was the best balance.
        current_vwap = self._safe_float(
            potential_confirmation_bar.vwap,
            None,
        )

        current_close = self._safe_float(
            potential_confirmation_bar.close,
            None,
        )

        if current_vwap is None or current_vwap <= 0:
            return False

        if current_close is None:
            return False

        current_close_to_vwap_pct = (
            current_close - current_vwap
        ) / current_vwap

        if current_close_to_vwap_pct > 0.18:
            return False

        return True

    def is_secondary_base_ignition_breakout(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        Detects RYOJ 11:57-style secondary base ignition.

        Pattern:
        - Not necessarily early/open-only.
        - Stock has already built above VWAP.
        - Previous 20-30 bars show base/rebuild.
        - Price holds above EMA 9 and VWAP.
        - Lows are mostly flat/rising.
        - Current bar breaks recent base resistance decisively.
        - Volume expands strongly.
        - Candle closes near high.

        This is different from the strict helper trend-start pattern because
        this setup may be far above VWAP by the trigger bar.
        """

        # Still avoid late-day lower-quality setups for now.
        # RYOJ was 11:57, right before noon.
        if potential_confirmation_bar.bar_time.time() >= datetime.time(12, 30):
            return False

        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if len(bars_before_current) < 30:
            return False

        previous_bar = bars_before_current[-1]

        # Use a 30-minute build window.
        build_window_bars = [
            bar_object
            for bar_object in bars_before_current
            if bar_object.bar_time >= potential_confirmation_bar.bar_time - datetime.timedelta(minutes=30)
        ]

        if len(build_window_bars) < 20:
            return False

        last_10_bars = build_window_bars[-10:]
        last_20_bars = build_window_bars[-20:]

        # --------------------------------------------------
        # 1. The base should already be above VWAP / EMA 9.
        # --------------------------------------------------
        close_above_vwap_count_10 = sum(
            1
            for bar_object in last_10_bars
            if bar_object.close > bar_object.vwap
        )

        if close_above_vwap_count_10 < 8:
            return False

        close_above_ema9_count_10 = sum(
            1
            for bar_object in last_10_bars
            if bar_object.close > bar_object.ema_9
        )

        if close_above_ema9_count_10 < 8:
            return False

        # --------------------------------------------------
        # 2. Base/rebuild: the lows should mostly hold.
        # --------------------------------------------------
        higher_or_flat_low_count = 0

        for index in range(1, len(last_10_bars)):
            previous_low = last_10_bars[index - 1].low
            current_low = last_10_bars[index].low

            # Allow tiny undercuts, but not real breakdowns.
            if current_low >= previous_low * 0.985:
                higher_or_flat_low_count += 1

        if higher_or_flat_low_count < 7:
            return False

        # --------------------------------------------------
        # 3. The base should have actual upward/rebuild progress.
        # --------------------------------------------------
        first_close_20 = last_20_bars[0].close
        last_close_before_current = last_20_bars[-1].close

        if first_close_20 <= 0:
            return False

        pre_20_bar_gain_pct = (
            last_close_before_current - first_close_20
        ) / first_close_20

        # RYOJ had a meaningful rebuild before 11:57.
        if pre_20_bar_gain_pct < 0.06:
            return False

        # --------------------------------------------------
        # 4. Recent base resistance.
        # --------------------------------------------------
        resistance_bar = max(
            last_20_bars,
            key=lambda bar_object: bar_object.high,
        )

        resistance_price = resistance_bar.high

        if resistance_price <= 0:
            return False

        breakout_close_above_resistance_pct = (
            potential_confirmation_bar.close - resistance_price
        ) / resistance_price

        # RYOJ 11:57 was very decisive: ~14%.
        # Use 8% minimum so it catches more than only extreme cases.
        if breakout_close_above_resistance_pct < 0.08:
            return False

        # Do not allow if the current bar is not actually making a strong new
        # break above the prior base.
        if potential_confirmation_bar.close <= resistance_price:
            return False

        # --------------------------------------------------
        # 5. Current bar volume ignition.
        # --------------------------------------------------
        if previous_bar.volume <= 0:
            return False

        volume_vs_previous_bar_ratio = (
            potential_confirmation_bar.volume / previous_bar.volume
        )

        if volume_vs_previous_bar_ratio < 2.5:
            return False

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        if volume_vs_average_ratio < 5.0:
            return False

        pre_5_bar_max_close_to_vwap_pct = self._get_pre_bar_max_close_to_vwap_pct(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            lookback_bars=5,
        )

        if pre_5_bar_max_close_to_vwap_pct is None:
            return False

        if pre_5_bar_max_close_to_vwap_pct > 0.20:
            return False

        # --------------------------------------------------
        # 6. Candle quality.
        # --------------------------------------------------
        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False

        candle_range = potential_confirmation_bar.high - potential_confirmation_bar.low

        if candle_range <= 0:
            return False

        close_position_in_range = (
            potential_confirmation_bar.close - potential_confirmation_bar.low
        ) / candle_range

        if close_position_in_range < 0.85:
            return False

        upper_wick_pct = (
            potential_confirmation_bar.high
            - max(
                potential_confirmation_bar.open_value,
                potential_confirmation_bar.close,
            )
        ) / candle_range

        if upper_wick_pct > 0.15:
            return False

        # --------------------------------------------------
        # 7. Momentum alignment at ignition.
        # --------------------------------------------------
        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_9:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_20:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.vwap:
            return False

        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.ema_20:
            return False

        # For this secondary ignition pattern, we DO NOT cap current close vs VWAP.
        # RYOJ 11:57 was ~30% above VWAP and still correct.
        return True

    def is_market_open_premarket_support_reclaim_ignition(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        """
        Detects MASK 09:30-style pattern.

        Pattern:
        - Premarket runner already proved demand.
        - Pullback into open holds above VWAP.
        - Volume dries up before open.
        - Opening bar retests pullback support.
        - Opening bar reclaims EMA 9 / EMA 20.
        - Opening bar closes strong with volume shock.

        This is different from secondary_base_ignition_breakout.
        It is specifically for the market-open transition.
        """

        # This pattern is specifically for the opening bar / first few minutes.
        if not (
            datetime.time(9, 30)
            <= potential_confirmation_bar.bar_time.time()
            <= datetime.time(9, 35)
        ):
            return False

        bars_before_current = self._get_bars_before_current(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if len(bars_before_current) < 30:
            return False

        previous_bar = bars_before_current[-1]

        premarket_bars = [
            bar_object
            for bar_object in bars_before_current
            if datetime.time(4, 0) <= bar_object.bar_time.time() < datetime.time(9, 30)
        ]

        if len(premarket_bars) < 20:
            return False

        # --------------------------------------------------
        # 1. Premarket had real ignition/demand.
        # --------------------------------------------------
        premarket_ignition_bars = [
            bar_object
            for bar_object in premarket_bars
            if (
                bar_object.volume_average > 0
                and bar_object.volume / bar_object.volume_average >= 4.0
                and bar_object.close > bar_object.open_value
                and bar_object.close > bar_object.vwap
                and bar_object.close > bar_object.ema_9
            )
        ]

        if not premarket_ignition_bars:
            return False

        # --------------------------------------------------
        # 2. Premarket high and controlled pullback.
        # --------------------------------------------------
        premarket_high_bar = max(
            premarket_bars,
            key=lambda bar_object: bar_object.high,
        )

        premarket_high = premarket_high_bar.high

        if premarket_high <= 0:
            return False

        recent_preopen_bars = [
            bar_object
            for bar_object in premarket_bars
            if (
                potential_confirmation_bar.bar_time - datetime.timedelta(minutes=15)
                <= bar_object.bar_time
                < potential_confirmation_bar.bar_time
            )
        ]

        if len(recent_preopen_bars) < 8:
            return False

        preopen_support_low_bar = min(
            recent_preopen_bars,
            key=lambda bar_object: bar_object.low,
        )

        preopen_support_low = preopen_support_low_bar.low

        if preopen_support_low <= 0:
            return False

        pullback_from_premarket_high_pct = (
            premarket_high - preopen_support_low
        ) / premarket_high

        # MASK pulled back ~13% from 6.10 to 5.30.
        if pullback_from_premarket_high_pct < 0.08:
            return False

        # Avoid completely destroyed pullbacks.
        if pullback_from_premarket_high_pct > 0.30:
            return False

        # --------------------------------------------------
        # 3. Pullback stayed structurally above VWAP.
        # --------------------------------------------------
        preopen_close_above_vwap_count = sum(
            1
            for bar_object in recent_preopen_bars
            if bar_object.close > bar_object.vwap
        )

        if preopen_close_above_vwap_count < len(recent_preopen_bars) * 0.70:
            return False

        # --------------------------------------------------
        # 4. Short-term pullback below EMA 9 happened.
        # This confirms it was a reset, not already chasing.
        # --------------------------------------------------
        last_5_preopen_bars = recent_preopen_bars[-5:]

        last_5_close_below_ema9_count = sum(
            1
            for bar_object in last_5_preopen_bars
            if bar_object.close < bar_object.ema_9
        )

        if last_5_close_below_ema9_count < 3:
            return False

        # --------------------------------------------------
        # 5. Volume dried up before open.
        # --------------------------------------------------
        preopen_volume_ratios = [
            bar_object.volume / bar_object.volume_average
            for bar_object in last_5_preopen_bars
            if bar_object.volume_average > 0
        ]

        if len(preopen_volume_ratios) < 3:
            return False

        preopen_avg_volume_ratio = (
            sum(preopen_volume_ratios) / len(preopen_volume_ratios)
        )

        # MASK last-5 preopen average was ~0.22x.
        if preopen_avg_volume_ratio > 0.60:
            return False

        # --------------------------------------------------
        # 6. Opening bar retests the support shelf.
        # --------------------------------------------------
        # MASK 09:30 low was 5.31, support was 5.30.
        if potential_confirmation_bar.low > preopen_support_low * 1.02:
            return False

        # Avoid deep support break.
        if potential_confirmation_bar.low < preopen_support_low * 0.985:
            return False

        # The MASK-style pattern is specifically a support-shelf retest,
        # not just a one-bar pullback. Require several recent pre-open lows
        # to cluster near the same support area.
        support_retest_count = sum(
            1
            for bar_object in recent_preopen_bars
            if abs(bar_object.low - preopen_support_low) / preopen_support_low <= 0.01
        )

        if support_retest_count < 3:
            return False

        # --------------------------------------------------
        # 7. Opening bar reclaims EMA 9 / EMA 20 / VWAP.
        # --------------------------------------------------
        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_9:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.ema_20:
            return False

        if potential_confirmation_bar.close <= potential_confirmation_bar.vwap:
            return False

        if potential_confirmation_bar.ema_9 <= potential_confirmation_bar.ema_20:
            return False

        # --------------------------------------------------
        # 8. Opening bar breaks recent micro resistance.
        # --------------------------------------------------
        recent_micro_resistance_bar = max(
            last_5_preopen_bars,
            key=lambda bar_object: bar_object.high,
        )

        recent_micro_resistance = recent_micro_resistance_bar.high

        if recent_micro_resistance <= 0:
            return False

        breakout_close_above_micro_resistance_pct = (
            potential_confirmation_bar.close - recent_micro_resistance
        ) / recent_micro_resistance

        # MASK was only ~0.8% above last-5 high, so keep this low.
        # This pattern is more about reclaim/support than huge resistance break.
        if breakout_close_above_micro_resistance_pct < 0.005:
            return False

        # --------------------------------------------------
        # 9. Volume shock at the open.
        # --------------------------------------------------
        if previous_bar.volume <= 0:
            return False

        volume_vs_previous_bar_ratio = (
            potential_confirmation_bar.volume / previous_bar.volume
        )

        if volume_vs_previous_bar_ratio < 5.0:
            return False

        if potential_confirmation_bar.volume_average <= 0:
            return False

        volume_vs_average_ratio = (
            potential_confirmation_bar.volume / potential_confirmation_bar.volume_average
        )

        if volume_vs_average_ratio < 1.5:
            return False

        # --------------------------------------------------
        # 10. Candle quality.
        # --------------------------------------------------
        if potential_confirmation_bar.close <= potential_confirmation_bar.open_value:
            return False

        candle_range = potential_confirmation_bar.high - potential_confirmation_bar.low

        if candle_range <= 0:
            return False

        close_position_in_range = (
            potential_confirmation_bar.close - potential_confirmation_bar.low
        ) / candle_range

        if close_position_in_range < 0.85:
            return False

        upper_wick_pct = (
            potential_confirmation_bar.high
            - max(
                potential_confirmation_bar.open_value,
                potential_confirmation_bar.close,
            )
        ) / candle_range

        if upper_wick_pct > 0.15:
            return False

        return True

    def bar_has_potential(
        self,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        has_good_live_trend_start_context = self.has_good_live_trend_start_context(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        has_secondary_base_ignition = self.is_secondary_base_ignition_breakout(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        has_market_open_premarket_support_reclaim_ignition = self.is_market_open_premarket_support_reclaim_ignition(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        if not (
            has_good_live_trend_start_context
            or has_secondary_base_ignition
            or has_market_open_premarket_support_reclaim_ignition
        ):
            return False

        return True
