import datetime
import logging
import queue

import alerter
import analyzer.evidences
import common
from tws import client


class Confirmator:
    def __init__(
        self,
        is_retro: bool,
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
        self.symbol_to_evidences: dict[str, list[analyzer.evidences._evidence.Evidence]] = {}

    def _confirm(
        self,
        relevant_stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        one_minute_bars: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
        highest_high_one_minute: float,
        already_sent_buy_order_for_stock: dict[str,bool],
    ) -> bool:
        bar_has_confirmed: bool = False
        entry_position_bar: common.objects.BarData = None
        one_minute_bars.append(potential_confirmation_bar)

        if potential_confirmation_bar.bar_time < datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=9,
            minute=30,
        ):
            return bar_has_confirmed

        confirmation_key = f"{original_bar_to_confirm.symbol}-{original_bar_to_confirm.bar_time}"
        evidences = self.symbol_to_evidences[confirmation_key]
        confirmed_evidences: list[str] = []
        for evidence in evidences:
            if evidence.confirm(
                relevant_stock=relevant_stock,
                original_bar_to_confirm=original_bar_to_confirm,
                potential_confirmation_bar=potential_confirmation_bar,
                milestones=milestones,
                highest_high_one_minute=highest_high_one_minute,
                one_minute_bars=one_minute_bars,
            ):
                entry_position_bar = potential_confirmation_bar
                confirmed_evidences.append(evidence.name)

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
                },
            )
            self.results_queue.put(
                {
                    "symbol": relevant_stock.symbol_name,
                    "original_bar_time": original_bar_to_confirm.bar_time,
                    "confirmation_bar_time": entry_position_bar.bar_time,
                    "evidence_name": evidence_name,
                },
            )

            if self.alerter_object:
                self.alerter_object.send_confirmation_alert(
                    sender="Confirmator",
                    original_bar=original_bar_to_confirm,
                    entry_position_bar=entry_position_bar,
                    evidence_name=evidence_name,
                    is_retro=self.is_retro,
                )

            unique_key_for_place_order = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key_for_place_order = f"{original_bar_to_confirm.symbol}-{relevant_stock.specific_bar_time}"
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
                    transmit=False,
                )
                return bar_has_confirmed

        return bar_has_confirmed

    def confirm_entry_position(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        milestones: common.objects.Milestones,
    ):
        one_minute_bars: list[common.objects.BarData] = []
        highest_high_one_minute: float = 0.0
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        already_sent_buy_order_for_stock: dict[str,bool] = {}
        relevant_stock.bars = sorted(
            relevant_stock.bars,
            key=lambda bar_object: bar_object.bar_time,
            reverse=True,
        )
        potential_confirmation_bar = None

        while True:
            if not relevant_stock.one_minute_bars_queue.empty():
                if (
                    True
                    and potential_confirmation_bar is not None
                    and potential_confirmation_bar.high > highest_high_one_minute
                    and potential_confirmation_bar.bar_time >= datetime.datetime(
                        year=original_bar_to_confirm.bar_time.year,
                        month=original_bar_to_confirm.bar_time.month,
                        day=original_bar_to_confirm.bar_time.day,
                        hour=4,
                    )
                ):
                    highest_high_one_minute = potential_confirmation_bar.high

                potential_confirmation_bar = relevant_stock.one_minute_bars_queue.get()
                relevant_stock.one_minute_bars_queue.task_done()
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

                most_updated_datetime = potential_confirmation_bar.bar_time
                if self._confirm(
                    relevant_stock=relevant_stock,
                    milestones=milestones,
                    one_minute_bars=one_minute_bars,
                    potential_confirmation_bar=potential_confirmation_bar,
                    original_bar_to_confirm=original_bar_to_confirm,
                    highest_high_one_minute=highest_high_one_minute,
                    already_sent_buy_order_for_stock=already_sent_buy_order_for_stock,
                ):
                    break

        return
