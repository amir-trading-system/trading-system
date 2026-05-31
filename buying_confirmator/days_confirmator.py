import copy
import datetime
import logging
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
                is_valid_breakout = self._is_valid_breakout(
                    potential_confirmation_bar=next_bar,
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                )
                if not is_valid_breakout:
                    continue

                if self._confirm_bar_for_placing_order(
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
            only_before_current_bar=False,
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

        bar_has_potential, reason = self._bar_has_potential(
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

                msg = "Bar analyzed by AI model"
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

    def _bar_has_potential(
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

        if self._highest_high_occurred_more_than_once_in_the_last_bars(
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

        if not self._is_valid_breakout(
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
        ):
            return False, "bar didnt have valid breakout"

        return True, "bar has potential"

    def _highest_high_occurred_more_than_once_in_the_last_bars(
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

    def _is_valid_breakout(
        self,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_timeframe_stock: common.objects.Stock,
    ) -> bool:
        previous_highest_high_one_minute_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=potential_confirmation_bar,
            only_before_current_bar=True,
        )
        if previous_highest_high_one_minute_bar is None:
            return False

        crossed_previous_highest_high = previous_highest_high_one_minute_bar.high < potential_confirmation_bar.close
        if not crossed_previous_highest_high:
            return False

        previous_highest_high_bar_is_recent = previous_highest_high_one_minute_bar.bar_time > potential_confirmation_bar.bar_time - datetime.timedelta(
            minutes=30,
        )
        if not previous_highest_high_bar_is_recent:
            return False

        lowest_low_bar_since_highest_high = one_minute_timeframe_stock.get_lowest_low_bar_between_bars(
            from_bar=previous_highest_high_one_minute_bar,
            to_bar=potential_confirmation_bar,
        )
        if lowest_low_bar_since_highest_high is None:
            return False

        lowest_low_became_support_or_previous_resistance = False
        for bar_object in one_minute_timeframe_stock.bars:
            if bar_object.bar_time >= previous_highest_high_one_minute_bar.bar_time:
                continue

            if bar_object.bar_time < lowest_low_bar_since_highest_high.bar_time - datetime.timedelta(
                minutes=30,
            ):
                continue

            highest_high_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
                current_one_minute_bar=bar_object,
                only_before_current_bar=True,
            )

            if (
                True
                and highest_high_bar is not None
                and 0.97 <= highest_high_bar.high/lowest_low_bar_since_highest_high.low <= 1.03
                and highest_high_bar.close <= lowest_low_bar_since_highest_high.low
                and lowest_low_bar_since_highest_high.bar_lower_wick_percentage >= 0.2
                and highest_high_bar.bar_wick_percentage >= 0.1
                and highest_high_bar.above_volume_average
                and highest_high_bar.ema_9 > highest_high_bar.vwap
                and highest_high_bar.ema_9 > highest_high_bar.ema_20
                and highest_high_bar.high > highest_high_bar.ema_9
            ):
                lowest_low_became_support_or_previous_resistance = True
                break

        return lowest_low_became_support_or_previous_resistance

    def _confirm_bar_for_placing_order(
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
