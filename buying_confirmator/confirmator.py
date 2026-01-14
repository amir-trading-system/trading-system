import datetime
import logging
import time
import threading
import queue

import alerter
from tws import objects as tws_objects

class Confirmator:
    def __init__(
        self,
        waiting_for_confirmation_queue: queue.Queue[tws_objects.BarData],
        request_id_to_symbol: dict[int,tws_objects.Stock],
        ibapi_requests: list[tws_objects.IbAPIRequest],
        alerter_object: alerter.alerter.Alerter,
        logger: logging.Logger,
    ):
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.request_id_to_symbol = request_id_to_symbol
        self.ibapi_requests = ibapi_requests
        self.alerter_object = alerter_object
        self.logger = logger

    def confirm_entry_position(
        self,
        one_minute_timeframe_request_id: int,
        original_bar_to_confirm: tws_objects.BarData,
    ):
        entry_position_confirmed: bool = False
        entry_position_bar: tws_objects.BarData = None
        most_updated_datetime = None

        while True:
            one_minute_stock_data: tws_objects.Stock = self.request_id_to_symbol[one_minute_timeframe_request_id]
            if len(one_minute_stock_data.bars) == 0:
                continue

            last_datetime = one_minute_stock_data.bars[-2].bar_time
            if one_minute_stock_data.bars[-2].low < original_bar_to_confirm.low:
                self.logger.info(
                    msg="Bar no logger need to be confirmed. crossed its low down",
                    extra={
                        "worker": "Confirmator",
                        "symbol": original_bar_to_confirm.symbol,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "last_one_minute_bar_time": one_minute_stock_data.bars[-2].bar_time,
                    }
                )
                break

            if (
                not one_minute_stock_data.ready_to_confirm
                or most_updated_datetime == last_datetime
            ):
                continue

            most_updated_datetime = one_minute_stock_data.bars[-2].bar_time

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

            one_minute_timeframe_starting_bar_to_look_from = [
                bar_object
                for bar_object in one_minute_stock_data.bars
                if bar_object.bar_time == original_bar_to_confirm.bar_time + datetime.timedelta(
                    minutes=original_bar_to_confirm.timeframe,
                )
            ]
            if len(one_minute_timeframe_starting_bar_to_look_from) == 0:
                continue

            one_minute_timeframe_starting_bar_to_look_from = one_minute_timeframe_starting_bar_to_look_from[0]

            relevant_bars = [
                bar_object
                for bar_object in one_minute_stock_data.bars
                if bar_object.bar_time >= one_minute_timeframe_starting_bar_to_look_from.bar_time
                and bar_object.ready_to_analyze
            ]

            highest_volume_until_now = 0
            for i, bar_object in enumerate(relevant_bars):
                bars_to_check = [
                    bar_obj
                    for bar_obj in relevant_bars[:i]
                    if bar_obj.bar_time >= one_minute_timeframe_starting_bar_to_look_from.bar_time
                    and bar_obj.bar_time <= one_minute_timeframe_starting_bar_to_look_from.bar_time + datetime.timedelta(
                        hours=8,
                    )
                ]
                previous_bar = [
                    bar_obj
                    for bar_obj in bars_to_check
                    if bar_obj.index == bar_object.index+1
                ]
                if len(previous_bar) == 0:
                    continue
                previous_bar = previous_bar[0]

                highest_volume_until_now = max(highest_volume_until_now, bar_object.volume)
                bar_is_most_volatile_since_now = (
                    True
                    and not any(
                        bar_obj
                        for bar_obj in bars_to_check
                        if bar_obj.volume > bar_obj.volume_average
                        and bar_obj.volume > bar_object.volume
                    )
                    and bar_object.volume > bar_object.volume_average
                )

                if (
                    True
                    and bar_object.ready_to_analyze
                    and bar_is_most_volatile_since_now
                    and bar_object.volume > bar_object.volume_average
                    and bar_object.close > bar_object.open_value
                    and bar_object.volume == highest_volume_until_now
                    and previous_bar.volume < previous_bar.volume_average
                    and bar_object.close > bar_object.ema_9
                ):
                    above_volume_average_count = len(
                        [
                            bar_obj
                            for bar_obj in bars_to_check
                            if bar_obj.volume > bar_obj.volume_average
                        ]
                    )
                    under_volume_average_count = len(
                        [
                            bar_obj
                            for bar_obj in bars_to_check
                            if bar_obj.volume <= bar_obj.volume_average
                        ]
                    )
                    bars_not_showing_real_retracement = (
                        True
                        and len(bars_to_check) > 10
                        and above_volume_average_count/under_volume_average_count >= 0.75
                    )

                    if not bars_not_showing_real_retracement:
                        entry_position_confirmed = True
                        entry_position_bar = bar_object
                        break

            if entry_position_confirmed:
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

            self.alerter_object.alert(
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
<b>Original bar to confirm Time:</b> <code>{original_bar_to_confirm.bar_time}</code>"""
            )

    def confirm_data(
        self,
    ):
        while True:
            if not self.waiting_for_confirmation_queue.empty():
                bar_to_confirm: tws_objects.BarData = self.waiting_for_confirmation_queue.get()
                one_minute_timeframe_request_id = [
                    request_id
                    for request_id, symbol_data in self.request_id_to_symbol.items()
                    if (
                        True
                        and symbol_data.symbol_name == bar_to_confirm.symbol
                        and symbol_data.timeframe == 1
                    )
                ]

                if len(one_minute_timeframe_request_id) == 0:
                    continue
                one_minute_timeframe_request_id = one_minute_timeframe_request_id[0]

                threading.Thread(
                    target=self.confirm_entry_position,
                    kwargs={
                        "one_minute_timeframe_request_id": one_minute_timeframe_request_id,
                        "original_bar_to_confirm": bar_to_confirm,
                    },
                ).start()

            time.sleep(1)
