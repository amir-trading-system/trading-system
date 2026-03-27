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

LOGS_PATH = "logs/app.log"
app_logger = logger.logger.Logger(
    enable_stdout=False,
)

class Symbol:
    def __init__(
        self,
        name: str,
        datetime_str: str,
        finished: bool = False,
    ):
        self.name = name
        self.date_time = datetime.datetime.strptime(datetime_str, "%m.%d.%yT%H:%M:%S")
        self.finished = finished

def get_symbols() -> list[Symbol]:
    return [
        Symbol(
            name="EPSM",
            datetime_str="11.20.25T11:06:00",
        ),
        Symbol(
            name="CYCU",
            datetime_str="11.14.25T12:42:00",
        ),
        Symbol(
            name="TWG",
            datetime_str="12.08.25T13:10:00",
        ),
        Symbol(
            name="AFJK",
            datetime_str="12.09.25T14:14:00",
        ),
        Symbol(
            name="QCLS",
            datetime_str="12.04.25T09:43:00",
        ),
        Symbol(
            name="BBGI",
            datetime_str="12.10.25T09:45:00",
        ),
        Symbol(
            name="ASPC",
            datetime_str="12.26.25T12:25:00",
        ),
        Symbol(
            name="INBS",
            datetime_str="01.05.26T12:29:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.14.26T09:51:00",
        ),
        Symbol(
            name="AHMA",
            datetime_str="01.15.26T10:31:00",
        ),
        Symbol(
            name="MLEC",
            datetime_str="01.15.26T11:59:00",
        ),
        Symbol(
            name="NAMM",
            datetime_str="01.22.26T10:30:00",
        ),
        Symbol(
            name="BGL",
            datetime_str="01.22.26T14:24:00",
        ),
        Symbol(
            name="AUST",
            datetime_str="01.23.26T12:45:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.23.26T10:24:00",
        ),
        Symbol(
            name="MBAI",
            datetime_str="01.26.26T10:22:00",
        ),
        Symbol(
            name="DRMA",
            datetime_str="01.26.26T12:19:00",
        ),
        Symbol(
            name="GITS",
            datetime_str="01.27.26T10:05:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.28.26T10:42:00",
        ),
        Symbol(
            name="NAMM",
            datetime_str="01.28.26T14:51:00",
        ),
        Symbol(
            name="FEED",
            datetime_str="01.29.26T09:47:00",
        ),
        Symbol(
            name="CATX",
            datetime_str="01.29.26T11:39:00",
        ),
        Symbol(
            name="ANL",
            datetime_str="01.29.26T15:44:00",
        ),
        Symbol(
            name="FEED",
            datetime_str="01.30.26T09:57:00",
        ),
        Symbol(
            name="CATX",
            datetime_str="02.02.26T10:48:00",
        ),
        Symbol(
            name="QVCGP",
            datetime_str="02.11.26T10:22:00",
        ),
        Symbol(
            name="NCI",
            datetime_str="02.11.26T11:00:00",
        ),
        Symbol(
            name="RIME",
            datetime_str="02.13.26T14:11:00",
        ),
        Symbol(
            name="ATOM",
            datetime_str="02.17.26T12:27:00",
        ),
        Symbol(
            name="MLEC",
            datetime_str="02.18.26T10:09:00",
        ),
        Symbol(
            name="RXT",
            datetime_str="02.19.26T15:12:00",
        ),
        Symbol(
            name="LRMR",
            datetime_str="02.25.26T09:57:00",
        ),
        Symbol(
            name="RXT",
            datetime_str="02.26.26T10:55:00",
        ),
        Symbol(
            name="AEHL",
            datetime_str="02.26.26T11:36:00",
        ),
        Symbol(
            name="EDSA",
            datetime_str="03.03.26T11:41:00",
        ),
        Symbol(
            name="BATL",
            datetime_str="03.04.26T11:27:00",
        ),
        Symbol(
            name="BATL",
            datetime_str="03.05.26T10:10:00",
        ),
        Symbol(
            name="TPET",
            datetime_str="03.05.26T09:45:00",
        ),
        Symbol(
            name="DXST",
            datetime_str="03.06.26T10:40:00",
        ),
        Symbol(
            name="EDSA",
            datetime_str="03.06.26T11:12:00",
        ),
        Symbol(
            name="EDSA",
            datetime_str="03.09.26T11:08:00",
        ),
        Symbol(
            name="ANTX",
            datetime_str="03.09.26T11:57:00",
        ),
        Symbol(
            name="ACXP",
            datetime_str="03.11.26T10:03:00",
        ),
        Symbol(
            name="AIFF",
            datetime_str="03.13.26T10:24:00",
        ),
        Symbol(
            name="PRSO",
            datetime_str="03.16.26T14:49:00",
        ),
        Symbol(
            name="BIAF",
            datetime_str="03.17.26T09:35:00",
        ),
        Symbol(
            name="ACXP",
            datetime_str="03.19.26T10:12:00",
        ),
        Symbol(
            name="ANNA",
            datetime_str="03.20.26T10:02:00",
        ),
        Symbol(
            name="BIAF",
            datetime_str="03.23.26T10:45:00",
        ),
        Symbol(
            name="EEIQ",
            datetime_str="03.26.26T09:59:00",
        ),
    ]

#pylint:disable=unspecified-encoding
def write_to_csv(
    symbols_data: list[dict[str, str]],
    file_name: str,
    counter: list[int],
):
    t = tqdm.tqdm(total=len(symbols_data))
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
                "feature_has_positive_more_than_negative_bars",
                "feature_has_more_positive_volume_than_negative",
                "feature_open_close_to_ema_9",
                "feature_most_of_bars_above_vwap",
                "feature_pullback_sharpness",
                "feature_pullback_depth",
                "feature_number_of_negative_bars_in_pullback_pct",
                "feature_price_minus_vwap_at_entry",
                "feature_pullback_to_trend_ratio",
                "feature_histogram_negative_momentum_pct",
                "feature_strong_positive_bars_with_full_body_pct",
                "feature_minutes_since_market_open_to_total_market_minutes_pct",
                "feature_bars_with_at_least_50_pct_wick_pct",
                "feature_bars_with_lower_volume_average_pct",
                "feature_volume_sum_since_market_open",
                "feature_volume_per_minute",
                "feature_volume_average",
                "feature_bar_volume",
                "feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open",
                "feature_highest_volume_before_to_entry_bar_volume_ratio",
                "feature_highest_average_volume_before_to_entry_bar_average_volume_ratio",
                "feature_highest_average_volume_before_to_entry_bar_volume_ratio",
                "feature_macd_under_signal_line_counter",
                "feature_entry_bar_strengh_pct",
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
                feature_has_positive_more_than_negative_bars = False
                feature_has_more_positive_volume_than_negative = False
                feature_open_close_to_ema_9 = False
                feature_most_of_bars_above_vwap = False
                feature_pullback_sharpness = 0
                feature_pullback_depth = 0
                feature_number_of_negative_bars_in_pullback_pct = 0
                feature_price_minus_vwap_at_entry = 0
                feature_pullback_to_trend_ratio = 0
                feature_histogram_negative_momentum_pct = 0
                feature_strong_positive_bars_with_full_body_pct = 0
                feature_minutes_since_market_open_to_total_market_minutes_pct = 0
                feature_bars_with_at_least_50_pct_wick_pct = 0
                feature_bars_with_lower_volume_average_pct = 0
                feature_volume_sum_since_market_open = 0
                feature_volume_per_minute = 0
                feature_volume_average = 0
                feature_bar_volume = 0
                feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = False
                feature_highest_volume_before_to_entry_bar_volume_ratio = 0
                feature_highest_average_volume_before_to_entry_bar_average_volume_ratio = 0
                feature_highest_average_volume_before_to_entry_bar_volume_ratio = 0
                feature_macd_under_signal_line_counter = 0
                feature_entry_bar_strengh_pct = 0

                price_movement_statistics = symbol_data.get("price_movement_statistics", None)
                if price_movement_statistics:
                    feature_has_positive_more_than_negative_bars = price_movement_statistics["feature_has_positive_more_than_negative_bars"]
                    feature_has_more_positive_volume_than_negative = price_movement_statistics["feature_has_more_positive_volume_than_negative"]
                    feature_open_close_to_ema_9 = price_movement_statistics["feature_open_close_to_ema_9"]
                    feature_most_of_bars_above_vwap = price_movement_statistics["feature_most_of_bars_above_vwap"]
                    feature_pullback_sharpness = price_movement_statistics["feature_pullback_sharpness"]
                    feature_pullback_depth = price_movement_statistics["feature_pullback_depth"]
                    feature_number_of_negative_bars_in_pullback_pct = price_movement_statistics["feature_number_of_negative_bars_in_pullback_pct"]
                    feature_price_minus_vwap_at_entry = price_movement_statistics["feature_price_minus_vwap_at_entry"]
                    feature_pullback_to_trend_ratio = price_movement_statistics["feature_pullback_to_trend_ratio"]
                    feature_histogram_negative_momentum_pct = price_movement_statistics["feature_histogram_negative_momentum_pct"]
                    feature_strong_positive_bars_with_full_body_pct = price_movement_statistics["feature_strong_positive_bars_with_full_body_pct"]
                    feature_minutes_since_market_open_to_total_market_minutes_pct = price_movement_statistics["feature_minutes_since_market_open_to_total_market_minutes_pct"]
                    feature_bars_with_at_least_50_pct_wick_pct = price_movement_statistics["feature_bars_with_at_least_50_pct_wick_pct"]
                    feature_bars_with_lower_volume_average_pct = price_movement_statistics["feature_bars_with_lower_volume_average_pct"]
                    feature_volume_sum_since_market_open = price_movement_statistics["feature_volume_sum_since_market_open"]
                    feature_volume_per_minute = price_movement_statistics["feature_volume_per_minute"]
                    feature_volume_average = price_movement_statistics["feature_volume_average"]
                    feature_bar_volume = price_movement_statistics["feature_bar_volume"]
                    feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = price_movement_statistics["feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open"]
                    feature_highest_volume_before_to_entry_bar_volume_ratio = price_movement_statistics["feature_highest_volume_before_to_entry_bar_volume_ratio"]
                    feature_highest_average_volume_before_to_entry_bar_average_volume_ratio = price_movement_statistics["feature_highest_average_volume_before_to_entry_bar_average_volume_ratio"]
                    feature_highest_average_volume_before_to_entry_bar_volume_ratio = price_movement_statistics["feature_highest_average_volume_before_to_entry_bar_volume_ratio"]
                    feature_macd_under_signal_line_counter = price_movement_statistics["feature_macd_under_signal_line_counter"]
                    feature_entry_bar_strengh_pct = price_movement_statistics["feature_entry_bar_strengh_pct"]

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

                    if not symbol.endswith("NEW"):
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
                                feature_has_positive_more_than_negative_bars,
                                feature_has_more_positive_volume_than_negative,
                                feature_open_close_to_ema_9,
                                feature_most_of_bars_above_vwap,
                                feature_pullback_sharpness,
                                feature_pullback_depth,
                                feature_number_of_negative_bars_in_pullback_pct,
                                feature_price_minus_vwap_at_entry,
                                feature_pullback_to_trend_ratio,
                                feature_histogram_negative_momentum_pct,
                                feature_strong_positive_bars_with_full_body_pct,
                                feature_minutes_since_market_open_to_total_market_minutes_pct,
                                feature_bars_with_at_least_50_pct_wick_pct,
                                feature_bars_with_lower_volume_average_pct,
                                feature_volume_sum_since_market_open,
                                feature_volume_per_minute,
                                feature_volume_average,
                                feature_bar_volume,
                                feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open,
                                feature_highest_volume_before_to_entry_bar_volume_ratio,
                                feature_highest_average_volume_before_to_entry_bar_average_volume_ratio,
                                feature_highest_average_volume_before_to_entry_bar_volume_ratio,
                                feature_macd_under_signal_line_counter,
                                feature_entry_bar_strengh_pct,
                            ]
                        )

                    f.flush()
                    t.update(1)

                    counter[0] -= 1

            time.sleep(2)

    t.close()

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
            if symbol.symbol_name in already_finished:
                continue

            finished_collection = len([
                symbol_obj
                for symbol_obj in request_id_to_symbol.values()
                if symbol_obj.symbol_name == symbol.symbol_name
                and symbol_obj.finished_collection
            ]) == 2

            finished_analysis = len([
                symbol_obj
                for symbol_obj in request_id_to_symbol.values()
                if symbol_obj.symbol_name == symbol.symbol_name
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
                already_finished.append(symbol.symbol_name)

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
            relevant_symbol_data[0]["price_movement_statistics"] = {}
            continue

        for evidence_name in confirmation_result["evidences"]:
            if should_update_first_default and relevant_symbol_data:
                relevant_symbol_data[0]["actual_confirmation_bar_time"] = confirmation_result["confirmation_bar_time"]
                relevant_symbol_data[0]["evidence_name"] = evidence_name
                relevant_symbol_data[0]["collection_status"] = "done"
                relevant_symbol_data[0]["analysis_status"] = "done"
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

def explore_past_potential_symbols() -> list[Symbol]:
    symbols = [
        Symbol(
            name=symbol,
            datetime_str=date,
        )
        for symbol, date in stock_finder.get_dynamic_symbols_data_from_period(
            period="5mo",
        ).items()
    ]

    current_symbols = get_symbols()
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
    for_positive_results = True
    should_run_model = True
    for_test_real_case = False
    symbols_data = []
    symbols = []
    output_file_name = "model/real_case_result.csv"
    # symbols = explore_past_potential_symbols()

    if not for_test_real_case:
        should_run_model = False
        if for_positive_results:
            symbols = get_symbols()
            output_file_name = "model/positive_results.csv"
        else:
            symbols = [
                Symbol(
                    name="HBIO",
                    datetime_str="10.30.25T09:52:00",
                ),
                Symbol(
                    name="FLYE",
                    datetime_str="12.01.25T10:52:00",
                ),
                Symbol(
                    name="JXG",
                    datetime_str="12.09.25T15:45:00",
                ),
                Symbol(
                    name="VMAR",
                    datetime_str="12.16.25T10:17:00",
                ),
                Symbol(
                    name="NBY",
                    datetime_str="01.09.26T15:50:00",
                ),
                Symbol(
                    name="LVLU",
                    datetime_str="01.12.26T11:23:00",
                ),
                Symbol(
                    name="EVTV",
                    datetime_str="01.13.26T12:49:00",
                ),
                Symbol(
                    name="CJMB",
                    datetime_str="01.15.26T11:26:00",
                ),
                Symbol(
                    name="XTKG",
                    datetime_str="01.26.26T14:11:00",
                ),
                Symbol(
                    name="MOVE",
                    datetime_str="01.27.26T10:04:00",
                ),
                Symbol(
                    name="ONEG",
                    datetime_str="01.27.26T10:14:00",
                ),
                Symbol(
                    name="XHLD",
                    datetime_str="01.27.26T15:36:00",
                ),
                Symbol(
                    name="JLHL",
                    datetime_str="02.02.26T10:46:00",
                ),
                Symbol(
                    name="SORA",
                    datetime_str="02.02.26T15:19:00",
                ),
                Symbol(
                    name="SMX",
                    datetime_str="02.06.26T10:16:00",
                ),
                Symbol(
                    name="JDZG",
                    datetime_str="02.13.26T11:50:00",
                ),
                Symbol(
                    name="CDIO",
                    datetime_str="02.18.26T14:18:00",
                ),
                Symbol(
                    name="BIYA",
                    datetime_str="02.20.26T10:49:00",
                ),
                Symbol(
                    name="NCI",
                    datetime_str="02.23.26T14:19:00",
                ),
                Symbol(
                    name="TURB",
                    datetime_str="03.05.26T12:07:00",
                ),
                Symbol(
                    name="CAMP",
                    datetime_str="03.09.26T13:51:00",
                ),
                Symbol(
                    name="PLYX",
                    datetime_str="03.10.26T14:06:00",
                ),
                Symbol(
                    name="ANTX",
                    datetime_str="03.12.26T14:35:00",
                ),
                Symbol(
                    name="ALTO",
                    datetime_str="03.12.26T10:35:00",
                ),
                Symbol(
                    name="LWLG",
                    datetime_str="03.13.26T15:03:00",
                ),
                Symbol(
                    name="TLYS",
                    datetime_str="03.13.26T13:41:00",
                ),
                Symbol(
                    name="TWAV",
                    datetime_str="03.16.26T10:55:00",
                ),
                Symbol(
                    name="QCLS",
                    datetime_str="03.18.26T11:30:00",
                ),
            ]
            output_file_name = "model/false_positive_results.csv"

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
    )
    # analyzer_object.confirmator_only = True

    confirmator_object = buying_confirmator.confirmator.Confirmator(
        tws_client=tws_client,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        results_queue=results_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        should_run_model=should_run_model,
        is_retro=True,
        # confirmation_only=True,
    )

    threading.Thread(
        target=analyzer_object.analyze_data,
        kwargs={
            "is_retro": True,
        },
    ).start()

    threading.Thread(
        target=confirmator_object.confirm_data,
    ).start()

    counter = [len(symbols)]

    for symbol in symbols:
        specific_bar_time = symbol.date_time.replace(hour=0, minute=0)
        collector_object.collect_data_retroactively(
            symbol=symbol.name,
            manual_timeframe_for_tests=common.objects.TimeframeInput(
                timeframe=1,
                timeframe_type=common.objects.TimeframeType(2),
            ),
            specific_bar_time=specific_bar_time,
        )
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
            },
        )

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
            "file_name": output_file_name,
            "counter": counter,
        },
    ).start()

    while True:
        if counter[0] == 0:
            break

    sys.exit(0)


if __name__ == "__main__":
    if os.path.exists(LOGS_PATH):
        os.remove(LOGS_PATH)
    run_retroactive_check()
