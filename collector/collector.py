import datetime
import logging
import time
import queue

import alerter
from tws import objects, client

class Collector:
    def __init__(
        self,
        tws_host: str,
        tws_port: int,
        symbols_to_collect_queue: queue.Queue[str],
        bars_ready_to_analyze_queue: queue.Queue[objects.Stock],
        request_id_to_symbol: dict[int,objects.Stock],
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter,
    ):
        self.logger = logger
        self.request_id_to_symbol = request_id_to_symbol
        self.tws_client = client.Client(
            host=tws_host,
            port=tws_port,
            symbols_to_collect_queue=symbols_to_collect_queue,
            bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
            request_id_to_symbol=request_id_to_symbol,
            logger=logger,
            alerter_object=alerter_object,
        )

    def request_historical_data(
        self,
        symbol: str,
        timeframe: int,
        specific_bar_time: datetime.datetime,
        request_id: int,
    ):
        contract = client.client.Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        self.request_id_to_symbol[request_id] = objects.Stock(
            symbol_name=symbol,
            bars=[],
            timeframe=timeframe,
            one_minute_bars_queue=queue.Queue(),
        )
        ibapi_request = objects.IbAPIRequest(
            request_id=request_id,
            symbol=symbol,
            timeframe=timeframe,
            last_time_analyzed=datetime.datetime.fromtimestamp(0),
        )
        if request_id not in self.tws_client.ibapi_requests:
            self.tws_client.ibapi_requests[request_id] = ibapi_request

        end_time_str = ""
        keep_up_to_date = True
        if specific_bar_time is not None:
            end_time = (specific_bar_time + datetime.timedelta(days=1)).strftime("%Y%m%d %H:%M:%S")
            end_time_str = f"{end_time} US/Eastern"
            keep_up_to_date = False

        bar_size = f"{timeframe} mins"
        if timeframe == 1:
            bar_size = f"{timeframe} min"

        self.tws_client.request_historical_data(
            request_id=request_id,
            contract=contract,
            end_time_str=end_time_str,
            bar_size=bar_size,
            keep_up_to_date=keep_up_to_date,
        )

    def collect_data(
        self,
        manual_timeframe_for_tests: int = None,
        specific_bar_time: datetime.datetime = None,
    ):
        while True:
            if not self.tws_client.symbols_to_collect_queue.empty():
                symbol = self.tws_client.symbols_to_collect_queue.get()
                timeframes = [1, 5, 15, 30]
                if manual_timeframe_for_tests:
                    timeframes = [1, manual_timeframe_for_tests]

                for timeframe in timeframes:
                    next_request_id = self.tws_client.next_id()

                    self.request_historical_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        specific_bar_time=specific_bar_time,
                        request_id=next_request_id,
                    )
            else:
                time.sleep(1)
