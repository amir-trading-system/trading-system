import logging
import queue

from ibapi import client, wrapper, tag_value

import alerter


class IbAPIScanner(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
        host: str,
        port: int,
        symbols_to_collect_queue: queue.Queue,
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter,
    ):
        client.EClient.__init__(
            self,
            self,
        )
        self.connect(
            host=host,
            port=port,
            clientId=0,
        )
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.relevant_symbols: list[str] = []
        self.logger = logger
        self.alerter_object = alerter_object
        self.next_id = 1

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
            request_id = self.next_id + 1

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
