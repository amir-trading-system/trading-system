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

    def confirm_entry_position(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        milestones: common.objects.Milestones,
        evidence_confirmator: analyzer.evidences._evidence.Evidence,
    ):
        entry_position_confirmed: bool = False
        entry_position_bar: common.objects.BarData = None
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

                one_minute_bars.append(potential_confirmation_bar)
                most_updated_datetime = potential_confirmation_bar.bar_time
                if potential_confirmation_bar.bar_time < datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=9,
                    minute=30,
                ):
                    continue

                if evidence_confirmator.confirm(
                    relevant_stock=relevant_stock,
                    potential_confirmation_bar=potential_confirmation_bar,
                    milestones=milestones,
                    highest_high_one_minute=highest_high_one_minute,
                ):
                    entry_position_confirmed = True
                    entry_position_bar = potential_confirmation_bar
                    break

        if entry_position_confirmed:
            self.logger.info(
                "Bar has confirmed",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": entry_position_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                },
            )
            self.request_id_to_symbol[relevant_stock.request_id].finished_confirmation = True
            self.results_queue.put(
                {
                    "symbol": relevant_stock.symbol_name,
                    "original_bar_time": original_bar_to_confirm.bar_time,
                    "confirmation_bar_time": entry_position_bar.bar_time,
                },
            )

            if self.alerter_object:
                self.alerter_object.send_confirmation_alert(
                    sender="Confirmator",
                    original_bar=original_bar_to_confirm,
                    entry_position_bar=entry_position_bar,
                    is_retro=self.is_retro,
                )

            unique_key = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key = f"{original_bar_to_confirm.symbol}-{relevant_stock.specific_bar_time}"
            if (
                not already_sent_buy_order_for_stock.get(unique_key, False)
            ):
                already_sent_buy_order_for_stock[unique_key] = True
                if self.is_retro:
                    return

                self.tws_client.place_buy_order(
                    symbol=original_bar_to_confirm.symbol,
                    current_price=entry_position_bar.close,
                    transmit=False,
                )

        return
