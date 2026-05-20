import concurrent.futures
import csv
import pickle
import glob

import numpy
import pandas as pd

import common
from ..import data_extractor


POSITIVE_FILE_NAME = "model/training/positive_results.csv"
FALSE_POSITIVE_FILE_NAME = "model/training/false_positive_results.csv"
POTENTIAL_HARD_RULES_FILE_NAME = "model/training/hard_rules.json"

#pylint:disable=unspecified-encoding
def write_to_csv(
    symbols_data: list[dict[str, any]],
):
    columns = [
        "symbol",
        "label",
        "original_bar_time",
        "expected_confirmation_bar_time",
        "highest_high_one_minute_bar_time",
        "total_volume",
        "entry_bar_volume",
    ]
    columns.extend(
        [
            k
            for k, _ in symbols_data[0].items()
            if k.startswith("feature_")
        ]
    )

    file_names = [
        POSITIVE_FILE_NAME,
        FALSE_POSITIVE_FILE_NAME,
    ]
    for file_name in file_names:
        with open(file_name, mode="w") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            f.flush()

    for symbol_data in symbols_data:
        stock_object: common.objects.Stock = symbol_data["stock"]
        highest_high_one_minute_bar_time = symbol_data["highest_high_one_minute_bar_time"]
        total_volume = symbol_data["total_volume"]
        entry_bar_volume = symbol_data["entry_bar_volume"]
        features = [v for k, v in symbol_data.items() if k.startswith("feature_")]

        symbol = stock_object.symbol_name
        original_bar_time = stock_object.specific_bar_time

        expected_confirmation_bar_time = stock_object.expected_bar_time
        file_name = POSITIVE_FILE_NAME
        label = 1
        if not stock_object.is_positive:
            file_name = FALSE_POSITIVE_FILE_NAME
            label = 0

        row_data = [
            symbol,
            label,
            original_bar_time,
            expected_confirmation_bar_time,
            highest_high_one_minute_bar_time,
            total_volume,
            entry_bar_volume,
        ]
        row_data.extend(features)

        with open(file_name, mode="a") as f:
            writer = csv.writer(f)
            writer.writerow(row_data)

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
    data_extractor_object = data_extractor.DataExtractor()
    symbols_data_parameters: list[dict[str, any]] = []
    training_model_data_list = load_data_for_training_model()
    for data in training_model_data_list:
        symbol_data_parameters = data_extractor_object.extract_features_from_symbol_data(
            day_timeframe_stock=data["day_timeframe_stock"],
            one_minute_timeframe_stock=data["one_minute_timeframe_stock"],
            potential_confirmation_bar=data["potential_confirmation_bar"],
            highest_high_one_minute_bar=data["highest_high_one_minute_bar"],
            one_minute_bars=data["one_minute_bars"],
        )
        symbol_data_parameters["stock"] = data["day_timeframe_stock"]
        symbols_data_parameters.append(symbol_data_parameters)

    write_to_csv(
        symbols_data=symbols_data_parameters,
    )
