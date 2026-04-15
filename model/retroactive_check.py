import csv
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

from . import training

LOGS_PATH = "logs/app.log"
app_logger = logger.logger.Logger(
    enable_stdout=False,
)

#pylint:disable=unspecified-encoding
def write_to_csv(
    symbols_data: list[dict[str, str]],
    original_file_name: str,
    counter: list[int],
    get_only_statistics: bool,
):
    file_names = [
        "model/positive_results.csv",
        "model/false_positive_results.csv",
    ]
    if original_file_name != "":
        file_names = [original_file_name]
    t = tqdm.tqdm(total=len(symbols_data))
    if not get_only_statistics:
        for file_name in file_names:
            with open(file_name, mode="w") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "symbol",
                        "original_bar_time",
                        "collection_status",
                        "analysis_status",
                        "actual_confirmation_bar_time",
                        "expected_confirmation_bar_time",
                        "evidence",
                        "result",
                        "feature_bars_with_at_least_50_pct_wick_pct",
                        "feature_positive_vs_negative_volume",
                        "feature_overlapped_bars_since_market_open_pct",
                        "feature_crossed_highest_high",
                        "feature_distance_from_highest_high_since_market_open",
                        "feature_entry_bar_lowest_wick_to_bar_body_pct",
                        "feature_entry_bar_volume",
                        "feature_entry_volume_vs_total_volume",
                        "feature_distance_from_highest_high",
                        "feature_bars_with_rejection_since_market_open",
                        "feature_entry_point_size_to_bars_size_average",
                        "feature_histogram_changed_directions_pct",
                        "feature_strong_negative_bars_pct",
                        "feature_price_action_is_stuck_pct",
                        "feature_entry_bar_close_to_crossed_highest_high_pct",
                        "feature_total_volume",
                        "feature_current_macd_to_previous",
                        "feature_entry_bar_shape_is_good",
                        "score",
                    ],
                )
                f.flush()

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
            symbol = symbol_data["symbol"]
            original_bar_time = symbol_data["original_bar_time"]
            result = symbol_data["result"]
            feature_bars_with_at_least_50_pct_wick_pct = 0
            feature_positive_vs_negative_volume = 0
            feature_overlapped_bars_since_market_open_pct = 0
            feature_crossed_highest_high = 0
            feature_distance_from_highest_high_since_market_open = 0
            feature_entry_bar_lowest_wick_to_bar_body_pct = 0
            feature_entry_bar_volume = 0
            feature_entry_volume_vs_total_volume = 0
            feature_distance_from_highest_high = 0
            feature_bars_with_rejection_since_market_open = 0
            feature_entry_point_size_to_bars_size_average = 0
            feature_histogram_changed_directions_pct = 0
            feature_strong_negative_bars_pct = 0
            feature_price_action_is_stuck_pct = 0
            feature_entry_bar_close_to_crossed_highest_high_pct = 0
            feature_total_volume = 0
            feature_current_macd_to_previous = 0
            feature_entry_bar_shape_is_good = 0

            price_movement_statistics = symbol_data.get("price_movement_statistics", None)
            if price_movement_statistics:
                feature_bars_with_at_least_50_pct_wick_pct = price_movement_statistics["feature_bars_with_at_least_50_pct_wick_pct"]
                feature_positive_vs_negative_volume = price_movement_statistics["feature_positive_vs_negative_volume"]
                feature_overlapped_bars_since_market_open_pct = price_movement_statistics["feature_overlapped_bars_since_market_open_pct"]
                feature_crossed_highest_high = price_movement_statistics["feature_crossed_highest_high"]
                feature_distance_from_highest_high_since_market_open = price_movement_statistics["feature_distance_from_highest_high_since_market_open"]
                feature_entry_bar_lowest_wick_to_bar_body_pct = price_movement_statistics["feature_entry_bar_lowest_wick_to_bar_body_pct"]
                feature_entry_bar_volume = price_movement_statistics["feature_entry_bar_volume"]
                feature_entry_volume_vs_total_volume = price_movement_statistics["feature_entry_volume_vs_total_volume"]
                feature_distance_from_highest_high = price_movement_statistics["feature_distance_from_highest_high"]
                feature_bars_with_rejection_since_market_open = price_movement_statistics["feature_bars_with_rejection_since_market_open"]
                feature_entry_point_size_to_bars_size_average = price_movement_statistics["feature_entry_point_size_to_bars_size_average"]
                feature_histogram_changed_directions_pct = price_movement_statistics["feature_histogram_changed_directions_pct"]
                feature_strong_negative_bars_pct = price_movement_statistics["feature_strong_negative_bars_pct"]
                feature_price_action_is_stuck_pct = price_movement_statistics["feature_price_action_is_stuck_pct"]
                feature_entry_bar_close_to_crossed_highest_high_pct = price_movement_statistics["feature_entry_bar_close_to_crossed_highest_high_pct"]
                feature_total_volume = price_movement_statistics["feature_total_volume"]
                feature_current_macd_to_previous = price_movement_statistics["feature_current_macd_to_previous"]
                feature_entry_bar_shape_is_good = price_movement_statistics["feature_entry_bar_shape_is_good"]

            collection_status = symbol_data["collection_status"]
            analysis_status = symbol_data["analysis_status"]

            evidence_name = symbol_data["evidence_name"]
            if symbol_data["is_new"]:
                evidence_name = f"{evidence_name} - NEW"
                symbol = f"{symbol} - NEW"

            actual_confirmation_bar_time = symbol_data["actual_confirmation_bar_time"]
            expected_confirmation_bar_time = symbol_data["expected_confirmation_bar_time"]

            if (
                True
                and result != "done"
                and result != "failed"
                and collection_status == "done"
                and analysis_status == "done"
                and actual_confirmation_bar_time != "in_progress"
            ):
                if actual_confirmation_bar_time == expected_confirmation_bar_time or evidence_name == "no evidence":
                    result = "done"
                    symbol_data["result"] = "done"
                else:
                    result = "failed"
                    symbol_data["result"] = "failed"

                if not symbol.endswith("NEW") and evidence_name != "no evidence":
                    file_name = "model/positive_results.csv"
                    if not symbol_data["is_positive"]:
                        file_name = "model/false_positive_results.csv"
                    if original_file_name != "":
                        file_name = original_file_name

                    if not get_only_statistics:
                        with open(file_name, mode="a") as f:
                            writer = csv.writer(f)
                            writer.writerow(
                                [
                                    symbol,
                                    original_bar_time,
                                    collection_status,
                                    analysis_status,
                                    actual_confirmation_bar_time,
                                    expected_confirmation_bar_time,
                                    evidence_name,
                                    result,
                                    feature_bars_with_at_least_50_pct_wick_pct,
                                    feature_positive_vs_negative_volume,
                                    feature_overlapped_bars_since_market_open_pct,
                                    feature_crossed_highest_high,
                                    feature_distance_from_highest_high_since_market_open,
                                    feature_entry_bar_lowest_wick_to_bar_body_pct,
                                    feature_entry_bar_volume,
                                    feature_entry_volume_vs_total_volume,
                                    feature_distance_from_highest_high,
                                    feature_bars_with_rejection_since_market_open,
                                    feature_entry_point_size_to_bars_size_average,
                                    feature_histogram_changed_directions_pct,
                                    feature_strong_negative_bars_pct,
                                    feature_price_action_is_stuck_pct,
                                    feature_entry_bar_close_to_crossed_highest_high_pct,
                                    feature_total_volume,
                                    feature_current_macd_to_previous,
                                    feature_entry_bar_shape_is_good,
                                    symbol_data["score"],
                                ]
                            )

                            f.flush()
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
                relevant_symbol_data["evidence_name"] = "Does not qualify"

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
            and symbol_data["evidence_name"] == "in_progress"
        ]
        should_update_first_default = True

        if not confirmation_result["evidences"]:
            relevant_symbol_data[0]["actual_confirmation_bar_time"] = confirmation_result["confirmation_bar_time"]
            relevant_symbol_data[0]["evidence_name"] = "no evidence"
            relevant_symbol_data[0]["collection_status"] = "done"
            relevant_symbol_data[0]["analysis_status"] = "done"
            relevant_symbol_data[0]["score"] = confirmation_result["score"]
            relevant_symbol_data[0]["price_movement_statistics"] = confirmation_result.get("price_movement_statistics", {})
            continue

        for evidence_name in confirmation_result["evidences"]:
            if should_update_first_default and relevant_symbol_data:
                relevant_symbol_data[0]["actual_confirmation_bar_time"] = confirmation_result["confirmation_bar_time"]
                relevant_symbol_data[0]["evidence_name"] = evidence_name
                relevant_symbol_data[0]["collection_status"] = "done"
                relevant_symbol_data[0]["analysis_status"] = "done"
                relevant_symbol_data[0]["score"] = confirmation_result["score"]
                relevant_symbol_data[0]["price_movement_statistics"] = confirmation_result["price_movement_statistics"]
                should_update_first_default = False
                continue

            symbols_data.append(
                {
                    "symbol": confirmation_result["symbol"],
                    "collection_status": "done",
                    "analysis_status": "done",
                    "original_bar_time": confirmation_result["original_bar_time"],
                    "actual_confirmation_bar_time": confirmation_result["confirmation_bar_time"],
                    "expected_confirmation_bar_time": confirmation_result["confirmation_bar_time"],
                    "evidence_name": evidence_name,
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
    symbols = [
        common.objects.SymbolTest(
            name=symbol,
            datetime_str=date,
        )
        for symbol, date in stock_finder.get_dynamic_symbols_data_from_period(
            period="4mo",
        ).items()
    ]

    current_symbols = [
        symbol
        for symbol in training.train_data.get_tagged_data()
        if symbol.is_positive
    ]
    for symbol in symbols:
        for current_symbol in current_symbols:
            if (
                True
                and symbol.name == current_symbol.name
                and symbol.date_time.year == current_symbol.date_time.year
                and symbol.date_time.month == current_symbol.date_time.month
                and symbol.date_time.day == current_symbol.date_time.day
            ):
                symbol.date_time = current_symbol.date_time

    return symbols

def run_retroactive_check():
    should_run_model = True
    get_only_statistics = False
    symbols_data = []
    symbols = [
        common.objects.SymbolTest(
            name="SIDU",
            datetime_str="04.06.26T10:59:00",
            is_positive=True,
        ),
    ]
    # symbols = explore_past_potential_symbols()
    output_file_name = "model/real_case_result.csv"

    if not symbols:
        output_file_name = ""
        symbols = training.train_data.get_tagged_data()
        get_only_statistics = True
        should_run_model = False

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
            target=write_to_csv,
            kwargs={
                "symbols_data": symbols_data,
                "original_file_name": output_file_name,
                "counter": counter,
                "get_only_statistics": get_only_statistics,
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
                "evidence_name": "in_progress",
                "is_new": False,
                "price_movement_statistics": {},
                "result": "in_progress",
                "is_positive": symbol.is_positive,
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
