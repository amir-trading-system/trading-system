import datetime
import concurrent.futures
import csv
import pickle
import glob

def load_pickle_data(
    file_path: str,
) -> any:
    with open(file_path, "rb") as f:
        obj = pickle.load(f)

    return obj

def load_data_for_training_model() -> list[dict[str, any]]:
    pickled_data: list[dict[str, any]] = []
    files = glob.glob("model/training/data/next_training/*.json")
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

#pylint:disable=unspecified-encoding
def extract_one_minute_timeframe_data_into_csv():
    data_list = load_data_for_training_model()

    columns = [
        "symbol",
        "bar_time",
        "high",
        "low",
        "open",
        "close",
        "volume",
        "volume_average",
        "ema_9",
        "ema_20",
        "vwap",
        "macd",
        "histogram",
        "signal_line",
    ]

    file_name = f"model/{datetime.datetime.now().date()}.csv"

    with open(file_name, mode="w") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        f.flush()

    for data_object in data_list:
        potential_confirmation_bar = data_object["potential_confirmation_bar"]
        one_minute_bar_rows = [
            [
                bar_object.symbol,
                bar_object.bar_time,
                bar_object.high,
                bar_object.low,
                bar_object.open_value,
                bar_object.close,
                bar_object.volume,
                bar_object.volume_average,
                bar_object.ema_9,
                bar_object.ema_20,
                bar_object.vwap,
                bar_object.macd,
                bar_object.histogram,
                bar_object.signal_line,
            ]
            for bar_object in data_object["one_minute_timeframe_stock"].bars
            if bar_object.bar_time.date() == potential_confirmation_bar.bar_time.date()
        ]

        with open(file_name, mode="a") as f:
            writer = csv.writer(f)
            writer.writerows(one_minute_bar_rows)

            f.flush()

if __name__ == '__main__':
    extract_one_minute_timeframe_data_into_csv()
