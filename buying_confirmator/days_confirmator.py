import datetime
import logging
import queue

import alerter
import common
import model
from tws import client
from . import helper


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
        self.helper = helper.Helper()

    def confirm_entry_position(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
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

        while True:
            next_bar = stock.one_minute_bars_queue.get()

            stock.one_minute_bars_queue.task_done()
            date_now = datetime.datetime.now()

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

            if self._confirm(
                stock=stock,
                one_minute_bars=one_minute_bars,
                potential_confirmation_bar=next_bar,
                original_bar_to_confirm=original_bar_to_confirm,
                already_sent_buy_order_for_stock=already_sent_buy_order_for_stock,
            ):
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
        one_minute_bars: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
        already_sent_buy_order_for_stock: dict[str,bool],
    ) -> bool:
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

        bar_has_potential, reason, case_details = self.helper.bar_has_potential(
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=potential_confirmation_bar,
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
                    "case_details": case_details,
                }
            )
            return False

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
                return False

        if self.model_runner.should_run_model:
            score = self.model_runner.score_potential_confirmation_bar(
                potential_confirmation_bar=potential_confirmation_bar,
                day_timeframe_stock=stock,
            )

            entry_position_bar = potential_confirmation_bar

            self.logger.info(
                msg="Bar analyzed by AI model",
                extra={
                    "worker": "Confirmator",
                    "symbol": stock.symbol_name,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "highest_high": highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else 0,
                    "highest_high_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else 0,
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
                    "reason": reason,
                },
            )
        else:
            score.should_take_trade = True

        if entry_position_bar is not None:
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

            unique_key_for_place_order = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key_for_place_order = f"{stock.symbol_name}-{stock.specific_bar_time}"
            if (
                not already_sent_buy_order_for_stock.get(unique_key_for_place_order, False)
            ):
                already_sent_buy_order_for_stock[unique_key_for_place_order] = True

                if not self.is_retro:
                    self.tws_client.place_buy_order(
                        symbol=original_bar_to_confirm.symbol,
                        price=potential_confirmation_bar.close,
                        transmit=False,
                        score=score,
                    )

                self.results_queue.put(
                    {
                        "symbol": potential_confirmation_bar.symbol,
                        "original_bar_time": original_bar_to_confirm.bar_time,
                        "confirmation_bar_time": potential_confirmation_bar.bar_time,
                        "bar_to_place_order_time": potential_confirmation_bar.bar_time,
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
                        "entry_position_bar_time": potential_confirmation_bar.bar_time,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "request_id": one_minute_timeframe_stock.request_id,
                        "score": score.score,
                    },
                )

            return True

        return False

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
