import datetime
import logging
import time
import threading
import queue

import alerter
from tws import objects as tws_objects, client

class Confirmator:
    is_retro: bool = False

    def __init__(
        self,
        tws_client: client.Client,
        waiting_for_confirmation_queue: queue.Queue[tws_objects.BarData],
        request_id_to_symbol: dict[int,tws_objects.Stock],
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
        relevant_stock: tws_objects.Stock,
        original_bar_to_confirm: tws_objects.BarData,
    ):
        entry_position_confirmed: bool = False
        not_relevant_anymore: bool = False
        entry_position_bar: tws_objects.BarData = None
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        one_minute_bars: list[tws_objects.BarData] = []

        while True:
            if not relevant_stock.one_minute_bars_queue.empty():
                potential_confirmation_bar = relevant_stock.one_minute_bars_queue.get()

                if (
                    potential_confirmation_bar.bar_time < original_bar_to_confirm.bar_time + datetime.timedelta(minutes=original_bar_to_confirm.timeframe-2)
                    or potential_confirmation_bar.bar_time < most_updated_datetime
                    or (potential_confirmation_bar.bar_time - original_bar_to_confirm.bar_time).seconds > 7200
                    or not potential_confirmation_bar.ready_to_analyze
                    or potential_confirmation_bar.histogram is None
                ):
                    continue

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
                    continue
                if (
                    True
                    and potential_confirmation_bar.low < original_bar_to_confirm.low
                    and not self.is_retro
                ):
                    not_relevant_anymore = True
                    break

                previous_bar = [
                    bar_obj
                    for bar_obj in one_minute_bars
                    if bar_obj.index == potential_confirmation_bar.index+1
                ]
                if len(previous_bar) == 0:
                    continue
                previous_bar = previous_bar[0]

                if (
                    True
                    and potential_confirmation_bar.ready_to_analyze
                    and potential_confirmation_bar.high >= original_bar_to_confirm.high
                    and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
                    and potential_confirmation_bar.close > potential_confirmation_bar.open_value
                    and previous_bar.volume/potential_confirmation_bar.volume <= 0.9
                    and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
                    and (potential_confirmation_bar.close-potential_confirmation_bar.open_value)/(potential_confirmation_bar.high-potential_confirmation_bar.low) >= 0.6
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
            self.tws_client.place_buy_order(
                symbol=original_bar_to_confirm.symbol,
                current_price=entry_position_bar.close,
            )

            self.alerter_object.send_alert(
                sender=f"{__name__}.{__class__.__name__}",
                symbol=entry_position_bar.symbol,
                timeframe=1,
                bar_date=entry_position_bar.bar_time,
                bar_index=entry_position_bar.index,
                message=f"""
                    <b>Entry position confirmed for:</b>
<b>Symbol:</b> <u>{entry_position_bar.symbol}</u>
<b>Timeframe:</b> <code>{entry_position_bar.timeframe}</code>
<b>Time:</b> <code>{entry_position_bar.bar_time}</code>
<b>Original bar to confirm Time:</b> <code>{original_bar_to_confirm.bar_time}</code>
<b>Original bar to confirm Timeframe:</b> <code>{original_bar_to_confirm.timeframe}</code>"""
            )

    def confirm_data(
        self,
    ):
        while True:
            if not self.waiting_for_confirmation_queue.empty():
                bar_to_confirm: tws_objects.BarData = self.waiting_for_confirmation_queue.get()
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
