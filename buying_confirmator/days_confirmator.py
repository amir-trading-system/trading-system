import copy
import datetime
import logging
import math
import statistics
import queue

import alerter
import analyzer.evidences
import common
import model
from tws import client


class Confirmator:
    def __init__(
        self,
        is_retro: bool,
        should_run_model: bool,
        tws_client: client.Client,
        logger: logging.Logger,
        request_id_to_symbol: dict[int,common.objects.Stock],
        results_queue: queue.Queue[dict[str,any]],
        alerter_object: alerter.alerter.Alerter = None,
    ):
        self.tws_client = tws_client
        self.is_retro = is_retro
        self.logger = logger
        self.alerter_object = alerter_object
        self.results_queue = results_queue
        self.request_id_to_symbol = request_id_to_symbol
        self.model_runner = model.runner.Runner(
            should_run_model=should_run_model,
        )
        self.data_extractor = model.data_extractor.DataExtractor()

    def confirm_entry_position(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        milestones: common.objects.Milestones,
    ):
        one_minute_bars: list[common.objects.BarData] = []
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        already_sent_buy_order_for_stock: dict[str,bool] = {}
        stock.bars = sorted(
            stock.bars,
            key=lambda bar_object: bar_object.bar_time,
            reverse=True,
        )
        next_bar = None
        bar_has_confirmed = False
        confirmation_bar = None
        score: common.objects.Score = None
        previous_highest_high = 0.0
        one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]

        while True:
            next_bar = stock.one_minute_bars_queue.get()
            if next_bar.low < 1:
                continue

            stock.one_minute_bars_queue.task_done()
            date_now = datetime.datetime.now()

            if bar_has_confirmed:
                if self.confirm_bar_for_placing_order(
                    day_timeframe_stock=stock,
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                    original_bar_to_confirm=original_bar_to_confirm,
                    potential_confirmation_bar=confirmation_bar,
                    current_bar=next_bar,
                    previous_highest_high=previous_highest_high,
                    score=score,
                    already_sent_buy_order_for_stock=already_sent_buy_order_for_stock,
                ):
                    bar_has_confirmed = False
                    score = None

                continue

            if (
                True
                and self.is_retro
                and next_bar.bar_time > datetime.datetime(
                    year=next_bar.bar_time.year,
                    month=next_bar.bar_time.month,
                    day=next_bar.bar_time.day,
                    hour=16,
                )
            ):
                self.results_queue.put(
                    {
                        "symbol": stock.symbol_name,
                        "original_bar_time": original_bar_to_confirm.bar_time,
                        "confirmation_bar_time": None,
                        "bar_to_place_order_time": None,
                        "price_movement_statistics": {},
                        "score": 0,
                    },
                )
                return

            if (
                next_bar.bar_time < datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
                or next_bar.bar_time < most_updated_datetime
                or not next_bar.ready_to_analyze
                or not next_bar.histogram
                or (
                    not self.is_retro
                    and next_bar.bar_time < datetime.datetime(
                        year=date_now.year,
                        month=date_now.month,
                        day=date_now.day,
                        hour=date_now.hour,
                        minute=date_now.minute-1 if date_now.minute > 0 else 59,
                    )
                )
            ):
                continue

            self.logger.info(
                msg="Starting to confirm one minute bar for entry point",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": next_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                    "high": next_bar.high,
                    "low": next_bar.low,
                    "open": next_bar.open_value,
                    "close": next_bar.close,
                    "collection_finished_time": next_bar.collection_finished_time,
                },
            )

            score, previous_highest_high = self._confirm(
                stock=stock,
                milestones=milestones,
                one_minute_bars=one_minute_bars,
                potential_confirmation_bar=next_bar,
                original_bar_to_confirm=original_bar_to_confirm,
            )

            if score.should_take_trade:
                bar_has_confirmed = True
                confirmation_bar = copy.deepcopy(next_bar)
                continue

            most_updated_datetime = next_bar.bar_time
            self.logger.info(
                msg="Entry point does not confirmed yet, waiting for next one",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": next_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                },
            )

    def _confirm(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        one_minute_bars: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
    ) -> tuple[common.objects.Score, float]:
        entry_position_bar: common.objects.BarData = None
        one_minute_bars.append(potential_confirmation_bar)
        confirmed_evidence: str = ""
        score = common.objects.Score(
            score=0.0,
            probability=0.0,
            threshold=0.0,
            should_take_trade=False,
        )

        one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]
        highest_high_one_minute_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=potential_confirmation_bar,
        )

        stock.volume_sum_since_4_am_today = one_minute_timeframe_stock.get_volume_sum_since_04_am_today(
            current_one_minute_bar=potential_confirmation_bar,
        )
        stock.volume_sum_since_market_open = one_minute_timeframe_stock.get_volume_sum_since_market_open(
            current_one_minute_bar=potential_confirmation_bar,
        )

        temp_one_minute_bars = sorted(
            [
                one_minute_bar
                for one_minute_bar in one_minute_bars
                if one_minute_bar.bar_time <= potential_confirmation_bar.bar_time
            ],
            key=lambda bar_object: bar_object.bar_time,
            reverse=True
        )

        highest_high: float = highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else potential_confirmation_bar.close

        bar_has_potential, reason = self.bar_has_potential(
            stock=stock,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=temp_one_minute_bars,
            highest_high=highest_high,
        )

        if not bar_has_potential:
            self.logger.info(
                msg="Bar does not have a potential",
                extra={
                    "worker": "Confirmator",
                    "symbol": stock.symbol_name,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "request_id": stock.request_id,
                    "reason": reason,
                }
            )
            return (
                score,
                highest_high,
            )

        stock_is_valid_for_evidence = False

        for evidence in analyzer.evidences.__evidences__:
            evidence_obj = evidence(
                logger=self.logger,
                stock=stock,
            )
            if (
                not stock_is_valid_for_evidence
                and not evidence_obj.relevant_bars
            ):
                break

            stock_is_valid_for_evidence = True
            if not evidence_obj.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=original_bar_to_confirm,
                is_retro=self.is_retro,
            ):
                continue

            one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]

            if not evidence_obj.confirm(
                stock=stock,
                original_bar_to_confirm=original_bar_to_confirm,
                potential_confirmation_bar=potential_confirmation_bar,
                milestones=milestones,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                one_minute_bars=temp_one_minute_bars,
            ):
                continue

            has_valid_breakout = self.has_valid_breakout(
                potential_confirmation_bar=potential_confirmation_bar,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
            )

            if not has_valid_breakout:
                continue

            self.logger.info(
                msg="Potential confirmation bar has passed static confirmation, waiting for model confirmation",
                extra={
                    "worker": "Confirmator",
                    "symbol": stock.symbol_name,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "evidence_name": evidence_obj.name,
                    "request_id": stock.request_id,
                },
            )

            potential_confirmation_bar.price_movement_statistics = self.data_extractor.extract_features_from_symbol_data(
                day_timeframe_stock=stock,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=potential_confirmation_bar,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                one_minute_bars=one_minute_bars,
            )

            total_volume = potential_confirmation_bar.price_movement_statistics.get("total_volume")
            positive_tier = potential_confirmation_bar.price_movement_statistics.get("positive_tier")
            positive_group_score = potential_confirmation_bar.price_movement_statistics.get("positive_group_score")
            positive_group_reasons = potential_confirmation_bar.price_movement_statistics.get("positive_group_reasons")
            positive_score = potential_confirmation_bar.price_movement_statistics.get("positive_score")
            strong_positive_group_score = potential_confirmation_bar.price_movement_statistics.get("strong_positive_group_score")
            strong_positive_group_reasons = potential_confirmation_bar.price_movement_statistics.get("strong_positive_group_reasons")
            soft_positive_group_score = potential_confirmation_bar.price_movement_statistics.get("soft_positive_group_score")
            soft_positive_group_reasons = potential_confirmation_bar.price_movement_statistics.get("soft_positive_group_reasons")

            if (
                True
                and total_volume is not None
            ):
                if (
                    total_volume < 200000
                    or potential_confirmation_bar.volume < 15000
                ):
                    return (
                        score,
                        highest_high_one_minute_bar.high,
                    )

            if self.model_runner.should_run_model:
                score = self.model_runner.score_potential_confirmation_bar(
                    potential_confirmation_bar=potential_confirmation_bar,
                    day_timeframe_stock=stock,
                )
                stock.number_of_potential_entry_points += 1

                msg = "Bar confirmed by model"

                if not score.should_take_trade:
                    most_of_body_above_highest_high = (
                        True
                        and highest_high_one_minute_bar is not None
                        and potential_confirmation_bar.close - highest_high_one_minute_bar.high > highest_high_one_minute_bar.high - potential_confirmation_bar.open_value
                    )

                    if most_of_body_above_highest_high:
                        msg = "Bar got denied by model but has positive family tag, so bar confirmed"
                        entry_position_bar = potential_confirmation_bar
                        confirmed_evidence = evidence_obj.name
                        score.should_take_trade = True
                    else:
                        msg = "Bar confirmed by static confirmation, but got denied on model confirmation"
                else:
                    entry_position_bar = potential_confirmation_bar
                    confirmed_evidence = evidence_obj.name

                self.logger.info(
                    msg=msg,
                    extra={
                        "worker": "Confirmator",
                        "symbol": stock.symbol_name,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "entry_position_bar_time": potential_confirmation_bar.bar_time,
                        "highest_high": highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else 0,
                        "highest_high_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else 0,
                        "evidence_name": evidence_obj.name,
                        "request_id": stock.request_id,
                        "score": score.score,
                        "probability": score.probability,
                        "threshold": score.threshold,
                        "current_day_ema_9": original_bar_to_confirm.ema_9,
                        "current_day_ema_20": original_bar_to_confirm.ema_20,
                        "current_day_vwap": original_bar_to_confirm.vwap,
                        "positive_tier": positive_tier,
                        "positive_group_score": positive_group_score,
                        "positive_group_reasons": positive_group_reasons,
                        "positive_score": positive_score,
                        "strong_positive_group_score": strong_positive_group_score,
                        "strong_positive_group_reasons": strong_positive_group_reasons,
                        "soft_positive_group_score": soft_positive_group_score,
                        "soft_positive_group_reasons": soft_positive_group_reasons,
                    },
                )

                break

            else:
                score.should_take_trade = True

        if entry_position_bar is not None:
            self.logger.info(
                "Bar has confirmed, waiting for volume confirmation for placing order",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": entry_position_bar.bar_time,
                    "highest_high": highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else 0,
                    "highest_high_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else 0,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "evidence_name": confirmed_evidence,
                    "request_id": stock.request_id,
                    "score": score.score,
                },
            )

            if self.alerter_object:
                self.alerter_object.send_confirmation_alert(
                    sender="Confirmator",
                    stock=stock,
                    original_bar=original_bar_to_confirm,
                    entry_position_bar=entry_position_bar,
                    highest_high_one_minute_bar=highest_high_one_minute_bar,
                    evidence_name=confirmed_evidence,
                    is_retro=self.is_retro,
                    request_id=stock.request_id,
                )

        return (
            score,
            highest_high_one_minute_bar.high,
        )

    def bar_has_potential(
        self,
        stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        highest_high: float,
    ) -> tuple[bool, str]:
        if stock.number_of_potential_entry_points >= 2 and potential_confirmation_bar.close > highest_high:
            return True, "number_of_potential_entry_points >= 2"

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=potential_confirmation_bar,
        )

        if (
            True
            and previous_bar is not None
            and previous_bar.high > potential_confirmation_bar.high
        ):
            return False, "previous_bar.high <= potential_confirmation_bar.high"

        if potential_confirmation_bar.close - potential_confirmation_bar.open_value < 0.03:
            return False, "bar body is less than 0.03"

        highest_high = round(highest_high, 2)
        if potential_confirmation_bar.close < 1.0:
            return False, "potential_confirmation_bar.close >= 1.0"

        crossed_any_resistance = any(
            r_l
            for r_l in stock.resistance_levels
            if potential_confirmation_bar.low < r_l.high < potential_confirmation_bar.close
        )
        crossed_highest_high = round(potential_confirmation_bar.low, 2) < highest_high < round(potential_confirmation_bar.close, 2)

        if not crossed_highest_high:
            return False, "Didnt crossed highest high"

        if (
            True
            and potential_confirmation_bar.low - potential_confirmation_bar.ema_9 > potential_confirmation_bar.close - potential_confirmation_bar.low
            and not crossed_any_resistance
            and not crossed_highest_high
        ):
            return False, "Didnt crossed highest high"

        if highest_high >= potential_confirmation_bar.close:
            return False, "highest_high < potential_confirmation_bar.close"

        if self.highest_high_occurred_more_than_once_in_the_last_bars(
            stock=stock,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=one_minute_bars,
        ):
            return False, "highest_high_occurred_more_than_once_in_the_last_bars"

        if potential_confirmation_bar.buyers_are_indecision:
            return False, "buyers_are_indecision"

        if any(
            r_l
            for r_l in stock.resistance_levels
            if r_l.high > potential_confirmation_bar.high
            and potential_confirmation_bar.high/r_l.high > 0.9
            and potential_confirmation_bar.bar_wick_percentage > 0.4
        ):
            return False, "close to resistance level"

        if (
            True
            and len(stock.bars) > 1
            and (
                stock.bars[1].close > potential_confirmation_bar.high
                or 0.9 < potential_confirmation_bar.high/stock.bars[1].high <= 1
            )
        ):
            return False, "previous day close is higher"

        if potential_confirmation_bar.bar_time < datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=9,
            minute=40,
        ):
            return False, "Before 09:40"

        if potential_confirmation_bar.bar_time > datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=15,
            minute=20,
        ):
            return False, "After 15:20"

        return True, "bar has potential"

    def highest_high_occurred_more_than_once_in_the_last_bars(
        self,
        stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        if len(one_minute_bars) < 3:
            return False

        current_bar_is_highest_high = max(
            bar_object.high
            for bar_object in one_minute_bars
        ) == potential_confirmation_bar.high

        previous_bar_was_highest_high = max(
            bar_object.high
            for bar_object in one_minute_bars[2:]
        )/one_minute_bars[1].high < 0.95

        current_bar_crossed_stock_highest_high = potential_confirmation_bar.low < stock.last_post_pre_one_minute_highest_high < potential_confirmation_bar.close

        return current_bar_is_highest_high and previous_bar_was_highest_high and not current_bar_crossed_stock_highest_high

    def has_valid_breakout(
        self,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_timeframe_stock: common.objects.Stock
    ) -> bool:
        bars_until_now = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if bar_object.bar_time.date() == potential_confirmation_bar.bar_time.date()
            and bar_object.index > potential_confirmation_bar.index
        ]
        recent_bars = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if bar_object.bar_time.date() == potential_confirmation_bar.bar_time.date()
            and bar_object.index - 10 <= potential_confirmation_bar.index
        ]

        resistance_zones = self.find_meaningful_resistance_zones(
            bars_until_now=bars_until_now,
            min_prior_bars=8,
            min_touches=1,
            min_rejections=1,
            lookback_bars=90,
        )

        if not resistance_zones:
            return False

        candidate_zones = [
            zone
            for zone in resistance_zones
            if self.safe_float(potential_confirmation_bar.high, 0.0) > zone.zone_high
        ]

        if not candidate_zones:
            return False

        # Use the highest broken resistance, so one candle does not create
        # duplicate rows for every lower old resistance.
        selected_zone = sorted(
            candidate_zones,
            key=lambda zone: zone.resistance_price,
            reverse=True,
        )[0]

        is_valid, valid_reason = self.is_valid_breakout_bar(
            bar_object=potential_confirmation_bar,
            resistance_zone=selected_zone,
            recent_bars=recent_bars,
        )

        log_message = "breakout is invalid, waiting for another bar"
        if is_valid:
            log_message = "breakout is valid"

        self.logger.info(
            msg=log_message,
            extra={
                "worker": "Confirmator",
                "symbol": potential_confirmation_bar.symbol,
                "timeframe": potential_confirmation_bar.timeframe,
                "timeframe_type": potential_confirmation_bar.timeframe_type.value,
                "entry_position_bar_time": potential_confirmation_bar.bar_time,
                "bar_time": potential_confirmation_bar.bar_time,
                "request_id": one_minute_timeframe_stock.request_id,
                "valid_reason": valid_reason,
            },
        )

        return is_valid

    def find_meaningful_resistance_zones(
        self,
        bars_until_now: list[common.objects.BarData],
        min_prior_bars: int = 8,
        min_touches: int = 1,
        min_rejections: int = 1,
        lookback_bars: int = 90,
    ) -> list[common.objects.ResistanceZone]:
        """
        Finds meaningful prior resistance zones before the current breakout candidate.

        Meaningful resistance:
        - local swing high
        - caused rejection
        - optionally repeated touches around same zone
        """

        if len(bars_until_now) < min_prior_bars:
            return []

        bars = bars_until_now[-lookback_bars:]

        candidate_levels: list[float] = []

        for i in range(1, len(bars) - 1):
            prev_bar = bars[i - 1]
            bar_object = bars[i]
            next_bar = bars[i + 1]

            high = self.safe_float(bar_object.high, 0.0)

            is_local_swing_high = (
                high >= self.safe_float(prev_bar.high, 0.0)
                and high >= self.safe_float(next_bar.high, 0.0)
            )

            rejected, _, _ = self.bar_rejected_from_level(
                bars=bars,
                touch_index=i,
                level=high,
                lookahead_bars=5,
                min_rejection_pct=0.018,
            )

            if is_local_swing_high and rejected:
                candidate_levels.append(high)

        # Also include the highest high so far if it caused rejection.
        highest_bar_index = max(
            range(len(bars)),
            key=lambda idx: self.safe_float(bars[idx].high, 0.0),
        )

        highest_high = self.safe_float(bars[highest_bar_index].high, 0.0)

        rejected, _, _ = self.bar_rejected_from_level(
            bars=bars,
            touch_index=highest_bar_index,
            level=highest_high,
            lookahead_bars=8,
            min_rejection_pct=0.018,
        )

        if rejected:
            candidate_levels.append(highest_high)

        zones: list[common.objects.ResistanceZone] = []

        for level in candidate_levels:
            tolerance = self.calculate_dynamic_zone_tolerance(
                price=level,
                recent_bars=bars,
            )

            zone_low = level - tolerance
            zone_high = level + tolerance

            touches: list[common.objects.BarData] = []
            rejection_count = 0
            max_rejection_pct = 0.0
            max_rejection_abs = 0.0

            for i, bar_object in enumerate(bars):
                high = self.safe_float(bar_object.high, 0.0)
                close = self.safe_float(bar_object.close, 0.0)

                touched_zone = (
                    zone_low <= high <= zone_high
                    or zone_low <= close <= zone_high
                    or high > zone_high and close < zone_high
                )

                if not touched_zone:
                    continue

                rejected, rejection_pct, rejection_abs = self.bar_rejected_from_level(
                    bars=bars,
                    touch_index=i,
                    level=level,
                    lookahead_bars=5,
                    min_rejection_pct=0.012,
                )

                touches.append(bar_object)

                if rejected:
                    rejection_count += 1
                    max_rejection_pct = max(max_rejection_pct, rejection_pct)
                    max_rejection_abs = max(max_rejection_abs, rejection_abs)

            if len(touches) < min_touches:
                continue

            if rejection_count < min_rejections:
                continue

            zones.append(
                common.objects.ResistanceZone(
                    resistance_price=level,
                    zone_low=zone_low,
                    zone_high=zone_high,
                    first_touch_time=touches[0].bar_time,
                    last_touch_time=touches[-1].bar_time,
                    touch_count=len(touches),
                    rejection_count=rejection_count,
                    max_rejection_pct=max_rejection_pct,
                    max_rejection_abs=max_rejection_abs,
                    source="swing_high_with_rejection",
                )
            )

        zones = sorted(
            zones,
            key=lambda zone: zone.resistance_price,
        )

        deduped: list[common.objects.ResistanceZone] = []

        for zone in zones:
            if not deduped:
                deduped.append(zone)
                continue

            previous = deduped[-1]
            zones_overlap = zone.zone_low <= previous.zone_high

            if zones_overlap:
                previous_score = (
                    previous.touch_count * 1.0
                    + previous.rejection_count * 2.0
                    + previous.max_rejection_pct * 100.0
                )

                current_score = (
                    zone.touch_count * 1.0
                    + zone.rejection_count * 2.0
                    + zone.max_rejection_pct * 100.0
                )

                if current_score > previous_score:
                    deduped[-1] = zone
            else:
                deduped.append(zone)

        return deduped

    def safe_float(
        self,
        value: any,
        default: float,
    ) -> float:
        try:
            if value is None:
                return default

            float_value = float(value)

            if math.isnan(float_value):
                return default

            return float_value

        except Exception:
            return default

    def bar_rejected_from_level(
        self,
        bars: list[common.objects.BarData],
        touch_index: int,
        level: float,
        lookahead_bars: int = 5,
        min_rejection_pct: float = 0.018,
    ) -> tuple[bool, float, float]:
        """
        Checks whether price touched a level and then rejected from it.

        Returns:
            rejected
            rejection_pct
            rejection_abs
        """

        if touch_index >= len(bars):
            return False, 0.0, 0.0

        touch_bar = bars[touch_index]
        touch_high = self.safe_float(touch_bar.high, 0.0)

        future_bars = bars[touch_index + 1: touch_index + 1 + lookahead_bars]

        if not future_bars:
            return False, 0.0, 0.0

        min_future_low = min(
            self.safe_float(bar_object.low, touch_high)
            for bar_object in future_bars
        )

        rejection_abs = max(0.0, touch_high - min_future_low)
        rejection_pct = rejection_abs / level if level > 0 else 0.0

        return rejection_pct >= min_rejection_pct, rejection_pct, rejection_abs

    def calculate_dynamic_zone_tolerance(
        self,
        price: float,
        recent_bars: list[common.objects.BarData],
    ) -> float:
        """
        Resistance should be a zone, not one exact price.

        This gives larger tolerance when the stock is volatile,
        but still keeps the zone tight enough for low-priced stocks.
        """

        recent_ranges = [
            self.get_bar_range(bar_object)
            for bar_object in recent_bars[-20:]
            if self.safe_float(bar_object.high, 0.0) > self.safe_float(bar_object.low, 0.0)
        ]

        median_range = statistics.median(recent_ranges) if recent_ranges else price * 0.005

        return max(
            0.01,
            price * 0.004,
            median_range * 0.25,
        )

    def get_bar_range(
        self,
        bar_object: common.objects.BarData,
    ) -> float:
        high = self.safe_float(bar_object.high, 0.0)
        low = self.safe_float(bar_object.low, 0.0)

        return max(0.000001, high - low)

    def is_valid_breakout_bar(
        self,
        bar_object: common.objects.BarData,
        resistance_zone: common.objects.ResistanceZone,
        recent_bars: list[common.objects.BarData],
    ) -> tuple[bool, str]:
        """
        Valid breakout means:
        - high breaks above zone
        - close confirms above zone
        - volume confirms
        - candle is not mostly upper wick
        - close is strong inside candle range
        """

        open_value = self.safe_float(bar_object.open_value, 0.0)
        high = self.safe_float(bar_object.high, 0.0)
        close = self.safe_float(bar_object.close, 0.0)

        volume_ratio = self.get_volume_ratio(bar_object)
        candle_stats = self.get_candle_stats(bar_object)

        zone_high = resistance_zone.zone_high
        zone_width = resistance_zone.zone_high - resistance_zone.zone_low

        min_close_above = max(
            0.005,
            close * 0.0015,
            zone_width * 0.25,
        )

        high_above_zone = high > zone_high + min_close_above
        close_above_zone = close > zone_high + min_close_above

        if not high_above_zone:
            return False, "high_did_not_clear_zone"

        if not close_above_zone:
            return False, "high_broke_zone_but_close_did_not_confirm"

        if close <= open_value:
            return False, "red_breakout_candle"

        if volume_ratio < 1.5:
            return False, "volume_ratio_too_low"

        if candle_stats["close_position_in_range"] < 0.60:
            return False, "close_not_strong_enough_in_range"

        if candle_stats["upper_wick_pct_of_range"] > 0.45:
            return False, "upper_wick_too_large"

        # This marks very late/extended moves as not "clean structure breakouts".
        # If this filters out too many good positive examples, loosen or remove it.
        last_5 = recent_bars[-5:]

        if len(last_5) >= 5:
            green_count = sum(
                1
                for b in last_5
                if self.safe_float(b.close, 0.0) > self.safe_float(b.open_value, 0.0)
            )

            move_from_5_bars_ago = self.pct_change(
                self.safe_float(last_5[0].close, close),
                close,
            )

            if green_count >= 5 and move_from_5_bars_ago > 0.25:
                return False, "too_extended_after_5_green_bars"

        return True, "valid_breakout_confirmed"

    def pct_change(
        self,
        from_value: float,
        to_value: float,
    ) -> float:
        if from_value == 0:
            return 0.0

        return (to_value - from_value) / from_value

    def get_candle_stats(
        self,
        bar_object: common.objects.BarData,
    ) -> dict[str, float]:
        open_value = self.safe_float(bar_object.open_value, 0.0)
        high = self.safe_float(bar_object.high, 0.0)
        low = self.safe_float(bar_object.low, 0.0)
        close = self.safe_float(bar_object.close, 0.0)

        bar_range = max(0.000001, high - low)
        body = abs(close - open_value)
        upper_wick = high - max(open_value, close)
        lower_wick = min(open_value, close) - low

        return {
            "body_pct_of_range": body / bar_range,
            "upper_wick_pct_of_range": max(0.0, upper_wick / bar_range),
            "lower_wick_pct_of_range": max(0.0, lower_wick / bar_range),
            "close_position_in_range": (close - low) / bar_range,
        }

    def get_volume_ratio(
        self,
        bar_object: common.objects.BarData,
    ) -> float:
        volume = self.safe_float(bar_object.volume, 0.0)
        volume_average = self.safe_float(bar_object.volume_average, 0.0)

        if volume_average <= 0:
            return 0.0

        return volume / volume_average

    def confirm_bar_for_placing_order(
        self,
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        current_bar: common.objects.BarData,
        previous_highest_high: float,
        score: common.objects.Score,
        already_sent_buy_order_for_stock: dict[str,bool] = {}
    ) -> bool:
        order_has_been_placed = False
        transmit = False

        if current_bar.close < previous_highest_high:
            return True

        relevant_bars = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if potential_confirmation_bar.bar_time < bar_object.bar_time <= current_bar.bar_time
        ]
        if not relevant_bars:
            return order_has_been_placed

        if any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close < previous_highest_high
            and bar_object.close < bar_object.ema_20
            and bar_object.volume > bar_object.volume_average
        ):
            # meaning that this trend is not relevant anymore - not a real trend.
            return True

        lowest_bar_since_now_from_relevant_bars = None
        lowest_low = 100.0
        for bar_object in relevant_bars:
            if bar_object.low < lowest_low:
                lowest_bar_since_now_from_relevant_bars = bar_object
                lowest_low = bar_object.low

        previous_crossed_resistance_became_to_support_level = (
            True
            and lowest_bar_since_now_from_relevant_bars is not None
            and (
                previous_highest_high/lowest_low >= 0.95
                or potential_confirmation_bar.high/lowest_low >= 0.95
            )
            and not any(
                bar_object
                for bar_object in relevant_bars
                if bar_object.close < previous_highest_high
                and bar_object.close < bar_object.ema_20
            )
        )

        there_was_any_retracement_movement = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.histogram < 0
        )

        current_bar_is_highest = max(
            bar_object.high
            for bar_object in relevant_bars
        ) == current_bar.high

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=current_bar,
        )
        distance_from_ema_9 = current_bar.low - current_bar.ema_9

        validation_for_placing_order = (
            True
            and current_bar.is_positive
            and current_bar.volume > current_bar.volume_average
            and current_bar.close > current_bar.ema_20
            and current_bar.ema_9 > current_bar.ema_20
            and previous_crossed_resistance_became_to_support_level
            and there_was_any_retracement_movement
            and current_bar_is_highest
            and current_bar.high - current_bar.low > distance_from_ema_9
            and previous_bar is not None
            and current_bar.volume > previous_bar.volume
            and current_bar.macd > 0
            and current_bar.body_percentage > 0.4
            and previous_bar.histogram < current_bar.histogram
        )

        if validation_for_placing_order:
            if not any(
                    bar_object
                    for bar_object in relevant_bars
                    if not bar_object.is_positive
            ) and current_bar.index + 1 < potential_confirmation_bar.index:
                # meaning there is no pullback basically
                return True

            unique_key_for_place_order = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key_for_place_order = f"{original_bar_to_confirm.symbol}-{day_timeframe_stock.specific_bar_time}"
            if (
                not already_sent_buy_order_for_stock.get(unique_key_for_place_order, False)
            ):
                already_sent_buy_order_for_stock[unique_key_for_place_order] = True

                if not self.is_retro:
                    self.tws_client.place_buy_order(
                        symbol=original_bar_to_confirm.symbol,
                        price=current_bar.close,
                        transmit=transmit,
                        score=score,
                    )
                order_has_been_placed = True

                self.results_queue.put(
                    {
                        "symbol": day_timeframe_stock.symbol_name,
                        "original_bar_time": original_bar_to_confirm.bar_time,
                        "confirmation_bar_time": potential_confirmation_bar.bar_time,
                        "bar_to_place_order_time": current_bar.bar_time,
                        "price_movement_statistics": potential_confirmation_bar.price_movement_statistics,
                        "score": score.score if score is not None else 0,
                    },
                )

                self.logger.info(
                    "Bar has confirmed by model and order has been placed",
                    extra={
                        "worker": "Confirmator",
                        "symbol": original_bar_to_confirm.symbol,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                        "entry_position_bar_time": current_bar.bar_time,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "request_id": one_minute_timeframe_stock.request_id,
                        "score": score.score,
                    },
                )

        return order_has_been_placed
