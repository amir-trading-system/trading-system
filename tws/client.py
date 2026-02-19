import decimal
import logging
import math
import queue
import time

from ibapi import client, common as ibapi_common, wrapper, order as tws_order

import common
from . import scanner
from . import data_streamer


class Client(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
        host: str,
        port: int,
        symbols_to_collect_queue: queue.Queue,
        request_id_to_symbol: dict[int, common.objects.Stock],
        bars_ready_to_analyze_queue: queue.Queue,
        logger: logging.Logger,
        potential_symbols_file_path: str = None,
    ):
        self.order_id: int = 0
        self.available_funds: float = 0.0
        client.EClient.__init__(
            self,
            self,
        )
        self.connect(
            host=host,
            port=port,
            clientId=0,
        )
        self.ibapi_requests: dict[int,common.objects.IbAPIRequest] = {}
        self.request_id_to_symbol = request_id_to_symbol
        self.order_id_to_symbol: dict[int, common.objects.Order] = {}
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.relevant_symbols: list[str] = []
        self.logger = logger

        self.scanner = scanner.Scanner(
            symbols_to_collect_queue=symbols_to_collect_queue,
            logger=logger,
        )
        self.data_streamer = data_streamer.DataStreamer(
            request_id_to_symbol=request_id_to_symbol,
            bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
            ibapi_requests=self.ibapi_requests,
            logger=logger,
            potential_symbols_file_path=potential_symbols_file_path,
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
        print(error_message)

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
        self.reqAccountSummary(
            reqId=self.next_id(),
            groupName="All",
            tags="AvailableFunds",
        )
        while not self.available_funds:
            time.sleep(1)

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

    def contractDetails(
        self,
        reqId,
        contractDetails,
    ):
        self.scanner.get_contract_details(
            request_id=reqId,
            contract_details=contractDetails,
        )
        return super().contractDetails(reqId, contractDetails)

    def request_historical_data(
        self,
        request_id: int,
        contract: client.Contract,
        end_time_str: str,
        bar_size: str,
        use_rth: int,
        duration_str: str,
        keep_up_to_date: bool,
    ):
        self.reqHistoricalData(
            reqId=request_id,
            contract=contract,
            endDateTime=end_time_str,
            durationStr=duration_str,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=use_rth,
            formatDate=2,
            chartOptions=[],
            keepUpToDate=keep_up_to_date,
        )

    def historicalData(
        self,
        reqId: int,
        bar: ibapi_common.BarData,
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
        bar: ibapi_common.BarData,
    ):
        self.data_streamer.on_historical_data_update(
            request_id=reqId,
            tws_bar=bar,
        )

    def accountSummary(
        self,
        reqId,
        account,
        tag,
        value,
        currency,
    ):
        self.available_funds = float(value)

        return super().accountSummary(reqId, account, tag, value, currency)

    def place_buy_order(
        self,
        symbol: str,
        current_price: float,
        transmit: bool,
    ) -> int:
        quantity = math.floor((self.available_funds * 0.75) / current_price)
        if quantity == 0:
            self.logger.info(
                msg="Not enough available funds to buy stock",
                extra={
                    "symbol": symbol,
                },
            )
            return 0

        self.place_order(
            symbol=symbol,
            order_action="BUY",
            order_type="MKT",
            quantity=quantity,
            transmit=transmit,
        )

        return quantity

    def place_take_profit_order(
        self,
        symbol: str,
        quantity: int,
        filled_price: float,
    ):
        self.place_order(
            symbol=symbol,
            order_action="SELL",
            order_type="LMT",
            quantity=quantity,
            price=filled_price,
            transmit=True,
        )

    def place_order(
        self,
        symbol: str,
        order_action: str,
        order_type: str,
        quantity: int,
        transmit: bool,
        price: float = None,
    ):
        contract = client.Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        order_object = tws_order.Order()
        order_object.action = order_action
        order_object.orderType = order_type
        order_object.totalQuantity = decimal.Decimal(quantity)
        order_object.transmit = transmit
        if price is not None:
            order_object.lmtPrice = price

        self.placeOrder(
            orderId=self.next_id(),
            contract=contract,
            order=order_object,
        )

    def execDetails(
        self,
        reqId,
        contract,
        execution,
    ):
        super().execDetails(reqId, contract, execution)
        self.order_id_to_symbol[execution.orderId] = common.objects.Order(
            symbol=contract.symbol,
            action=execution.side,
            status="Filled",
        )
        self.logger.info(
            msg="Order has been filled for symbol",
            extra={
                "order_action": execution.side,
                "quantity": int(execution.shares),
                "symbol": contract.symbol,
                "request_id": reqId,
            },
        )
        if execution.side == "BOT":
            self.place_take_profit_order(
                symbol=contract.symbol,
                quantity=int(execution.shares),
                filled_price=round(execution.price * 1.15, 2),
            )
