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
                    "highest_high_one_minute_bar_time",
                    "feature_total_volume",
                    "feature_entry_bar_price_action_pct_to_volume_pct",
                    "feature_distance_between_highest_high_to_entry_bar_high",
                    "feature_positive_bars_above_volume_average_pct",
                    "feature_volume_quality",
                    "feature_price_action_is_stuck_pct",
                    "feature_previous_historgam_to_current_histogram",
                    "feature_efficiency_balance",
                    "feature_trap_signal",
                    "feature_clean_move",
                    "feature_fake_momentum",
                    "feature_structure_adjusted_strength",
                ],
            )
            f.flush()

    for symbol_data in symbols_data:
        stock_object: common.objects.Stock = symbol_data["stock"]

        symbol = stock_object.symbol_name
        original_bar_time = stock_object.specific_bar_time
        highest_high_one_minute_bar_time = symbol_data["highest_high_one_minute_bar_time"]

        feature_price_action_is_stuck_pct = symbol_data["feature_price_action_is_stuck_pct"]
        feature_total_volume = symbol_data["feature_total_volume"]
        feature_entry_bar_price_action_pct_to_volume_pct = symbol_data["feature_entry_bar_price_action_pct_to_volume_pct"]
        feature_distance_between_highest_high_to_entry_bar_high = symbol_data["feature_distance_between_highest_high_to_entry_bar_high"]
        feature_positive_bars_above_volume_average_pct = symbol_data["feature_positive_bars_above_volume_average_pct"]
        feature_volume_quality = symbol_data["feature_volume_quality"]
        feature_previous_historgam_to_current_histogram = symbol_data["feature_previous_historgam_to_current_histogram"]
        feature_efficiency_balance = symbol_data["feature_efficiency_balance"]
        feature_trap_signal = symbol_data["feature_trap_signal"]
        feature_clean_move = symbol_data["feature_clean_move"]
        feature_fake_momentum = symbol_data["feature_fake_momentum"]
        feature_structure_adjusted_strength = symbol_data["feature_structure_adjusted_strength"]

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
                    highest_high_one_minute_bar_time,
                    feature_total_volume,
                    feature_entry_bar_price_action_pct_to_volume_pct,
                    feature_distance_between_highest_high_to_entry_bar_high,
                    feature_positive_bars_above_volume_average_pct,
                    feature_volume_quality,
                    feature_price_action_is_stuck_pct,
                    feature_previous_historgam_to_current_histogram,
                    feature_efficiency_balance,
                    feature_trap_signal,
                    feature_clean_move,
                    feature_fake_momentum,
                    feature_structure_adjusted_strength,
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
    files = glob.glob("model/training/data/*.json")
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
