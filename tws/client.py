import datetime
import logging
import queue

import pandas as pd
import talib
from talib import MA_Type
from ibapi import client, wrapper, common, tag_value

import alerter
from . import objects


class Client(client.EClient, wrapper.EWrapper):
    on_specific_bar_time: bool = False
    is_retro: bool = False

    def __init__(
        self,
        host: str,
        port: int,
        ibapi_requests: list[objects.IbAPIRequest],
        request_id_to_symbol: dict[int, objects.Stock],
        symbols_to_collect_queue: queue.Queue,
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
        self.ibapi_requests = ibapi_requests
        self.request_id_to_symbol = request_id_to_symbol
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.relevant_symbols: list[str] = []
        self.logger = logger
        self.alerter_object = alerter_object

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

    #pylint: disable=too-many-arguments,too-many-positional-arguments
    def error(
        self,
        reqId,
        errorTime,
        errorCode,
        errorString,
        advancedOrderRejectJson="",
    ):
        if reqId == -1:
            return

        error_message = f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}"
        self.alerter_object.alert_on_error(
            message=error_message,
        )

    def _get_scanner_subscription(
        self,
    ) -> client.ScannerSubscription:
        scanner_subscription = client.ScannerSubscription()
        scanner_subscription.numberOfRows = 50
        scanner_subscription.instrument = "STK"
        scanner_subscription.locationCode = "STK.US.MAJOR"
        scanner_subscription.scanCode = "TOP_PERC_GAIN"


        return scanner_subscription

    def _get_scanner_filters(
        self,
    ) -> list[tag_value.TagValue]:
        return [
            tag_value.TagValue("volumeAbove", "100000"),
            tag_value.TagValue("priceAbove", "1"),
            tag_value.TagValue("priceBelow", "100"),
            tag_value.TagValue("marketCapBelow1e6", "500000000"),
            tag_value.TagValue("changePercAbove", "20")
        ]

    def start_scanner(
        self,
        manual_results_for_test: list[str] = None,
    ):
        if manual_results_for_test:
            for test_symbol in manual_results_for_test:
                self.symbols_to_collect_queue.put(test_symbol)
        else:
            scanner_subscription = self._get_scanner_subscription()
            filters = self._get_scanner_filters()
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
        no_opening_trades = False
        symbol_name = contractDetails.contract.symbol
        if symbol_name not in self.relevant_symbols:
            if contractDetails.ineligibilityReasonList is not None:
                for reason in contractDetails.ineligibilityReasonList:
                    if (
                        str(reason.description).startswith("No Opening Trades")
                        or "this product is in closing-only status" in str(reason.description)
                    ):
                        no_opening_trades = True
                        self.relevant_symbols.append(contractDetails.contract.symbol)
                        break
            if not no_opening_trades:
                if contractDetails.contract.symbol not in self.relevant_symbols:
                    self.logger.info(
                        msg="New symbol founded by scanner",
                        extra={
                            "worker": f"{__name__}.{__class__.__name__}",
                            "symbol": contractDetails.contract.symbol,
                            "symbol_type": contractDetails.stockType,
                        },
                    )
                    self.relevant_symbols.append(contractDetails.contract.symbol)
                    self.symbols_to_collect_queue.put(contractDetails.contract.symbol)

        return super().contractDetails(reqId, contractDetails)

    def _filter_ignored_bars(
        self,
        bars: list[objects.BarData],
    ):
        relevant_bars: list[objects.BarData] = []
        for i, bar_object in enumerate(bars):
            if (
                bar_object.bar_time.hour == 8
                and bar_object.bar_time.minute == 0
                and i+1 < len(bars)-1
            ):
                bar_before = bars[i-1]
                bar_after = bars[i+1]
                if (
                    bar_object.volume > bar_before.volume * 10
                    and bar_object.volume > bar_after.volume * 10
                    and bar_object.high - bar_object.low > (bar_before.high - bar_before.low) * 10
                    and bar_object.high - bar_object.low > (bar_after.high - bar_after.low) * 10
                ):
                    continue

            relevant_bars.append(bar_object)

        return relevant_bars

    #pylint: disable=no-member
    def enrich_bars(
        self,
        bars: list[objects.BarData],
    ) -> list[objects.BarData]:
        fitered_bars = self._filter_ignored_bars(
            bars=bars,
        )
        bar_data_df = pd.DataFrame([vars(bar_candle) for bar_candle in fitered_bars])

        bar_data_df["ema_9"] = talib.EMA(
            real=bar_data_df["close"],
            timeperiod=9,
        )
        bar_data_df["ema_20"] = talib.EMA(
            real=bar_data_df["close"],
            timeperiod=20,
        )
        bar_data_df["volume_average"] = talib.SMA(
            real=bar_data_df["volume"],
            timeperiod=20,
        )

        ## calculate vwap
        bar_data_df["bar_time"] = (
            pd.to_datetime(bar_data_df["bar_time"])
        )
        since_open_bar_df = bar_data_df.where(
            (bar_data_df["bar_time"].dt.time >= pd.to_datetime("09:30").time()) &
            (bar_data_df["bar_time"].dt.time <= pd.to_datetime("16:00").time())
        )
        since_open_bar_df["session"] = since_open_bar_df["bar_time"].dt.date

        since_open_bar_df["volume"] = since_open_bar_df["volume"].astype(float)
        since_open_bar_df["hlc3"] = (since_open_bar_df["high"] + since_open_bar_df["low"] + since_open_bar_df["close"]) / 3
        since_open_bar_df["pv"] = since_open_bar_df["hlc3"] * since_open_bar_df["volume"]

        bar_data_df["vwap"] = since_open_bar_df.groupby("session")["pv"].cumsum() / since_open_bar_df.groupby("session")["volume"].cumsum()

        [macd, signal_line, histogram] = talib.MACDEXT(
            real=bar_data_df["close"],
            fastperiod=12,
            fastmatype=MA_Type.EMA,
            slowperiod=26,
            slowmatype=MA_Type.EMA,
            signalperiod=9,
            signalmatype=MA_Type.EMA,
        )
        bar_data_df["macd"] = macd
        bar_data_df["signal_line"] = signal_line
        bar_data_df["histogram"] = histogram

        results_dict = bar_data_df.to_dict(orient="records")
        bars = sorted(
            [objects.BarData(**kwargs) for kwargs in results_dict],
            key=lambda bar: bar.bar_time,
        )
        for i, bar_object in enumerate(bars):
            bar_object.index = len(bars) - i-1

        return bars

    def request_historical_data(
        self,
        symbol: str,
        timeframe: int,
        specific_bar_time: datetime.datetime,
    ):
        contract = client.Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        request_id = self.next_id()
        self.request_id_to_symbol[request_id] = objects.Stock(
            symbol_name=symbol,
            bars=[],
            timeframe=timeframe,
        )
        ibapi_request = objects.IbAPIRequest(
            request_id=request_id,
            symbol=symbol,
            timeframe=timeframe,
        )
        if ibapi_request not in self.ibapi_requests:
            self.ibapi_requests.append(ibapi_request)

        end_time_str = ""
        keep_up_to_date = True
        if specific_bar_time is not None:
            end_time = (specific_bar_time + datetime.timedelta(days=1)).strftime("%Y%m%d %H:%M:%S")
            end_time_str = f"{end_time} US/Eastern"
            keep_up_to_date = False

        bar_size = f"{timeframe} mins"
        if timeframe == 1:
            bar_size = f"{timeframe} min"

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
        bar_time = datetime.datetime.fromtimestamp(float(bar.date))
        now = datetime.datetime.now()
        if (
            (now.day != bar_time.day and bar_time.hour < 16 and not self.on_specific_bar_time and not self.is_retro)
            or bar.volume == 0.0
        ):
            return

        ibapi_request = [
            request
            for request in self.ibapi_requests
            if request.request_id == reqId
        ]
        if len(ibapi_request) == 0:
            return

        ibapi_request = ibapi_request[0]
        self.request_id_to_symbol[reqId].bars.append(
            objects.BarData(
                symbol=ibapi_request.symbol,
                timeframe=ibapi_request.timeframe,
                open_value=bar.open,
                close=bar.close,
                high=bar.high,
                low=bar.low,
                volume=float(bar.volume),
                bar_time=bar_time,
            )
        )

    def historicalDataEnd(
        self,
        reqId: int,
        start: str,
        end: str,
    ):
        if self.on_specific_bar_time or self.is_retro:
            relevant_symbol_bars = self.request_id_to_symbol[reqId].bars
            symbol = self.request_id_to_symbol[reqId].symbol_name
            bars_data = self.enrich_bars(
                bars=relevant_symbol_bars,
            )
            for bar_object in bars_data:
                bar_object.ready_to_analyze = True
            self.request_id_to_symbol[reqId].bars = bars_data
            self.request_id_to_symbol[reqId].ready_to_confirm = True
            if self.request_id_to_symbol[reqId].timeframe == 1:
                return

            self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[reqId])
            self.logger.info(
                msg="Finished to collect data for symbol",
                extra={
                    "worker": f"{__name__}.{__class__.__name__}",
                    "symbol": symbol,
                }
            )

    def historicalDataUpdate(
        self,
        reqId: int,
        bar: common.BarData,
    ):
        if bar.volume == 0.0:
            return
        relevant_symbol_bars = self.request_id_to_symbol[reqId].bars
        current_bar_time = datetime.datetime.fromtimestamp(float(bar.date))

        ibapi_request = [
            request
            for request in self.ibapi_requests
            if request.request_id == reqId
        ]
        if len(ibapi_request) == 0:
            return

        ibapi_request = ibapi_request[0]

        current_bar = objects.BarData(
            symbol=ibapi_request.symbol,
            timeframe=ibapi_request.timeframe,
            open_value=bar.open,
            close=bar.close,
            high=bar.high,
            low=bar.low,
            volume=bar.volume,
            bar_time=current_bar_time,
        )

        if relevant_symbol_bars[-1].bar_time == current_bar_time:
            relevant_symbol_bars[-1].close = bar.close
            relevant_symbol_bars[-1].open_value = bar.open
            relevant_symbol_bars[-1].high = bar.high
            relevant_symbol_bars[-1].low = bar.low
            relevant_symbol_bars[-1].volume = bar.volume

            bars_data = self.enrich_bars(
                bars=relevant_symbol_bars,
            )
            return

        relevant_symbol_bars[-1].ready_to_analyze = True
        relevant_symbol_bars.append(current_bar)
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        self.request_id_to_symbol[reqId].bars = bars_data
        self.request_id_to_symbol[reqId].ready_to_confirm = True

        if self.request_id_to_symbol[reqId].timeframe == 1:
            return

        self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[reqId])
        relevant_symbol = self.request_id_to_symbol[reqId]
        self.logger.info(
            msg="Bar is ready to analyze and confirm",
            extra={
                "worker": f"{__name__}.{__class__.__name__}",
                "symbol": relevant_symbol.symbol_name,
                "timeframe": relevant_symbol.timeframe,
            }
        )
