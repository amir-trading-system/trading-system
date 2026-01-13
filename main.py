from  argparse import ArgumentParser
import datetime
import threading
import time
import queue

import alerter
import analyzer
import buying_confirmator
import collector
import logger
import tws

def run_bot(
    c_obj: collector.collector.Collector,
    a_obj: analyzer.analyzer.Analyzer,
    co_obj: buying_confirmator.confirmator.Confirmator,
    symbol: str = None,
    timeframe: int = None,
    specific_bar_time: datetime.datetime = None,
    retroactive_from: datetime.datetime = None,
):
    manual_results_for_test = []
    collector_kwargs = {}
    analyzer_kwargs = {}
    c_obj.tws_client.on_specific_bar_time = specific_bar_time is not None
    c_obj.tws_client.is_retro = retroactive_from is not None

    if symbol is not None:
        manual_results_for_test = [str.upper(symbol)]

        if specific_bar_time:
            collector_kwargs = {
                "manual_timeframe_for_tests": timeframe,
                "specific_bar_time": specific_bar_time,
            }
            analyzer_kwargs = {
                "specific_bar_time": specific_bar_time,
            }
        if retroactive_from:
            collector_kwargs = {
                "manual_timeframe_for_tests": timeframe,
                "specific_bar_time": retroactive_from,
            }
            analyzer_kwargs = {
                "retroactive_from": retroactive_from,
            }

    c_obj.tws_client.start_scanner(
        manual_results_for_test=manual_results_for_test,
    )

    threading.Thread(
        target=c_obj.collect_data,
        kwargs=collector_kwargs,
    ).start()

    threading.Thread(
        target=a_obj.analyze_data,
        kwargs=analyzer_kwargs,
    ).start()

    threading.Thread(
        target=co_obj.confirm_data,
    ).start()

if __name__ == "__main__":
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[tws.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[tws.objects.BarData] = queue.Queue()
    request_id_to_symbol: dict[int,tws.objects.Stock] = {}
    ibapi_requests: list[tws.objects.IbAPIRequest] = []
    logger_object = logger.logger.Logger()
    logger_object = logger_object.get_logger()

    alerter_object = alerter.alerter.Alerter(
        logger=logger_object,
    )
    collector_obj = collector.collector.Collector(
        tws_host="localhost",
        tws_port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        ibapi_requests=ibapi_requests,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        alerter_object=alerter_object,
    )
    analyzer_obj = analyzer.analyzer.Analyzer(
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        alerter_object=alerter_object,
        logger=logger_object,
    )
    confirmator_obj = buying_confirmator.confirmator.Confirmator(
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        request_id_to_symbol=request_id_to_symbol,
        ibapi_requests=ibapi_requests,
        alerter_object=alerter_object,
        logger=logger_object,
    )

    argument_parser = ArgumentParser()
    subparser = argument_parser.add_subparsers(
        dest="command",
    )
    test_parser = subparser.add_parser(
        "test"
    )
    prod_parser = subparser.add_parser(
        "prod"
    )
    test_parser.add_argument(
        "--symbol",
        type=str,
    )
    test_parser.add_argument(
        "--specific_bar_time",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
        default=None,
    )
    test_parser.add_argument(
        "--retroactive_from",
        type=datetime.date.fromisoformat,
        default=None,
    )
    test_parser.add_argument(
        "--timeframe",
        type=int,
    )

    args = argument_parser.parse_args()

    threading.Thread(
        target=collector_obj.tws_client.run
    ).start()
    time.sleep(1)

    if args.command == "prod":
        run_bot(
            c_obj=collector_obj,
            a_obj=analyzer_obj,
            co_obj=confirmator_obj,
        )
    else:
        run_bot(
            c_obj=collector_obj,
            a_obj=analyzer_obj,
            co_obj=confirmator_obj,
            symbol=args.symbol,
            timeframe=args.timeframe,
            specific_bar_time=args.specific_bar_time,
            retroactive_from=args.retroactive_from,
        )
