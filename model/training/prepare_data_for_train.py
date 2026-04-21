import concurrent.futures
import csv
import pickle
import glob

import common
from ..import data_extractor


POSITIVE_FILE_NAME = "model/training/positive_results.csv"
FALSE_POSITIVE_FILE_NAME = "model/training/false_positive_results.csv"

#pylint:disable=unspecified-encoding
def write_to_csv(
    symbols_data: list[dict[str, any]],
):
    file_names = [
        POSITIVE_FILE_NAME,
        FALSE_POSITIVE_FILE_NAME,
    ]
    for file_name in file_names:
        with open(file_name, mode="w") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "symbol",
                    "original_bar_time",
                    "expected_confirmation_bar_time",
                    "feature_bars_with_at_least_50_pct_wick_pct",
                    "feature_positive_vs_negative_volume",
                    "feature_overlapped_bars_since_market_open_pct",
                    "feature_entry_bar_volume",
                    "feature_distance_from_highest_high",
                    "feature_bars_with_rejection_since_market_open",
                    "feature_entry_point_size_to_bars_size_average",
                    "feature_histogram_changed_directions_pct",
                    "feature_strong_negative_bars_pct",
                    "feature_price_action_is_stuck_pct",
                    "feature_entry_bar_close_to_crossed_highest_high_pct",
                    "feature_total_volume",
                    "feature_current_macd_to_previous",
                    "feature_late_volume_spike",
                    "feature_entry_bar_price_action_to_total_price_pct",
                    "feature_entry_volume_vs_total_volume",
                    "feature_entry_bar_price_action_pct_to_volume_pct",
                    "feature_bars_above_vwap_pct",
                    "feature_distance_between_highest_high_to_entry_bar_high",
                    "feature_fibonacci_retracement",
                ],
            )
            f.flush()

    for symbol_data in symbols_data:
        stock_object: common.objects.Stock = symbol_data["stock"]

        symbol = stock_object.symbol_name
        original_bar_time = stock_object.specific_bar_time

        feature_bars_with_at_least_50_pct_wick_pct = symbol_data["feature_bars_with_at_least_50_pct_wick_pct"]
        feature_positive_vs_negative_volume = symbol_data["feature_positive_vs_negative_volume"]
        feature_overlapped_bars_since_market_open_pct = symbol_data["feature_overlapped_bars_since_market_open_pct"]
        feature_entry_bar_volume = symbol_data["feature_entry_bar_volume"]
        feature_distance_from_highest_high = symbol_data["feature_distance_from_highest_high"]
        feature_bars_with_rejection_since_market_open = symbol_data["feature_bars_with_rejection_since_market_open"]
        feature_entry_point_size_to_bars_size_average = symbol_data["feature_entry_point_size_to_bars_size_average"]
        feature_histogram_changed_directions_pct = symbol_data["feature_histogram_changed_directions_pct"]
        feature_strong_negative_bars_pct = symbol_data["feature_strong_negative_bars_pct"]
        feature_price_action_is_stuck_pct = symbol_data["feature_price_action_is_stuck_pct"]
        feature_entry_bar_close_to_crossed_highest_high_pct = symbol_data["feature_entry_bar_close_to_crossed_highest_high_pct"]
        feature_total_volume = symbol_data["feature_total_volume"]
        feature_current_macd_to_previous = symbol_data["feature_current_macd_to_previous"]
        feature_late_volume_spike = symbol_data["feature_late_volume_spike"]
        feature_entry_bar_price_action_to_total_price_pct = symbol_data["feature_entry_bar_price_action_to_total_price_pct"]
        feature_entry_volume_vs_total_volume = symbol_data["feature_entry_volume_vs_total_volume"]
        feature_entry_bar_price_action_pct_to_volume_pct = symbol_data["feature_entry_bar_price_action_pct_to_volume_pct"]
        feature_bars_above_vwap_pct = symbol_data["feature_bars_above_vwap_pct"]
        feature_distance_between_highest_high_to_entry_bar_high = symbol_data["feature_distance_between_highest_high_to_entry_bar_high"]
        feature_fibonacci_retracement = symbol_data["feature_fibonacci_retracement"]

        expected_confirmation_bar_time = stock_object.expected_bar_time
        file_name = POSITIVE_FILE_NAME
        if not stock_object.is_positive:
            file_name = FALSE_POSITIVE_FILE_NAME

        with open(file_name, mode="a") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    symbol,
                    original_bar_time,
                    expected_confirmation_bar_time,
                    feature_bars_with_at_least_50_pct_wick_pct,
                    feature_positive_vs_negative_volume,
                    feature_overlapped_bars_since_market_open_pct,
                    feature_entry_bar_volume,
                    feature_distance_from_highest_high,
                    feature_bars_with_rejection_since_market_open,
                    feature_entry_point_size_to_bars_size_average,
                    feature_histogram_changed_directions_pct,
                    feature_strong_negative_bars_pct,
                    feature_price_action_is_stuck_pct,
                    feature_entry_bar_close_to_crossed_highest_high_pct,
                    feature_total_volume,
                    feature_current_macd_to_previous,
                    feature_late_volume_spike,
                    feature_entry_bar_price_action_to_total_price_pct,
                    feature_entry_volume_vs_total_volume,
                    feature_entry_bar_price_action_pct_to_volume_pct,
                    feature_bars_above_vwap_pct,
                    feature_distance_between_highest_high_to_entry_bar_high,
                    feature_fibonacci_retracement,
                ]
            )

            f.flush()


def load_pickle_data(
    file_path: str,
) -> any:
    with open(file_path, "rb") as f:
        obj = pickle.load(f)

    return obj

def load_data_for_training_model() -> list[dict[str, any]]:
    pickled_data: list[dict[str, any]] = []
    files = glob.glob("model/training/data/*")
    futures = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=10,
    ) as executor:
        for file_path in files:
            f = executor.submit(
                load_pickle_data,
                file_path,
            )
            futures.append(f)

    for future in concurrent.futures.as_completed(futures):
        pickled_object = future.result()
        pickled_data.append(pickled_object)

    return pickled_data

if __name__ == '__main__':
    symbols_data_parameters: list[dict[str, any]] = []
    training_model_data_list = load_data_for_training_model()
    for data in training_model_data_list:
        symbol_data_parameters = data_extractor.DataExtractor.extract_features_from_symbol_data(
            day_timeframe_stock=data["day_timeframe_stock"],
            one_minute_timeframe_stock=data["one_minute_timeframe_stock"],
            potential_confirmation_bar=data["potential_confirmation_bar"],
            highest_high_one_minute_bar=data["highest_high_one_minute_bar"],
            volume_sum_since_market_open=data["volume_sum_since_market_open"],
            one_minute_bars=data["one_minute_bars"],
        )
        symbol_data_parameters["stock"] = data["day_timeframe_stock"]
        symbols_data_parameters.append(symbol_data_parameters)

    write_to_csv(
        symbols_data=symbols_data_parameters,
    )
