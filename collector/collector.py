import datetime
import logging
import time
import queue

import common
from tws import client

class Collector:
    def __init__(
        self,
        tws_client: client.Client,
        request_id_to_symbol: dict[int,common.objects.Stock],
        logger: logging.Logger,
    ):
        self.logger = logger
        self.request_id_to_symbol = request_id_to_symbol
        self.tws_client = tws_client

    def request_historical_data(
        self,
        symbol: str,
        timeframe: int,
        timeframe_type: common.objects.TimeframeType,
        specific_bar_time: datetime.datetime,
        request_id: int,
    ):
        contract = client.client.Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        self.request_id_to_symbol[request_id] = common.objects.Stock(
            symbol_name=symbol,
            bars=[],
            timeframe=timeframe,
            timeframe_type=timeframe_type,
            one_minute_bars_queue=queue.Queue(),
        )
        ibapi_request = common.objects.IbAPIRequest(
            request_id=request_id,
            symbol=symbol,
            timeframe=timeframe,
            timeframe_type=timeframe_type,
        )
        if request_id not in self.tws_client.ibapi_requests:
            self.tws_client.ibapi_requests[request_id] = ibapi_request

        end_time_str = ""
        keep_up_to_date = True
        bar_size = ""
        duration_str = "1 W"
        use_rth = 0
        if specific_bar_time is not None:
            end_time = (specific_bar_time + datetime.timedelta(days=1)).strftime("%Y%m%d %H:%M:%S")
            end_time_str = f"{end_time} US/Eastern"
            keep_up_to_date = False

        match timeframe_type:
            case common.objects.TimeframeType.MINUTE:
                bar_size = f"{timeframe} mins"
                if timeframe == 1:
                    bar_size = f"{timeframe} min"
                    duration_str = "2 D"
            case common.objects.TimeframeType.DAY:
                bar_size = f"{timeframe} day"
                duration_str = "50 D"
                use_rth = 1

        self.tws_client.request_historical_data(
            request_id=request_id,
            contract=contract,
            end_time_str=end_time_str,
            duration_str=duration_str,
            bar_size=bar_size,
            use_rth=use_rth,
            keep_up_to_date=keep_up_to_date,
        )

    def collect_data(
        self,
        manual_timeframe_for_tests: common.objects.TimeframeInput = None,
        specific_bar_time: datetime.datetime = None,
    ):
        while True:
            if not self.tws_client.symbols_to_collect_queue.empty():
                symbol = self.tws_client.symbols_to_collect_queue.get()
                timeframes = [
                    common.objects.TimeframeInput(
                        timeframe=1,
                        timeframe_type=common.objects.TimeframeType.MINUTE,
                    ),
                    common.objects.TimeframeInput(
                        timeframe=1,
                        timeframe_type=common.objects.TimeframeType.DAY,
                    ),
                ]
                if manual_timeframe_for_tests:
                    timeframes = [
                        common.objects.TimeframeInput(
                            timeframe=1,
                            timeframe_type=common.objects.TimeframeType.MINUTE,
                        ),
                        common.objects.TimeframeInput(
                            timeframe=manual_timeframe_for_tests.timeframe,
                            timeframe_type=manual_timeframe_for_tests.timeframe_type,
                        ),
                    ]

                for timeframe_input in timeframes:
                    next_request_id = self.tws_client.next_id()

                    self.request_historical_data(
                        symbol=symbol,
                        timeframe=timeframe_input.timeframe,
                        timeframe_type=timeframe_input.timeframe_type,
                        specific_bar_time=specific_bar_time,
                        request_id=next_request_id,
                    )
            else:
                time.sleep(1)
