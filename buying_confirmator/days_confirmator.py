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
        confirmation_only: bool = False,
    ):
        self.tws_client = tws_client
        self.is_retro = is_retro
        self.logger = logger
        self.alerter_object = alerter_object
        self.results_queue = results_queue
        self.request_id_to_symbol = request_id_to_symbol
        self.confirmation_only = confirmation_only
        self.model_runner = model.runner.Runner(
            should_run_model=should_run_model,
        )

    def _confirm(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        one_minute_bars: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        already_sent_buy_order_for_stock: dict[str,bool],
    ) -> bool:
        bar_has_confirmed: bool = False
        entry_position_bar: common.objects.BarData = None
        one_minute_bars.append(potential_confirmation_bar)

        if (
            True
            and self.is_retro
            and potential_confirmation_bar.bar_time.hour == 19
            and potential_confirmation_bar.bar_time.minute == 59
        ):
            self.results_queue.put(
                {
                    "symbol": stock.symbol_name,
                    "original_bar_time": original_bar_to_confirm.bar_time,
                    "confirmation_bar_time": None,
                    "evidences": [],
                    "volume_until_now": stock.volume_sum_since_4_am_today,
                    "price_movement_statistics": {},
                },
            )
            return False

        today_09_30 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=9,
            minute=30,
        )
        today_10_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=10,
            minute=00,
        )
        today_12_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=12,
            minute=00,
        )
        volume_sum_since_market_open = sum(
            one_minute_bar.volume
            for one_minute_bar in one_minute_bars
            if today_09_30 <= one_minute_bar.bar_time < potential_confirmation_bar.bar_time
        )

        should_wait_for_next_bar = (
            potential_confirmation_bar.bar_time < today_09_30
            or potential_confirmation_bar.volume < 20000
            or volume_sum_since_market_open < 100000
            or (
                today_10_00 <= potential_confirmation_bar.bar_time <= today_12_00
                and volume_sum_since_market_open < 500000
            )
            or (
                potential_confirmation_bar.bar_time > today_12_00
                and volume_sum_since_market_open < 1000000
            )
        )

        bar_is_strong_than_before = (
            True
            and potential_confirmation_bar.bar_up_percentage >= 0.03
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
        )

        if should_wait_for_next_bar and not bar_is_strong_than_before:
            return bar_has_confirmed

        confirmed_evidences: list[str] = []
        stock_is_valid_for_evidence = False
        for evidence in analyzer.evidences.__evidences__:
            evidence_obj = evidence(
                logger=self.logger,
            )
            if (
                not stock_is_valid_for_evidence
                and not evidence_obj.pre_process(
                    stock=stock,
                    current_bar=original_bar_to_confirm,
                )
            ):
                break

            stock_is_valid_for_evidence = True
            if not self.confirmation_only:
                if not evidence_obj.find_evidence(
                    stock=stock,
                    milestones=milestones,
                    current_bar=original_bar_to_confirm,
                    is_retro=self.is_retro,
                ):
                    continue

            temp_one_minute_bars = sorted(
                [
                    one_minute_bar
                    for one_minute_bar in one_minute_bars
                    if one_minute_bar.bar_time <= potential_confirmation_bar.bar_time
                ],
                key=lambda bar_object: bar_object.bar_time,
                reverse=True
            )

            one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]

            if evidence_obj.confirm(
                stock=stock,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                original_bar_to_confirm=original_bar_to_confirm,
                potential_confirmation_bar=potential_confirmation_bar,
                milestones=milestones,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                one_minute_bars=temp_one_minute_bars,
                volume_sum_since_market_open=volume_sum_since_market_open,
                model_runner=self.model_runner,
            ):
                entry_position_bar = potential_confirmation_bar
                confirmed_evidences.append(evidence.name)

        if confirmed_evidences:
            self.results_queue.put(
                {
                    "symbol": stock.symbol_name,
                    "original_bar_time": original_bar_to_confirm.bar_time,
                    "confirmation_bar_time": entry_position_bar.bar_time,
                    "evidences": confirmed_evidences,
                    "volume_until_now": stock.volume_sum_since_4_am_today,
                    "price_movement_statistics": entry_position_bar.price_movement_statistics,
                },
            )

        for evidence_name in confirmed_evidences:
            self.logger.info(
                "Bar has confirmed",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": entry_position_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "evidence_name": evidence_name,
                    "request_id": stock.request_id,
                },
            )

            transmit = False
            if self.alerter_object:
                ## For now keping it false until we think how to manage it.
                # transmit = True

                self.alerter_object.send_confirmation_alert(
                    sender="Confirmator",
                    stock=stock,
                    original_bar=original_bar_to_confirm,
                    entry_position_bar=entry_position_bar,
                    evidence_name=evidence_name,
                    is_retro=self.is_retro,
                    request_id=stock.request_id,
                    transmit=transmit,
                )

            unique_key_for_place_order = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key_for_place_order = f"{original_bar_to_confirm.symbol}-{stock.specific_bar_time}"
            if (
                not already_sent_buy_order_for_stock.get(unique_key_for_place_order, False)
            ):
                already_sent_buy_order_for_stock[unique_key_for_place_order] = True
                bar_has_confirmed = True

                if self.is_retro:
                    return bar_has_confirmed

                self.tws_client.place_buy_order(
                    symbol=original_bar_to_confirm.symbol,
                    current_price=entry_position_bar.close,
                    transmit=transmit,
                )

        return bar_has_confirmed

    def should_write_log(
        self,
        most_updated_datetime: datetime.datetime,
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
    ) -> bool:
        return (
            True
            and most_updated_datetime < potential_confirmation_bar.bar_time
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.high > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.high > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.high > potential_confirmation_bar.vwap
            and potential_confirmation_bar.bar_time >= datetime.datetime(
                year=original_bar_to_confirm.bar_time.year,
                month=original_bar_to_confirm.bar_time.month,
                day=original_bar_to_confirm.bar_time.day,
                hour=9,
                minute=30,
            )
        )

    def confirm_entry_position(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        milestones: common.objects.Milestones,
    ):
        one_minute_bars: list[common.objects.BarData] = []
        highest_high_one_minute_bar: common.objects.BarData = None
        lowest_low_one_minute_bar: common.objects.BarData = None
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        already_sent_buy_order_for_stock: dict[str,bool] = {}
        stock.bars = sorted(
            stock.bars,
            key=lambda bar_object: bar_object.bar_time,
            reverse=True,
        )
        potential_confirmation_bar = None

        while True:
            if (
                True
                and potential_confirmation_bar is not None
                and highest_high_one_minute_bar is not None
                and potential_confirmation_bar.high > highest_high_one_minute_bar.high
                and potential_confirmation_bar.bar_time >= datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
            ):
                highest_high_one_minute_bar = potential_confirmation_bar

            if (
                True
                and potential_confirmation_bar is not None
                and lowest_low_one_minute_bar is not None
                and potential_confirmation_bar.low < lowest_low_one_minute_bar.low
                and potential_confirmation_bar.bar_time >= datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
            ):
                lowest_low_one_minute_bar = potential_confirmation_bar

            potential_confirmation_bar = stock.one_minute_bars_queue.get()
            if highest_high_one_minute_bar is None:
                highest_high_one_minute_bar = potential_confirmation_bar
            if lowest_low_one_minute_bar is None:
                lowest_low_one_minute_bar = potential_confirmation_bar

            self.logger.info(
                msg="Got potential bar for confirmation",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                },
            )
            stock.one_minute_bars_queue.task_done()
            date_now = datetime.datetime.now()

            if (
                potential_confirmation_bar.bar_time < datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
                or potential_confirmation_bar.bar_time < most_updated_datetime
                or not potential_confirmation_bar.ready_to_analyze
                or not potential_confirmation_bar.histogram
                or (
                    not self.is_retro
                    and potential_confirmation_bar.bar_time < datetime.datetime(
                        year=date_now.year,
                        month=date_now.month,
                        day=date_now.day,
                        hour=date_now.hour,
                        minute=date_now.minute,
                    )
                )
            ):
                continue

            should_write_log = self.should_write_log(
                most_updated_datetime=most_updated_datetime,
                potential_confirmation_bar=potential_confirmation_bar,
                original_bar_to_confirm=original_bar_to_confirm,
            )
            if should_write_log:
                self.logger.info(
                    msg="Starting to confirm one minute bar for entry point",
                    extra={
                        "worker": "Confirmator",
                        "symbol": original_bar_to_confirm.symbol,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                        "entry_position_bar_time": potential_confirmation_bar.bar_time,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "request_id": stock.request_id,
                    },
                )

            if potential_confirmation_bar.bar_time == datetime.datetime(
                year=original_bar_to_confirm.bar_time.year,
                month=original_bar_to_confirm.bar_time.month,
                day=original_bar_to_confirm.bar_time.day,
                hour=9,
                minute=30,
            ):
                highest_high_one_minute_bar = potential_confirmation_bar
                lowest_low_one_minute_bar = potential_confirmation_bar

            if self._confirm(
                stock=stock,
                milestones=milestones,
                one_minute_bars=one_minute_bars,
                potential_confirmation_bar=potential_confirmation_bar,
                original_bar_to_confirm=original_bar_to_confirm,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                already_sent_buy_order_for_stock=already_sent_buy_order_for_stock,
            ):
                break

            most_updated_datetime = potential_confirmation_bar.bar_time
            if should_write_log:
                self.logger.info(
                    msg="Entry point does not confirmed yet, waiting for next one",
                    extra={
                        "worker": "Confirmator",
                        "symbol": original_bar_to_confirm.symbol,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                        "entry_position_bar_time": potential_confirmation_bar.bar_time,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "request_id": stock.request_id,
                    },
                )

        return
