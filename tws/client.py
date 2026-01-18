import logging
import queue

from ibapi import client, common, wrapper

import alerter
from . import scanner
from . import data_streamer
from . import objects


class Client(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
        host: str,
        port: int,
        symbols_to_collect_queue: queue.Queue,
        request_id_to_symbol: dict[int, objects.Stock],
        bars_ready_to_analyze_queue: queue.Queue,
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter,
    ):
        self.order_id = None
        client.EClient.__init__(
            self,
            self,
        )
        self.connect(
            host=host,
            port=port,
            clientId=0,
        )
        self.ibapi_requests: dict[int,objects.IbAPIRequest] = {}
        self.request_id_to_symbol = request_id_to_symbol
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.relevant_symbols: list[str] = []
        self.logger = logger
        self.alerter_object = alerter_object

        self.scanner = scanner.Scanner(
            symbols_to_collect_queue=symbols_to_collect_queue,
            logger=logger,
            alerter_object=alerter_object,
        )
        self.data_streamer = data_streamer.DataStreamer(
            request_id_to_symbol=request_id_to_symbol,
            bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
            ibapi_requests=self.ibapi_requests,
            logger=logger,
            alerter_object=alerter_object,
        )

    #pylint: disable=too-many-arguments,too-many-positional-arguments
    def error(
        self,
        reqId,
        errorTime,
        errorCode,
        errorString,
        advancedOrderRejectJson="",
    ):
        if reqId == -1 or errorCode == 162:
            return

        error_message = f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}"
        if errorCode == 366:
            print(error_message)
        else:
            self.alerter_object.alert_on_error(
                message=error_message,
            )

    def nextValidId(
        self,
        orderId,
    ):
        self.order_id = orderId

    def next_id(
        self,
    ):
        self.order_id += 1
        return self.order_id

    def start_scanner(
        self,
        manual_results_for_test: list[str] = None,
    ):
        if manual_results_for_test:
            for test_symbol in manual_results_for_test:
                self.symbols_to_collect_queue.put(test_symbol)
        else:
            scanner_subscription = self.scanner.get_scanner_subscription()
            filters = self.scanner.get_scanner_filters()
            request_id = self.next_id()

            self.reqScannerSubscription(
                reqId=request_id,
                subscription=scanner_subscription,
                scannerSubscriptionOptions=[],
                scannerSubscriptionFilterOptions=filters,
            )

    #pylint: disable=too-many-arguments,too-many-positional-arguments
    def scannerData(
        self,
        reqId,
        rank,
        contractDetails,
        distance,
        benchmark,
        projection,
        legsStr,
    ):
        self.reqContractDetails(
            reqId=reqId,
            contract=contractDetails.contract,
        )

    def contractDetails(self, reqId, contractDetails):
        self.scanner.get_contract_details(
            contract_details=contractDetails,
        )
        return super().contractDetails(reqId, contractDetails)

    def request_historical_data(
        self,
        request_id: int,
        contract: client.Contract,
        end_time_str: str,
        bar_size: str,
        keep_up_to_date: bool,
    ):
        self.reqHistoricalData(
            reqId=request_id,
            contract=contract,
            endDateTime=end_time_str,
            durationStr="1 W",
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=0,
            formatDate=2,
            chartOptions=[],
            keepUpToDate=keep_up_to_date,
        )

    def historicalData(
        self,
        reqId: int,
        bar: common.BarData,
    ):
        self.data_streamer.get_historical_data(
            request_id=reqId,
            tws_bar=bar,
        )

    def historicalDataEnd(
        self,
        reqId: int,
        start: str,
        end: str,
    ):
        self.data_streamer.on_historical_data_end(
            request_id=reqId,
        )

    def historicalDataUpdate(
        self,
        reqId: int,
        bar: common.BarData,
    ):
        self.data_streamer.on_historical_data_update(
            request_id=reqId,
            tws_bar=bar,
        )
