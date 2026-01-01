import datetime
import queue

import pandas as pd
import talib
from talib import MA_Type

from ibapi import client, wrapper, common, tag_value
from . import objects


class Client(client.EClient, wrapper.EWrapper):
    on_specific_bar_time: bool = False

    def __init__(
        self,
        host: str,
        port: int,
        request_id_to_symbol: dict[int, objects.Stock],
        symbols_to_collect_queue: queue.Queue,
        bars_ready_to_analyze_queue: queue.Queue,
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
        self.request_id_to_symbol = request_id_to_symbol
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.relevant_symbols: list[str] = []

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
        print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}")

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
            tag_value.TagValue("changePercAbove", "30")
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
        if contractDetails.stockType != "ETF":
            if contractDetails.contract.symbol not in self.relevant_symbols:
                print(f"New symbol!! name: {contractDetails.contract.symbol}. type: {contractDetails.stockType}. request_id: {reqId}.")
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
            reverse=True,
        )
        for i, bar_object in enumerate(bars):
            bar_object.index = i

        bars = sorted(
            [bar_object for bar_object in bars],
            key=lambda bar: bar.bar_time,
        )

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
        end_time_str = ""
        keep_up_to_date = True
        if specific_bar_time is not None:
            end_time = (specific_bar_time + datetime.timedelta(days=1)).strftime("%Y%m%d %H:%M:%S")
            end_time_str = f"{end_time} US/Eastern"
            keep_up_to_date = False

        self.reqHistoricalData(
            reqId=request_id,
            contract=contract,
            endDateTime=end_time_str,
            durationStr="1 W",
            barSizeSetting=f"{timeframe} mins",
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
            (now.day != bar_time.day and bar_time.hour < 16 and not self.on_specific_bar_time)
            or bar.volume == 0.0
        ):
            return

        self.request_id_to_symbol[reqId].bars.append(
            objects.BarData(
                open_value=bar.open,
                close=bar.close,
                high=bar.high,
                low=bar.low,
                volume=float(bar.volume),
                vwap=float(bar.wap),
                bar_time=bar_time,
            )
        )

    def historicalDataEnd(
        self,
        reqId: int,
        start: str,
        end: str,
    ):
        relevant_symbol_bars = self.request_id_to_symbol[reqId].bars
        symbol = self.request_id_to_symbol[reqId].symbol_name
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        self.request_id_to_symbol[reqId].bars = bars_data
        self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[reqId])
        print(f"symbol: {symbol}. request_id: {reqId}. finished to get data.")

    def historicalDataUpdate(
        self,
        reqId: int,
        bar: common.BarData,
    ):
        relevant_symbol_bars = self.request_id_to_symbol[reqId].bars
        current_bar_time = datetime.datetime.fromtimestamp(float(bar.date))
        current_bar = objects.BarData(
            open_value=bar.open,
            close=bar.close,
            high=bar.high,
            low=bar.low,
            volume=bar.volume,
            vwap=bar.wap,
            bar_time=current_bar_time,
        )

        if (current_bar_time - relevant_symbol_bars[-1].bar_time).seconds >= 30:
            if relevant_symbol_bars[-1].bar_time == current_bar_time:
                relevant_symbol_bars[-1] = current_bar
            else:
                relevant_symbol_bars.append(current_bar)

            bars_data = self.enrich_bars(
                bars=relevant_symbol_bars,
            )
            self.request_id_to_symbol[reqId].bars = bars_data
            self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[reqId])
