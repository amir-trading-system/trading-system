import logging
import threading
import queue

import alerter
import common
from tws import client

from . import days_confirmator


class Confirmator:
    def __init__(
        self,
        tws_client: client.Client,
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        results_queue: queue.Queue[dict[str,any]],
        request_id_to_symbol: dict[int,common.objects.Stock],
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter = None,
        is_retro: bool = False,
    ):
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.request_id_to_symbol = request_id_to_symbol

        self.days_confirmator = days_confirmator.Confirmator(
            is_retro=is_retro,
            tws_client=tws_client,
            request_id_to_symbol=request_id_to_symbol,
            logger=logger,
            results_queue=results_queue,
            alerter_object=alerter_object,
        )

    def confirm_data(
        self,
    ):
        while True:
            bar_to_milestones: dict[str, any] = self.waiting_for_confirmation_queue.get()

            bar_to_confirm: common.objects.BarData = bar_to_milestones["bar_to_confirm"]
            milestones: common.objects.Milestones = bar_to_milestones["milestones"]

            relevant_stock = [
                stock
                for _, stock in self.request_id_to_symbol.items()
                if stock.is_same(
                    symbol=bar_to_confirm.symbol,
                    timeframe=bar_to_confirm.timeframe,
                    timeframe_type=bar_to_confirm.timeframe_type,
                    specific_bar_time=bar_to_confirm.bar_time,
                )
            ][0]

            threading.Thread(
                target=self.days_confirmator.confirm_entry_position,
                kwargs={
                    "relevant_stock": relevant_stock,
                    "original_bar_to_confirm": bar_to_confirm,
                    "milestones": milestones,
                },
            ).start()
