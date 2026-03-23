import csv
import datetime
import os
import sys
import threading
import time
import queue

import tqdm

import analyzer
import analyzer.evidences
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
            name="EDSA",
            datetime_str="03.06.26T11:12:00",
        ),
        Symbol(
            name="DTCK",
            datetime_str="03.09.26T10:12:00",
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
                "volume_until_now",
                "result",
                "positive_movement_since_market_open",
                "negative_movement_since_market_open",
                "movement_above_vwap_since_market_open",
                "movement_under_vwap_since_market_open",
                "movement_above_volume_average_counter_since_market_open",
                "movement_under_volume_average_counter_since_market_open",
                "highest_histogram_since_market_open",
                "lowest_histogram_since_market_open",
                "pullback_sharpness",
                "pullback_duration",
                "pullback_depth",
                "histogram_at_entry",
                "price_minus_vwap_at_entry",
                "entry_volume_spike_3",
                "entry_volume_spike_5",
                "minutes_since_market_open",
                "distance_from_recent_high",
                "distance_from_high_of_day",
                "volume_trend",
                "number_of_negative_bars",
                "broke_high_of_day_at_entry",
                "vwap_slope_3",
                "vwap_slope_5",
                "ema9_minus_vwap_at_entry",
                "ema9_minus_ema20_at_entry",
                "number_of_green_bars_last_5",
                "number_of_red_bars_last_5",
                "distance_from_premarket_high",
                "entry_bar_range_pct",
                "entry_bar_body_pct",
                "upper_wick_pct_at_entry",
                "volume_acceleration",
                "extension_vs_pullback",
                "move_efficiency",
                "pullback_to_trend_ratio",
                "trend_cleanliness",
                "pullback_structure_score",
                "volume_confirmation_ratio",
                "volume_trend_strength",
                "volume_during_pullback",
                "relative_position_in_range",
                "distance_from_vwap_normalized",
                "hod_proximity_score",
                "momentum_alignment_score",
                "momentum_strength",
                "entry_conviction_score",
                "entry_efficiency",
                "failed_breakout_risk",
                "late_move_indicator",
                "early_vs_late_flag",
                "volatility_regime",
                "average_range_last_5",
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

                positive_movement = 0.0
                negative_movement = 0.0
                above_vwap = 0.0
                under_vwap = 0.0
                bars_above_volume_average_counter = 0
                bars_under_volume_average_counter = 0
                highest_histogram = 0.0
                lowest_histogram = 0.0
                pullback_sharpness = 0.0
                pullback_duration = 0
                pullback_depth = 0.0
                histogram_at_entry = 0.0
                price_minus_vwap_at_entry = 0.0
                entry_volume_spike_3 = 0.0
                entry_volume_spike_5 = 0.0
                minutes_since_market_open = 0
                distance_from_recent_high = 0.0
                distance_from_high_of_day = 0.0
                volume_trend = 0.0
                number_of_negative_bars = 0
                broke_high_of_day_at_entry = False
                vwap_slope_3 = 0.0
                vwap_slope_5 = 0.0
                ema9_minus_vwap_at_entry = 0.0
                ema9_minus_ema20_at_entry = 0.0
                number_of_green_bars_last_5 = 0.0
                number_of_red_bars_last_5 = 0.0
                distance_from_premarket_high = 0.0
                entry_bar_range_pct = 0.0
                entry_bar_body_pct = 0.0
                upper_wick_pct_at_entry = 0.0
                volume_acceleration = 0.0
                extension_vs_pullback = 0
                move_efficiency = 0
                pullback_to_trend_ratio = 0
                trend_cleanliness = 0
                pullback_structure_score = 0
                volume_confirmation_ratio = 0
                volume_trend_strength = 0
                volume_during_pullback = 0
                relative_position_in_range = 0
                distance_from_vwap_normalized = 0
                hod_proximity_score = 0
                momentum_alignment_score = 0
                momentum_strength = 0
                entry_conviction_score = 0
                entry_efficiency = 0
                failed_breakout_risk = 0
                late_move_indicator = 0
                early_vs_late_flag = False
                volatility_regime = 0
                average_range_last_5 = 0

                price_movement_statistics = symbol_data.get("price_movement_statistics", None)
                if price_movement_statistics:
                    positive_movement = price_movement_statistics["positive_movement_since_market_open"]
                    negative_movement = price_movement_statistics["negative_movement_since_market_open"]
                    above_vwap = price_movement_statistics["movement_above_vwap_since_market_open"]
                    under_vwap = price_movement_statistics["movement_under_vwap_since_market_open"]
                    bars_above_volume_average_counter = price_movement_statistics["movement_above_volume_average_counter_since_market_open"]
                    bars_under_volume_average_counter = price_movement_statistics["movement_under_volume_average_counter_since_market_open"]
                    highest_histogram = price_movement_statistics["highest_histogram_since_market_open"]
                    lowest_histogram = price_movement_statistics["lowest_histogram_since_market_open"]
                    pullback_sharpness = price_movement_statistics["pullback_sharpness"]
                    pullback_duration = price_movement_statistics["pullback_duration"]
                    pullback_depth = price_movement_statistics["pullback_depth"]
                    histogram_at_entry = price_movement_statistics["histogram_at_entry"]
                    price_minus_vwap_at_entry = price_movement_statistics["price_minus_vwap_at_entry"]
                    entry_volume_spike_3 = price_movement_statistics["entry_volume_spike_3"]
                    entry_volume_spike_5 = price_movement_statistics["entry_volume_spike_5"]
                    minutes_since_market_open = price_movement_statistics["minutes_since_market_open"]
                    distance_from_recent_high = price_movement_statistics["distance_from_recent_high"]
                    distance_from_high_of_day = price_movement_statistics["distance_from_high_of_day"]
                    volume_trend = price_movement_statistics["volume_trend"]
                    number_of_negative_bars = price_movement_statistics["number_of_negative_bars"]
                    broke_high_of_day_at_entry = price_movement_statistics["broke_high_of_day_at_entry"]
                    vwap_slope_3 = price_movement_statistics["vwap_slope_3"]
                    vwap_slope_5 = price_movement_statistics["vwap_slope_5"]
                    ema9_minus_vwap_at_entry = price_movement_statistics["ema9_minus_vwap_at_entry"]
                    ema9_minus_ema20_at_entry = price_movement_statistics["ema9_minus_ema20_at_entry"]
                    number_of_green_bars_last_5 = price_movement_statistics["number_of_green_bars_last_5"]
                    number_of_red_bars_last_5 = price_movement_statistics["number_of_red_bars_last_5"]
                    distance_from_premarket_high = price_movement_statistics["distance_from_premarket_high"]
                    entry_bar_range_pct = price_movement_statistics["entry_bar_range_pct"]
                    entry_bar_body_pct = price_movement_statistics["entry_bar_body_pct"]
                    upper_wick_pct_at_entry = price_movement_statistics["upper_wick_pct_at_entry"]
                    volume_acceleration = price_movement_statistics["volume_acceleration"]
                    extension_vs_pullback = price_movement_statistics["extension_vs_pullback"]
                    move_efficiency = price_movement_statistics["move_efficiency"]
                    pullback_to_trend_ratio = price_movement_statistics["pullback_to_trend_ratio"]
                    trend_cleanliness = price_movement_statistics["trend_cleanliness"]
                    pullback_structure_score = price_movement_statistics["pullback_structure_score"]
                    volume_confirmation_ratio = price_movement_statistics["volume_confirmation_ratio"]
                    volume_trend_strength = price_movement_statistics["volume_trend_strength"]
                    volume_during_pullback = price_movement_statistics["volume_during_pullback"]
                    relative_position_in_range = price_movement_statistics["relative_position_in_range"]
                    distance_from_vwap_normalized = price_movement_statistics["distance_from_vwap_normalized"]
                    hod_proximity_score = price_movement_statistics["hod_proximity_score"]
                    momentum_alignment_score = price_movement_statistics["momentum_alignment_score"]
                    momentum_strength = price_movement_statistics["momentum_strength"]
                    entry_conviction_score = price_movement_statistics["entry_conviction_score"]
                    entry_efficiency = price_movement_statistics["entry_efficiency"]
                    failed_breakout_risk = price_movement_statistics["failed_breakout_risk"]
                    late_move_indicator = price_movement_statistics["late_move_indicator"]
                    early_vs_late_flag = price_movement_statistics["early_vs_late_flag"]
                    volatility_regime = price_movement_statistics["volatility_regime"]
                    average_range_last_5 = price_movement_statistics["average_range_last_5"]

                collection_status = symbol_data["collection_status"]
                analysis_status = symbol_data["analysis_status"]

                evidence_name = symbol_data["evidence_name"]
                if symbol_data["is_new"]:
                    evidence_name = f"{evidence_name} - NEW"
                    symbol = f"{symbol} - NEW"

                actual_confirmation_bar_time = symbol_data["actual_confirmation_bar_time"]
                expected_confirmation_bar_time = symbol_data["expected_confirmation_bar_time"]

                volume_until_now = "0"
                if symbol_data.get("volume_until_now"):
                    volume_until_now = symbol_data["volume_until_now"]

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

                    writer.writerow(
                        [
                            symbol,
                            original_bar_time,
                            collection_status,
                            analysis_status,
                            actual_confirmation_bar_time,
                            expected_confirmation_bar_time,
                            evidence_name,
                            volume_until_now,
                            result,
                            positive_movement,
                            negative_movement,
                            above_vwap,
                            under_vwap,
                            bars_above_volume_average_counter,
                            bars_under_volume_average_counter,
                            highest_histogram,
                            lowest_histogram,
                            pullback_sharpness,
                            pullback_duration,
                            pullback_depth,
                            histogram_at_entry,
                            price_minus_vwap_at_entry,
                            entry_volume_spike_3,
                            entry_volume_spike_5,
                            minutes_since_market_open,
                            distance_from_recent_high,
                            distance_from_high_of_day,
                            volume_trend,
                            number_of_negative_bars,
                            broke_high_of_day_at_entry,
                            vwap_slope_3,
                            vwap_slope_5,
                            ema9_minus_vwap_at_entry,
                            ema9_minus_ema20_at_entry,
                            number_of_green_bars_last_5,
                            number_of_red_bars_last_5,
                            distance_from_premarket_high,
                            entry_bar_range_pct,
                            entry_bar_body_pct,
                            upper_wick_pct_at_entry,
                            volume_acceleration,
                            extension_vs_pullback,
                            move_efficiency,
                            pullback_to_trend_ratio,
                            trend_cleanliness,
                            pullback_structure_score,
                            volume_confirmation_ratio,
                            volume_trend_strength,
                            volume_during_pullback,
                            relative_position_in_range,
                            distance_from_vwap_normalized,
                            hod_proximity_score,
                            momentum_alignment_score,
                            momentum_strength,
                            entry_conviction_score,
                            entry_efficiency,
                            failed_breakout_risk,
                            late_move_indicator,
                            early_vs_late_flag,
                            volatility_regime,
                            average_range_last_5,
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
                relevant_symbol_data["volume_until_now"] = "Does not qualify"

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
            relevant_symbol_data[0]["volume_until_now"] = int(confirmation_result["volume_until_now"])
            relevant_symbol_data[0]["price_movement_statistics"] = {}
            continue

        for evidence_name in confirmation_result["evidences"]:
            if should_update_first_default and relevant_symbol_data:
                relevant_symbol_data[0]["actual_confirmation_bar_time"] = confirmation_result["confirmation_bar_time"]
                relevant_symbol_data[0]["evidence_name"] = evidence_name
                relevant_symbol_data[0]["collection_status"] = "done"
                relevant_symbol_data[0]["analysis_status"] = "done"
                relevant_symbol_data[0]["volume_until_now"] = int(confirmation_result["volume_until_now"])
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
                    "volume_until_now": int(confirmation_result["volume_until_now"]),
                    "price_movement_statistics": confirmation_result["price_movement_statistics"],
                    "result": "in_progress",
                },
            )

def flush_logs():
    last_time_flushed = datetime.datetime.now()

    while True:
        now = datetime.datetime.now()
        if now - datetime.timedelta(
            minutes=1,
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
        for symbol, date in stock_finder.get_dynamic_symbols_from_last_month().items()
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
    symbols_data = []
    # symbols = get_symbols()
    # output_file_name = "positive_results.csv"

    # symbols = explore_past_potential_symbols()
    symbols = [
        Symbol(
            name="CAMP",
            datetime_str="03.09.26T13:51:00",
        ),
        Symbol(
            name="CDIO",
            datetime_str="02.18.26T14:18:00",
        ),
        Symbol(
            name="MOVE",
            datetime_str="01.27.26T10:04:00",
        ),
        Symbol(
            name="PLYX",
            datetime_str="03.10.26T14:06:00",
        ),
        Symbol(
            name="JLHL",
            datetime_str="02.02.26T10:46:00",
        ),
        Symbol(
            name="SMX",
            datetime_str="02.06.26T10:16:00",
        ),
        Symbol(
            name="TWAV",
            datetime_str="03.16.26T10:55:00",
        ),
        Symbol(
            name="TURB",
            datetime_str="03.05.26T12:07:00",
        ),
        Symbol(
            name="NCI",
            datetime_str="02.23.26T14:19:00",
        ),
        Symbol(
            name="ONEG",
            datetime_str="01.27.26T10:14:00",
        ),
        Symbol(
            name="BIYA",
            datetime_str="02.20.26T10:49:00",
        ),
        Symbol(
            name="DXST",
            datetime_str="03.06.26T10:40:00",
        ),
        Symbol(
            name="SORA",
            datetime_str="02.02.26T15:19:00",
        ),
        Symbol(
            name="XHLD",
            datetime_str="01.27.26T15:36:00",
        ),
        Symbol(
            name="XTKG",
            datetime_str="01.26.26T14:11:00",
        ),
    ]
    output_file_name = "false_positive_results.csv"

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
                "volume_until_now": "0",
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

def calculate_score():
    positive_data: list[dict[str, any]] = []
    false_positive_data: list[dict[str, any]] = []
    positive_file_path = "positive_results.csv"
    false_positive_file_path = "false_positive_results.csv"

    evidence_object = analyzer.evidences.evidence.Evidence()

    with open(positive_file_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            positive_data.append(row)

    with open(false_positive_file_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            false_positive_data.append(row)

    # positive_scores = []
    for p_d in positive_data:
        score = evidence_object.compute_score(
            symbol_statistics=p_d,
        )
        # positive_scores.append(score)
        print(f"POSITIVE - symbol: {p_d["symbol"]}, bar_time: {p_d["actual_confirmation_bar_time"]}, score: {score}")

    # false_positive_scores = []
    # for f_p_d in false_positive_data:
    #     score = evidence_object.compute_score(
    #         symbol_statistics=f_p_d,
    #     )
    #     # false_positive_scores.append(score)
    #     print(f"NEGATIVE - symbol: {f_p_d["symbol"]}, bar_time: {f_p_d["actual_confirmation_bar_time"]}, score: {score}")

    # for p_d in positive_data:
    #     probability = evidence_object.compute_probability(
    #         symbol_statistics=p_d,
    #         older_positive_scores=positive_scores,
    #     )

    # for f_p_d in false_positive_data:
    #     probability = evidence_object.compute_probability(
    #         symbol_statistics=f_p_d,
    #         older_positive_scores=positive_scores,
    #     )


if __name__ == "__main__":
    calculate_score()
    # if os.path.exists(LOGS_PATH):
    #     os.remove(LOGS_PATH)
    # run_retroactive_check()
