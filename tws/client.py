import decimal
import logging
import math
import queue
import time
import xml.etree.ElementTree as ET

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
        client_id: int,
        is_retro: bool,
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
            clientId=client_id,
        )
        self.ibapi_requests: dict[int,common.objects.IbAPIRequest] = {}
        self.request_id_to_symbol = request_id_to_symbol
        self.request_id_to_contract: dict[int,client.Contract] = {}
        self.order_id_to_symbol: dict[int, common.objects.Order] = {}
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.relevant_symbols: list[str] = []
        self.already_monitored: set[str] = set()
        self.logger = logger

        self.scanner = scanner.Scanner(
            symbols_to_collect_queue=symbols_to_collect_queue,
            logger=logger,
        )
        self.data_streamer = data_streamer.DataStreamer(
            request_id_to_symbol=request_id_to_symbol,
            ibapi_requests=self.ibapi_requests,
            logger=logger,
            is_retro=is_retro,
        )
        self.is_retro = is_retro

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

    def fundamentalData(
        self,
        reqId: int,
        data: str,
    ):
        parsed_fundamental_data = ET.fromstring(data)
        shares_outstanding_element = parsed_fundamental_data.find(".//SharesOut")
        if shares_outstanding_element is not None:
            available_float = float(shares_outstanding_element.attrib.get("TotalFloat", 0))
            if available_float >= 40000000:
                return super().fundamentalData(reqId, data)

        contract = self.request_id_to_contract[reqId]
        self.reqContractDetails(
            reqId=reqId,
            contract=contract,
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
        self.data_streamer.on_historical_data(
            request_id=reqId,
            tws_bar=bar,
        )

    def historicalDataEnd(
        self,
        reqId: int,
        start: str,
        end: str,
    ):
        stock = self.request_id_to_symbol[reqId]
        stock.arrange_data_for_analysis()
        stock.finished_collection = True
        unique_key = stock.symbol_name
        if self.is_retro:
            unique_key = f"{stock.symbol_name}-{stock.expected_bar_time}"
        if stock.is_worth_to_monitor() and not unique_key in self.already_monitored:
            self.bars_ready_to_analyze_queue.put(stock)
            self.already_monitored.add(unique_key)

        if self.is_retro and not stock.is_worth_to_monitor():
            stock.finished_analyze = True

        self.logger.info(
            msg="Finished to collect data for symbol",
            extra={
                "worker": "DataStreamer",
                "symbol": stock.symbol_name,
                "timeframe": stock.timeframe,
                "timeframe_type": stock.timeframe_type.value,
                "request_id": stock.request_id,
            }
        )

    def historicalDataUpdate(
        self,
        reqId: int,
        bar: ibapi_common.BarData,
    ):
        self.data_streamer.on_historical_data(
            request_id=reqId,
            tws_bar=bar,
        )
        stock = self.request_id_to_symbol[reqId]

        if stock.is_worth_to_monitor():
            self.bars_ready_to_analyze_queue.put(stock)

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
        price: float,
        transmit: bool,
        score: common.objects.Score,
    ) -> int:
        if not score.should_take_trade:
            return 0

        pct = 0
        if 50 < score.score < 60:
            pct = 0.2
        if 60 <= score.score < 70:
            pct = 0.4
        if score.score >= 70:
            pct = 0.5

        quantity = math.floor((self.available_funds * pct) / price)
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

    def place_stop_loss_order(
        self,
        symbol: str,
        quantity: int,
        filled_price: float,
    ):
        self.place_order(
            symbol=symbol,
            order_action="SELL",
            order_type="STP",
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
        if order_type == "LMT":
            if price is None:
                raise ValueError("Limit order requires a price")
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
        symbol = contract.symbol
        quantity = int(execution.shares)

        self.order_id_to_symbol[execution.orderId] = common.objects.Order(
            symbol=symbol,
            action=execution.side,
            status="Filled",
        )
        self.logger.info(
            msg="Order has been filled for symbol",
            extra={
                "order_action": execution.side,
                "quantity": quantity,
                "symbol": symbol,
                "request_id": reqId,
            },
        )
        if execution.side == "BOT":
            take_profit_price = round(execution.price * 1.3, 2)
            stop_loss_price = round(execution.price * 0.9, 2)
            self.place_take_profit_order(
                symbol=symbol,
                quantity=quantity,
                filled_price=take_profit_price,
            )
            self.place_stop_loss_order(
                symbol=symbol,
                quantity=quantity,
                filled_price=stop_loss_price,
            )
