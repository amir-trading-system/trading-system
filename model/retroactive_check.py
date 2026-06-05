import datetime
import os
import sys
import threading
import time
import queue

import tqdm

import analyzer
import buying_confirmator
import common
import collector
import logger
from scripts import stock_finder
import tws

LOGS_PATH = "logs/app.log"
app_logger = logger.logger.Logger(
    enable_stdout=False,
)

#pylint:disable=unspecified-encoding
def wait_for_process_to_finish(
    symbols_data: list[dict[str, str]],
    counter: list[int],
):
    t = tqdm.tqdm(total=len(symbols_data))

    while True:
        while any(
            s_data
            for s_data in symbols_data
            if s_data["result"] != "done"
            and s_data["result"] != "failed"
        ):
            for symbol_data in sorted(
                symbols_data,
                key=lambda symbol_data: symbol_data["symbol"],
            ):
                result = symbol_data["result"]

                actual_confirmation_bar_time = symbol_data["actual_confirmation_bar_time"]

                if (
                    True
                    and result != "done"
                    and result != "failed"
                    and float(symbol_data["score"]) > 0
                    and actual_confirmation_bar_time != "in_progress"
                ):
                    t.update(1)
                    counter[0] -= 1

            time.sleep(2)

        t.close()

def wait_for_collection_and_analysis_only(
    symbols_data: list[dict[str,any]],
    request_id_to_symbol: dict[int,common.objects.Stock],
):
    t = tqdm.tqdm(iterable=symbols_data)
    already_finished: list[str] = []
    while any(
        symbol_data
        for symbol_data in symbols_data
        if symbol_data["analysis_status"] == "in_progress"
    ):
        for _, symbol in request_id_to_symbol.items():
            key = f"{symbol.symbol_name}-{symbol.expected_bar_time}"
            if key in already_finished:
                continue

            finished_analysis = len([
                symbol_obj
                for symbol_obj in request_id_to_symbol.values()
                if symbol_obj.symbol_name == symbol.symbol_name
                and symbol_obj.expected_bar_time == symbol.expected_bar_time
                and symbol_obj.finished_analyze
            ]) == 2
            relevant_symbol_data = [
                symbol_data
                for symbol_data in symbols_data
                if symbol_data["symbol"] == symbol.symbol_name
                and symbol_data["original_bar_time"] == symbol.specific_bar_time
                and symbol_data["expected_confirmation_bar_time"] == symbol.expected_bar_time
            ][0]
            if finished_analysis and relevant_symbol_data["analysis_status"] != "done":
                relevant_symbol_data["analysis_status"] = "done"
                already_finished.append(key)
                t.update(1)

def wait_for_collection_and_analysis(
    symbols_data: list[dict[str,any]],
    request_id_to_symbol: dict[int,common.objects.Stock],
):
    already_finished: list[str] = []
    while any(
        symbol_data
        for symbol_data in symbols_data
        if symbol_data["actual_confirmation_bar_time"] == "in_progress"
    ):
        for _, symbol in request_id_to_symbol.items():
            key = f"{symbol.symbol_name}-{symbol.expected_bar_time}"
            if key in already_finished:
                continue

            finished_collection = len([
                symbol_obj
                for symbol_obj in request_id_to_symbol.values()
                if symbol_obj.symbol_name == symbol.symbol_name
                and symbol_obj.expected_bar_time == symbol.expected_bar_time
                and symbol_obj.finished_collection
            ]) == 2

            finished_analysis = len([
                symbol_obj
                for symbol_obj in request_id_to_symbol.values()
                if symbol_obj.symbol_name == symbol.symbol_name
                and symbol_obj.expected_bar_time == symbol.expected_bar_time
                and symbol_obj.finished_analyze
            ]) == 2

            relevant_symbol_data = [
                symbol_data
                for symbol_data in symbols_data
                if symbol_data["symbol"] == symbol.symbol_name
                and symbol_data["original_bar_time"] == symbol.specific_bar_time
            ][0]
            if finished_collection and relevant_symbol_data["collection_status"] != "done":
                relevant_symbol_data["collection_status"] = "done"
            if finished_analysis and relevant_symbol_data["analysis_status"] != "done":
                relevant_symbol_data["analysis_status"] = "done"

            if (
                True
                and finished_collection
                and finished_analysis
                and symbol.is_day_timeframe()
                and not symbol.is_worth_to_monitor()
            ):
                relevant_symbol_data["actual_confirmation_bar_time"] = "Does not qualify"

            if (
                relevant_symbol_data["collection_status"] == "done"
                and relevant_symbol_data["analysis_status"] == "done"
            ):
                already_finished.append(key)

def wait_for_confirmation(
    results_queue: queue.Queue[dict[str,any]],
    symbols_data: list[dict[str,any]],
):
    while True:
        confirmation_result = results_queue.get()
        relevant_symbol_data = [
            symbol_data
            for symbol_data in symbols_data
            if symbol_data["symbol"] == confirmation_result["symbol"]
            and symbol_data["original_bar_time"] == confirmation_result["original_bar_time"]
        ]

        if relevant_symbol_data:
            relevant_symbol_data[0]["actual_confirmation_bar_time"] = confirmation_result["confirmation_bar_time"]
            relevant_symbol_data[0]["bar_to_place_order_time"] = confirmation_result["bar_to_place_order_time"]
            relevant_symbol_data[0]["collection_status"] = "done"
            relevant_symbol_data[0]["analysis_status"] = "done"
            relevant_symbol_data[0]["score"] = confirmation_result["score"]
            relevant_symbol_data[0]["price_movement_statistics"] = confirmation_result.get("price_movement_statistics", {})
            continue

        symbols_data.append(
            {
                "symbol": confirmation_result["symbol"],
                "collection_status": "done",
                "analysis_status": "done",
                "original_bar_time": confirmation_result["original_bar_time"],
                "actual_confirmation_bar_time": confirmation_result["confirmation_bar_time"],
                "expected_confirmation_bar_time": confirmation_result["confirmation_bar_time"],
                "bar_to_place_order_time": confirmation_result["bar_to_place_order_time"],
                "is_new": True,
                "price_movement_statistics": confirmation_result["price_movement_statistics"],
                "score": confirmation_result["score"],
                "result": "in_progress",
            },
        )

def flush_logs():
    last_time_flushed = datetime.datetime.now()

    while True:
        now = datetime.datetime.now()
        if now - datetime.timedelta(
            seconds=10,
        ) > last_time_flushed:
            app_logger.elastic_handler.flush_logs()
            last_time_flushed = datetime.datetime.now()
        else:
            time.sleep(1)

def explore_past_potential_symbols() -> list[common.objects.SymbolTest]:
    symbols: list[common.objects.SymbolTest] = []
    for symbol, dates in stock_finder.get_dynamic_symbols_data_from_period(
        period="5d",
    ).items():
        for date in dates:
            symbols.append(
                common.objects.SymbolTest(
                    name=symbol,
                    datetime_str=date,
                )
            )

    return symbols

def run_retroactive_check():
    should_run_model = True
    get_only_statistics = False
    symbols_data = []
    symbols = [
        common.objects.SymbolTest(
            name="CODX",
            datetime_str="05.22.26T11:44:00",
            is_positive=False,
        ),
    ]
    # symbols = explore_past_potential_symbols()

    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[dict[str, common.objects.BarData|common.objects.Milestones]] = queue.Queue()
    results_queue: queue.Queue[dict[str,any]] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}

    logger_object = app_logger.get_logger()
    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        client_id=1,
        is_retro=True,
    )

    threading.Thread(
        target=flush_logs,
    ).start()

    threading.Thread(
        target=tws_client.run
    ).start()
    time.sleep(1)

    tws_client.data_streamer.on_specific_bar_time = True
    collector_object = collector.collector.Collector(
        tws_client=tws_client,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )

    analyzer_object = analyzer.analyzer.Analyzer(
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        request_id_to_symbol=request_id_to_symbol,
        tws_client=tws_client,
        logger=logger_object,
        get_only_statistics=get_only_statistics,
    )
    counter = [len(symbols)]

    if not get_only_statistics:
        confirmator_object = buying_confirmator.confirmator.Confirmator(
            tws_client=tws_client,
            waiting_for_confirmation_queue=waiting_for_confirmation_queue,
            results_queue=results_queue,
            request_id_to_symbol=request_id_to_symbol,
            logger=logger_object,
            should_run_model=should_run_model,
            is_retro=True,
        )

        threading.Thread(
            target=confirmator_object.confirm_data,
        ).start()

        threading.Thread(
            target=wait_for_collection_and_analysis,
            kwargs={
                "symbols_data": symbols_data,
                "request_id_to_symbol": request_id_to_symbol,
            }
        ).start()

        threading.Thread(
            target=wait_for_confirmation,
            kwargs={
                "results_queue": results_queue,
                "symbols_data": symbols_data,
            },
        ).start()

        threading.Thread(
            target=wait_for_process_to_finish,
            kwargs={
                "symbols_data": symbols_data,
                "counter": counter,
            },
        ).start()

    for symbol in symbols:
        specific_bar_time = symbol.date_time.replace(hour=0, minute=0)
        collector_object.collect_data_retroactively(
            symbol=symbol.name,
            manual_timeframe_for_tests=common.objects.TimeframeInput(
                timeframe=1,
                timeframe_type=common.objects.TimeframeType(2),
            ),
            specific_bar_time=specific_bar_time,
            expected_bar_time=symbol.date_time,
            is_positive=symbol.is_positive,
        )
        threading.Thread(
            target=analyzer_object.analyze_data,
            kwargs={
                "is_retro": True,
            },
        ).start()

        symbols_data.append(
            {
                "symbol": symbol.name,
                "collection_status": "in_progress",
                "analysis_status": "in_progress",
                "original_bar_time": specific_bar_time,
                "actual_confirmation_bar_time": "in_progress",
                "expected_confirmation_bar_time": symbol.date_time,
                "bar_to_place_order_time": "in_progress",
                "is_new": False,
                "price_movement_statistics": {},
                "result": "in_progress",
                "is_positive": symbol.is_positive,
                "score": 0,
            },
        )

    if get_only_statistics:
        threading.Thread(
            target=wait_for_collection_and_analysis_only,
            kwargs={
                "symbols_data": symbols_data,
                "request_id_to_symbol": request_id_to_symbol,
            },
        ).start()
    else:
        while True:
            if counter[0] == 0:
                break

    sys.exit(0)


if __name__ == "__main__":
    if os.path.exists(LOGS_PATH):
        os.remove(LOGS_PATH)
    run_retroactive_check()
