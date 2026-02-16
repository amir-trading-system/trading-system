import logging
import time
import threading
import queue

import alerter
import analyzer.evidences
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
            if not self.waiting_for_confirmation_queue.empty():
                bar_to_milestones: dict[str, any] = self.waiting_for_confirmation_queue.get()

                bar_to_confirm: common.objects.BarData = bar_to_milestones["bar_to_confirm"]
                milestones: common.objects.Milestones = bar_to_milestones["milestones"]
                evidences: list[analyzer.evidences._evidence.Evidence] = bar_to_milestones["evidences"]

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
                        "evidences": evidences,
                    },
                ).start()


            time.sleep(1)
