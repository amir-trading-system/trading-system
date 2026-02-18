from argparse import ArgumentParser
import datetime
import logging
import os
import threading
import time
import queue

import alerter
import analyzer
import buying_confirmator
import config_manager
import common
import collector
import logger
import tws

#pylint:disable=unspecified-encoding
def initiate_potential_symbols_from_yesterday(
    file_path: str,
    logger_obj: logging.Logger,
    symbols_queue: queue.Queue[str],
):
    lines_to_save: list[str] = []

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            return

    with open(file_path, "r") as f:
        try:
            lines = f.readlines()
            for line in lines:
                [symbol, date] = line.split("--")
                formatted_date = datetime.datetime.fromisoformat(date.replace("\n", ""))
                if (formatted_date + datetime.timedelta(
                    days=1,
                )).day == datetime.datetime.now().day:
                    lines_to_save.append(f"{symbol}--{date}")
                    symbols_queue.put(symbol)
        except FileNotFoundError as e:
            logger_obj.error(
                msg="potential stocks file does not exists",
                extra={
                    "exception": e,
                },
            )

    if lines_to_save:
        with open(file_path, "w") as f:
            f.writelines(lines_to_save)

def run_bot(
    tws_client_obj: tws.client.Client,
    c_obj: collector.collector.Collector,
    a_obj: analyzer.analyzer.Analyzer,
    co_obj: buying_confirmator.confirmator.Confirmator,
    symbol: str = "",
    timeframe: common.objects.TimeframeInput = None,
    specific_bar_time: datetime.datetime = None,
    retroactive_from: datetime.datetime = None,
    confirmator_only: bool = False,
):
    manual_results_for_test = []
    collector_kwargs = {}
    analyzer_kwargs = {}
    tws_client_obj.data_streamer.on_specific_bar_time = specific_bar_time is not None
    tws_client_obj.data_streamer.is_retro = retroactive_from is not None
    a_obj.confirmator_only = confirmator_only

    if symbol:
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

    tws_client_obj.start_scanner(
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
    test_parser.add_argument(
        "--timeframe_type",
        type=int,
    )
    test_parser.add_argument(
        "--confirmator_only",
        action='store_true',
    )

    args = argument_parser.parse_args()
    is_retro = args.command == "test" and (args.retroactive_from is not None or args.specific_bar_time is not None)

    configuration: config_manager.BotConfig = config_manager.ConfigManager().load_config()
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[dict[str, common.objects.BarData|common.objects.Milestones]] = queue.Queue()
    results_queue: queue.Queue[dict[str, any]] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}
    logger_object = logger.logger.Logger(
        enable_stdout=True,
    ).get_logger()

    initiate_potential_symbols_from_yesterday(
        file_path=configuration.potential_symbols_file_path,
        logger_obj=logger_object,
        symbols_queue=symbols_to_collect_queue,
    )
    alerter_object = alerter.alerter.Alerter(
        logger=logger_object,
        configuration=configuration.alerts,
    )
    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        potential_symbols_file_path=configuration.potential_symbols_file_path,
    )
    collector_obj = collector.collector.Collector(
        tws_client=tws_client,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    analyzer_obj = analyzer.analyzer.Analyzer(
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        request_id_to_symbol=request_id_to_symbol,
        alerter_object=alerter_object,
        logger=logger_object,
    )
    confirmator_obj = buying_confirmator.confirmator.Confirmator(
        tws_client=tws_client,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        results_queue=results_queue,
        request_id_to_symbol=request_id_to_symbol,
        alerter_object=alerter_object,
        logger=logger_object,
        is_retro=is_retro,
    )

    threading.Thread(
        target=tws_client.run
    ).start()
    time.sleep(1)

    if args.command == "prod":
        run_bot(
            tws_client_obj=tws_client,
            c_obj=collector_obj,
            a_obj=analyzer_obj,
            co_obj=confirmator_obj,
        )
    else:
        run_bot(
            tws_client_obj=tws_client,
            c_obj=collector_obj,
            a_obj=analyzer_obj,
            co_obj=confirmator_obj,
            symbol=args.symbol,
            timeframe=common.objects.TimeframeInput(
                timeframe=args.timeframe,
                timeframe_type=common.objects.TimeframeType(args.timeframe_type),
            ),
            specific_bar_time=args.specific_bar_time,
            retroactive_from=args.retroactive_from,
            confirmator_only=args.confirmator_only,
        )
