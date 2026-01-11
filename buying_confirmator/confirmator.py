import logging
import time
import queue

from tws import objects as tws_objects

class Confirmator:
    def __init__(
        self,
        waiting_for_confirmation_queue: queue.Queue[tws_objects.BarData],
        request_id_to_symbol: dict[int,tws_objects.Stock],
        ibapi_requests: list[tws_objects.IbAPIRequest],
        logger: logging.Logger,
    ):
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.request_id_to_symbol = request_id_to_symbol
        self.ibapi_requests = ibapi_requests
        self.logger = logger

    def confirm_data(
        self,
    ):
        while True:
            if not self.waiting_for_confirmation_queue.empty():
                bar_to_confirm: tws_objects.BarData = self.waiting_for_confirmation_queue.get()
                ## TODO: continue from here
            time.sleep(1)
