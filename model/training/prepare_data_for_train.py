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
                    "feature_crossed_highest_high",

                    # "feature_volume_per_minute_to_bar_volume",
                    # "feature_volume_average_to_volume",
                    # "feature_last_bars_positive_movement_pct",
                    # "feature_bars_with_lower_volume_average_pct",
                    # "feature_bars_with_ordered_indicators_pct",
                    # "feature_bars_closed_above_half_of_bar_pct",

                    # "feature_price_minus_vwap_at_entry",
                    # "feature_negative_bars_with_positive_histogram_pct",
                    # "feature_positive_vs_negative_movement",
                    # "feature_rejected_pick_points_pct",
                    # "feature_volume_average_goes_up_pct",
                    # "feature_bars_been_crossed_in_the_last_10_bars_pct",
                    # "feature_crossed_bar_with_big_resistance",
                    # "feature_high_volume_bars_with_rejection_pct",
                    # "feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold",
                    # "feature_crossed_any_near_resistance",
                    # "feature_volume_avergae_above_10000_pct_above_threshold",
                    # "feature_entry_bar_closed_strong",
                    # "feature_volume_bigger_than_last_10_bars_pct",
                    # "feature_histogram_negative_momentum_pct",
                    # "feature_bars_with_rejection_inside_entry_bar_range_pct",
                    # "feature_bars_without_movement_pct_above_threshold",
                    # "feature_entry_strength_vs_avg",
                    # "feature_weak_bars_to_bars_since_highest_high_to_total_bars",
                    # "feature_entry_bar_volume_average_above_threshold",
                    # "feature_is_there_highest_high_after_market_open",
                    # "feature_entry_bar_has_highest_volume",
                    # "feature_entry_bar_is_biggest_bar",
                    # "feature_entry_bar_is_highest",
                    # "feature_volume_average_goes_down_pct",
                    # "feature_stronger_than_previous_bars_pct",
                    # "feature_indecision_bars_pct",
                    # "feature_bar_getting_high_while_9_ema_getting_down",
                    # "feature_crossed_any_resistance",
                    # "feature_highest_volume_average_greater_than_entry_bar",
                    # "feature_highest_high_was_recently",
                    # "feature_ema_9_crossed_down_ema_20_since_pullback",
                    # "feature_bar_closed_under_vwap_during_pullback",
                    # "feature_bar_histogram_changed_direction",
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
        feature_distance_from_highest_high_since_market_open = symbol_data["feature_distance_from_highest_high_since_market_open"]
        feature_entry_bar_lowest_wick_to_bar_body_pct = symbol_data["feature_entry_bar_lowest_wick_to_bar_body_pct"]
        feature_entry_bar_volume = symbol_data["feature_entry_bar_volume"]
        feature_entry_volume_vs_total_volume = symbol_data["feature_entry_volume_vs_total_volume"]
        feature_distance_from_highest_high = symbol_data["feature_distance_from_highest_high"]
        feature_bars_with_rejection_since_market_open = symbol_data["feature_bars_with_rejection_since_market_open"]
        feature_entry_point_size_to_bars_size_average = symbol_data["feature_entry_point_size_to_bars_size_average"]
        feature_histogram_changed_directions_pct = symbol_data["feature_histogram_changed_directions_pct"]
        feature_strong_negative_bars_pct = symbol_data["feature_strong_negative_bars_pct"]
        feature_price_action_is_stuck_pct = symbol_data["feature_price_action_is_stuck_pct"]
        feature_entry_bar_close_to_crossed_highest_high_pct = symbol_data["feature_entry_bar_close_to_crossed_highest_high_pct"]
        feature_total_volume = symbol_data["feature_total_volume"]
        feature_current_macd_to_previous = symbol_data["feature_current_macd_to_previous"]
        feature_entry_bar_shape_is_good = symbol_data["feature_entry_bar_shape_is_good"]
        feature_crossed_highest_high = symbol_data["feature_crossed_highest_high"]

        # feature_volume_per_minute_to_bar_volume = symbol_data["feature_volume_per_minute_to_bar_volume"]
        # feature_volume_average_to_volume = symbol_data["feature_volume_average_to_volume"]
        # feature_last_bars_positive_movement_pct = symbol_data["feature_last_bars_positive_movement_pct"]
        # feature_bars_with_lower_volume_average_pct = symbol_data["feature_bars_with_lower_volume_average_pct"]
        # feature_bars_with_ordered_indicators_pct = symbol_data["feature_bars_with_ordered_indicators_pct"]
        # feature_bars_closed_above_half_of_bar_pct = symbol_data["feature_bars_closed_above_half_of_bar_pct"]

        # feature_price_minus_vwap_at_entry = symbol_data["feature_price_minus_vwap_at_entry"]
        # feature_negative_bars_with_positive_histogram_pct = symbol_data["feature_negative_bars_with_positive_histogram_pct"]
        # feature_positive_vs_negative_movement = symbol_data["feature_positive_vs_negative_movement"]
        # feature_rejected_pick_points_pct = symbol_data["feature_rejected_pick_points_pct"]
        # feature_volume_average_goes_up_pct = symbol_data["feature_volume_average_goes_up_pct"]
        # feature_bars_been_crossed_in_the_last_10_bars_pct = symbol_data["feature_bars_been_crossed_in_the_last_10_bars_pct"]
        # feature_crossed_bar_with_big_resistance = symbol_data["feature_crossed_bar_with_big_resistance"]
        # feature_high_volume_bars_with_rejection_pct = symbol_data["feature_high_volume_bars_with_rejection_pct"]
        # feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold = symbol_data["feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold"]
        # feature_crossed_any_near_resistance = symbol_data["feature_crossed_any_near_resistance"]
        # feature_volume_avergae_above_10000_pct_above_threshold = symbol_data["feature_volume_avergae_above_10000_pct_above_threshold"]
        # feature_entry_bar_closed_strong = symbol_data["feature_entry_bar_closed_strong"]
        # feature_volume_bigger_than_last_10_bars_pct = symbol_data["feature_volume_bigger_than_last_10_bars_pct"]
        # feature_histogram_negative_momentum_pct = symbol_data["feature_histogram_negative_momentum_pct"]
        # feature_bars_with_rejection_inside_entry_bar_range_pct = symbol_data["feature_bars_with_rejection_inside_entry_bar_range_pct"]
        # feature_bars_without_movement_pct_above_threshold = symbol_data["feature_bars_without_movement_pct_above_threshold"]
        # feature_entry_strength_vs_avg = symbol_data["feature_entry_strength_vs_avg"]
        # feature_weak_bars_to_bars_since_highest_high_to_total_bars = symbol_data["feature_weak_bars_to_bars_since_highest_high_to_total_bars"]
        # feature_entry_bar_volume_average_above_threshold = symbol_data["feature_entry_bar_volume_average_above_threshold"]
        # feature_is_there_highest_high_after_market_open = symbol_data["feature_is_there_highest_high_after_market_open"]
        # feature_entry_bar_has_highest_volume = symbol_data["feature_entry_bar_has_highest_volume"]
        # feature_entry_bar_is_biggest_bar = symbol_data["feature_entry_bar_is_biggest_bar"]
        # feature_entry_bar_is_highest = symbol_data["feature_entry_bar_is_highest"]
        # feature_volume_average_goes_down_pct = symbol_data["feature_volume_average_goes_down_pct"]
        # feature_stronger_than_previous_bars_pct = symbol_data["feature_stronger_than_previous_bars_pct"]
        # feature_indecision_bars_pct = symbol_data["feature_indecision_bars_pct"]
        # feature_bar_getting_high_while_9_ema_getting_down = symbol_data["feature_bar_getting_high_while_9_ema_getting_down"]
        # feature_crossed_any_resistance = symbol_data["feature_crossed_any_resistance"]
        # feature_highest_volume_average_greater_than_entry_bar = symbol_data["feature_highest_volume_average_greater_than_entry_bar"]
        # feature_highest_high_was_recently = symbol_data["feature_highest_high_was_recently"]
        # feature_ema_9_crossed_down_ema_20_since_pullback = symbol_data["feature_ema_9_crossed_down_ema_20_since_pullback"]
        # feature_bar_closed_under_vwap_during_pullback = symbol_data["feature_bar_closed_under_vwap_during_pullback"]
        # feature_bar_histogram_changed_direction = symbol_data["feature_bar_histogram_changed_direction"]

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
                    feature_crossed_highest_high,

                    # feature_volume_per_minute_to_bar_volume,
                    # feature_volume_average_to_volume,
                    # feature_last_bars_positive_movement_pct,
                    # feature_bars_with_lower_volume_average_pct,
                    # feature_bars_with_ordered_indicators_pct,
                    # feature_bars_closed_above_half_of_bar_pct,

                    # feature_price_minus_vwap_at_entry,
                    # feature_negative_bars_with_positive_histogram_pct,
                    # feature_positive_vs_negative_movement,
                    # feature_rejected_pick_points_pct,
                    # feature_volume_average_goes_up_pct,
                    # feature_bars_been_crossed_in_the_last_10_bars_pct,
                    # feature_crossed_bar_with_big_resistance,
                    # feature_high_volume_bars_with_rejection_pct,
                    # feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold,
                    # feature_crossed_any_near_resistance,
                    # feature_volume_avergae_above_10000_pct_above_threshold,
                    # feature_entry_bar_closed_strong,
                    # feature_volume_bigger_than_last_10_bars_pct,
                    # feature_histogram_negative_momentum_pct,
                    # feature_bars_with_rejection_inside_entry_bar_range_pct,
                    # feature_bars_without_movement_pct_above_threshold,
                    # feature_entry_strength_vs_avg,
                    # feature_weak_bars_to_bars_since_highest_high_to_total_bars,
                    # feature_entry_bar_volume_average_above_threshold,
                    # feature_is_there_highest_high_after_market_open,
                    # feature_entry_bar_has_highest_volume,
                    # feature_entry_bar_is_biggest_bar,
                    # feature_entry_bar_is_highest,
                    # feature_volume_average_goes_down_pct,
                    # feature_stronger_than_previous_bars_pct,
                    # feature_indecision_bars_pct,
                    # feature_bar_getting_high_while_9_ema_getting_down,
                    # feature_crossed_any_resistance,
                    # feature_highest_volume_average_greater_than_entry_bar,
                    # feature_highest_high_was_recently,
                    # feature_ema_9_crossed_down_ema_20_since_pullback,
                    # feature_bar_closed_under_vwap_during_pullback,
                    # feature_bar_histogram_changed_direction,
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
