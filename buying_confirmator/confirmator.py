import datetime
import logging
import time
import threading
import queue

import alerter
import common
from tws import client

class Confirmator:
    is_retro: bool = False

    def __init__(
        self,
        tws_client: client.Client,
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        request_id_to_symbol: dict[int,common.objects.Stock],
        alerter_object: alerter.alerter.Alerter,
        logger: logging.Logger,
    ):
        self.tws_client = tws_client
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.request_id_to_symbol = request_id_to_symbol
        self.alerter_object = alerter_object
        self.logger = logger

    def confirm_entry_position(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
    ):
        entry_position_confirmed: bool = False
        not_relevant_anymore: bool = False
        entry_position_bar: common.objects.BarData = None
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        one_minute_bars: list[common.objects.BarData] = []
        already_sent_buy_order_for_stock: dict[str,bool] = {}

        while True:
            if not relevant_stock.one_minute_bars_queue.empty():
                potential_confirmation_bar = relevant_stock.one_minute_bars_queue.get()

                if (
                    potential_confirmation_bar.bar_time < original_bar_to_confirm.bar_time + datetime.timedelta(minutes=original_bar_to_confirm.timeframe-2)
                    or potential_confirmation_bar.bar_time < most_updated_datetime
                    or (potential_confirmation_bar.bar_time - original_bar_to_confirm.bar_time).seconds > 7200
                    or not potential_confirmation_bar.ready_to_analyze
                    or not potential_confirmation_bar.histogram
                ):
                    relevant_stock.one_minute_bars_queue.put(potential_confirmation_bar)
                    continue

                if not self.is_retro:
                    log_message = ""
                    if potential_confirmation_bar.low < original_bar_to_confirm.low:
                        log_message = "No need to confirm bar anymore, got lower than bar himself"

                    one_minute_bar_is_too_late = (
                        True
                        and (potential_confirmation_bar.bar_time - original_bar_to_confirm.bar_time).seconds > 3600
                        and potential_confirmation_bar.bar_time > original_bar_to_confirm.bar_time
                    )
                    if one_minute_bar_is_too_late:
                        log_message = "No need to confirm bar anymore: It has been more than an hour since original bar"

                    if log_message:
                        not_relevant_anymore = True
                        self.logger.info(
                            msg=log_message,
                            extra={
                                "worker": "Confirmator",
                                "symbol": original_bar_to_confirm.symbol,
                                "timeframe": original_bar_to_confirm.timeframe,
                                "bar_time": original_bar_to_confirm.bar_time,
                                "last_one_minute_bar_time": most_updated_datetime,
                            },
                        )
                        break

                one_minute_bars.append(potential_confirmation_bar)
                most_updated_datetime = potential_confirmation_bar.bar_time

                self.logger.info(
                    msg="Trying to confirm bar",
                    extra={
                        "worker": "Confirmator",
                        "symbol": original_bar_to_confirm.symbol,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "last_one_minute_bar_time": most_updated_datetime,
                    },
                )

                if (potential_confirmation_bar.bar_time - original_bar_to_confirm.bar_time).seconds / 60 < original_bar_to_confirm.timeframe:
                    relevant_stock.one_minute_bars_queue.put(potential_confirmation_bar)
                    continue

                previous_bar = [
                    bar_obj
                    for bar_obj in one_minute_bars
                    if bar_obj.index == potential_confirmation_bar.index+1
                ]
                if len(previous_bar) == 0:
                    relevant_stock.one_minute_bars_queue.put(potential_confirmation_bar)
                    continue
                previous_bar = previous_bar[0]

                if potential_confirmation_bar.high-potential_confirmation_bar.low == 0:
                    continue

                potential_bar_body_percentage = (potential_confirmation_bar.close-potential_confirmation_bar.open_value)/(potential_confirmation_bar.high-potential_confirmation_bar.low)

                if (
                    True
                    and potential_confirmation_bar.ready_to_analyze
                    and potential_confirmation_bar.high >= original_bar_to_confirm.high
                    and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
                    and potential_confirmation_bar.close > potential_confirmation_bar.open_value
                    and previous_bar.volume/potential_confirmation_bar.volume <= 0.9
                    and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
                    and potential_bar_body_percentage >= 0.6
                ):
                    above_volume_average_count = len(
                        [
                            bar_obj
                            for bar_obj in one_minute_bars
                            if bar_obj.volume > bar_obj.volume_average
                        ]
                    )
                    under_volume_average_count = len(
                        [
                            bar_obj
                            for bar_obj in one_minute_bars
                            if bar_obj.volume <= bar_obj.volume_average
                        ]
                    )

                    bars_not_showing_real_retracement = (
                        True
                        and len(one_minute_bars) > 10
                        and above_volume_average_count/under_volume_average_count >= 0.75
                    )

                    if not bars_not_showing_real_retracement:
                        entry_position_confirmed = True
                        entry_position_bar = potential_confirmation_bar
                        break

            if entry_position_confirmed or not_relevant_anymore:
                break

        if entry_position_confirmed:
            self.logger.info(
                "Bar has confirmed",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "entry_position_bar_time": entry_position_bar.bar_time,
                },
            )

            self.alerter_object.send_confirmation_alert(
                sender="Confirmator",
                original_bar=original_bar_to_confirm,
                entry_position_bar=entry_position_bar,
            )

            if (
                not already_sent_buy_order_for_stock.get(original_bar_to_confirm.symbol, False)
            ):
                already_sent_buy_order_for_stock[original_bar_to_confirm.symbol] = True
                if self.is_retro:
                    return

                self.tws_client.place_buy_order(
                    symbol=original_bar_to_confirm.symbol,
                    current_price=entry_position_bar.close,
                    transmit=False,
                )

        return

    def confirm_data(
        self,
    ):
        while True:
            if not self.waiting_for_confirmation_queue.empty():
                bar_to_confirm: common.objects.BarData = self.waiting_for_confirmation_queue.get()
                relevant_stock = [
                    stock
                    for _, stock in self.request_id_to_symbol.items()
                    if (
                        True
                        and stock.symbol_name == bar_to_confirm.symbol
                        and stock.timeframe == bar_to_confirm.timeframe
                    )
                ][0]

                threading.Thread(
                    target=self.confirm_entry_position,
                    kwargs={
                        "relevant_stock": relevant_stock,
                        "original_bar_to_confirm": bar_to_confirm,
                    },
                ).start()

            time.sleep(1)
