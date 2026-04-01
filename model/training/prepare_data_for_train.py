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
                    "feature_has_positive_more_than_negative_bars",
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
                    "feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open",
                    "feature_highest_volume_before_to_entry_bar_volume_ratio",
                    "feature_highest_average_volume_before_to_entry_bar_average_volume_ratio",
                    "feature_highest_average_volume_before_to_entry_bar_volume_ratio",
                    "feature_macd_under_signal_line_counter",
                    "feature_entry_bar_strengh_pct",
                    "feature_ema_9_keeps_going_up_pct",
                    "feature_strong_bars_above_volume_average_pct",
                    "feature_strong_bars_above_volume_average_to_total_bars_pct",
                    "feature_bars_above_volume_average_pct",
                    "feature_strong_bars_has_continuation",
                    "feature_high_volume_bars_with_rejection_pct",
                    "feature_previous_bar_to_highest_high_pct",
                    "feature_bar_volume_to_volume_sum_since_market_open",
                    "feature_volume_average_to_bar_volume",
                    "feature_volume_per_minute_to_bar_volume",
                    "feature_high_lows_pct",
                    "feature_bars_with_rejection_inside_entry_bar_range_pct",
                    "feature_positive_vs_negative_volume",
                    "feature_positive_vs_negative_movement",
                    "feature_volume_before_middle_point_vs_after_middle_point_pct",
                    "feature_bars_without_movement_pct",
                    "feature_last_negative_to_positive_bars_pct",
                    "feature_crossed_any_resistance",
                    "feature_bars_above_vwap_pct",
                    "feature_entry_bar_profit_pct",
                    "feature_entry_bar_volume_to_highest_bar_volume_pct",
                    "feature_previous_bar_volume_to_entry_bar_volume_pct",
                    "feature_bars_closed_under_ema_20_since_highest_high_bar_pct",
                    "feature_volume_average_change_since_highest_high_pct",
                    "feature_volume_to_volume_average_ratio_since_highest_high",
                    "feature_entry_bar_volume_is_highest_until_now",
                    "feature_ema_9_has_been_tested_since_highest_high",
                    "feature_entry_strength_vs_avg",
                    "feature_weak_bars_since_highest_high_to_total_pct",
                    "feature_bars_since_highest_high_to_total_bars_pct",
                    "feature_weak_bars_to_bars_since_highest_high_to_total_bars",
                    "feature_bars_ema_above_vwap_pct",
                    "feature_positive_bars_close_strong_pct",
                    "feature_positive_to_negative_histograms_pct",
                    "feature_volume_per_minute_to_bar_volume_above_threshold",
                    "feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold",
                    "feature_bars_without_movement_pct_above_threshold",
                    "feature_crossed_highest_high_of_the_day",
                    "feature_crossed_highest_high_of_post_pre_market",
                    "feature_potential_bar_volume_greater_than_volume_average",
                    "feature_potential_bar_low_close_to_open",
                    "feature_potential_bar_wick_is_weak",
                    "feature_volume_average_goes_up_pct",
                    "feature_overlapped_bars_since_market_open_pct",
                ],
            )
            f.flush()

    for symbol_data in symbols_data:
        stock_object: common.objects.Stock = symbol_data["stock"]

        symbol = stock_object.symbol_name
        original_bar_time = stock_object.specific_bar_time

        feature_has_positive_more_than_negative_bars = False
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
        feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = False
        feature_highest_volume_before_to_entry_bar_volume_ratio = 0
        feature_highest_average_volume_before_to_entry_bar_average_volume_ratio = 0
        feature_highest_average_volume_before_to_entry_bar_volume_ratio = 0
        feature_macd_under_signal_line_counter = 0
        feature_entry_bar_strengh_pct = 0
        feature_ema_9_keeps_going_up_pct = 0
        feature_strong_bars_above_volume_average_pct = 0
        feature_strong_bars_above_volume_average_to_total_bars_pct = 0
        feature_bars_above_volume_average_pct = 0
        feature_strong_bars_has_continuation = 0
        feature_high_volume_bars_with_rejection_pct = 0
        feature_previous_bar_to_highest_high_pct = 0
        feature_bar_volume_to_volume_sum_since_market_open = 0
        feature_volume_average_to_bar_volume = 0
        feature_volume_per_minute_to_bar_volume = 0
        feature_high_lows_pct = 0
        feature_bars_with_rejection_inside_entry_bar_range_pct = 0
        feature_positive_vs_negative_volume = 0
        feature_positive_vs_negative_movement = 0
        feature_volume_before_middle_point_vs_after_middle_point_pct = 0
        feature_bars_without_movement_pct = 0
        feature_last_negative_to_positive_bars_pct = 0
        feature_crossed_any_resistance = 0
        feature_bars_above_vwap_pct = 0
        feature_entry_bar_profit_pct = 0
        feature_entry_bar_volume_to_highest_bar_volume_pct = 0
        feature_previous_bar_volume_to_entry_bar_volume_pct = 0
        feature_bars_closed_under_ema_20_since_highest_high_bar_pct = 0
        feature_volume_average_change_since_highest_high_pct = 0
        feature_volume_to_volume_average_ratio_since_highest_high = 0
        feature_entry_bar_volume_is_highest_until_now = 0
        feature_ema_9_has_been_tested_since_highest_high = 0
        feature_entry_strength_vs_avg = 0
        feature_weak_bars_since_highest_high_to_total_pct = 0
        feature_bars_since_highest_high_to_total_bars_pct = 0
        feature_weak_bars_to_bars_since_highest_high_to_total_bars = 0
        feature_bars_ema_above_vwap_pct = 0
        feature_positive_bars_close_strong_pct = 0
        feature_positive_to_negative_histograms_pct = 0
        feature_volume_per_minute_to_bar_volume_above_threshold = 0
        feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold = 0
        feature_bars_without_movement_pct_above_threshold = 0
        feature_crossed_highest_high_of_the_day = 0
        feature_crossed_highest_high_of_post_pre_market = 0
        feature_potential_bar_volume_greater_than_volume_average = 0
        feature_potential_bar_low_close_to_open = 0
        feature_potential_bar_wick_is_weak = 0
        feature_volume_average_goes_up_pct = 0
        feature_overlapped_bars_since_market_open_pct = 0

        feature_has_positive_more_than_negative_bars = symbol_data["feature_has_positive_more_than_negative_bars"]
        feature_pullback_sharpness = symbol_data["feature_pullback_sharpness"]
        feature_pullback_depth = symbol_data["feature_pullback_depth"]
        feature_number_of_negative_bars_in_pullback_pct = symbol_data["feature_number_of_negative_bars_in_pullback_pct"]
        feature_price_minus_vwap_at_entry = symbol_data["feature_price_minus_vwap_at_entry"]
        feature_pullback_to_trend_ratio = symbol_data["feature_pullback_to_trend_ratio"]
        feature_histogram_negative_momentum_pct = symbol_data["feature_histogram_negative_momentum_pct"]
        feature_strong_positive_bars_with_full_body_pct = symbol_data["feature_strong_positive_bars_with_full_body_pct"]
        feature_minutes_since_market_open_to_total_market_minutes_pct = symbol_data["feature_minutes_since_market_open_to_total_market_minutes_pct"]
        feature_bars_with_at_least_50_pct_wick_pct = symbol_data["feature_bars_with_at_least_50_pct_wick_pct"]
        feature_bars_with_lower_volume_average_pct = symbol_data["feature_bars_with_lower_volume_average_pct"]
        feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open = symbol_data["feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open"]
        feature_highest_volume_before_to_entry_bar_volume_ratio = symbol_data["feature_highest_volume_before_to_entry_bar_volume_ratio"]
        feature_highest_average_volume_before_to_entry_bar_average_volume_ratio = symbol_data["feature_highest_average_volume_before_to_entry_bar_average_volume_ratio"]
        feature_highest_average_volume_before_to_entry_bar_volume_ratio = symbol_data["feature_highest_average_volume_before_to_entry_bar_volume_ratio"]
        feature_macd_under_signal_line_counter = symbol_data["feature_macd_under_signal_line_counter"]
        feature_entry_bar_strengh_pct = symbol_data["feature_entry_bar_strengh_pct"]
        feature_ema_9_keeps_going_up_pct = symbol_data["feature_ema_9_keeps_going_up_pct"]
        feature_strong_bars_above_volume_average_pct = symbol_data["feature_strong_bars_above_volume_average_pct"]
        feature_strong_bars_above_volume_average_to_total_bars_pct = symbol_data["feature_strong_bars_above_volume_average_to_total_bars_pct"]
        feature_bars_above_volume_average_pct = symbol_data["feature_bars_above_volume_average_pct"]
        feature_strong_bars_has_continuation = symbol_data["feature_strong_bars_has_continuation"]
        feature_high_volume_bars_with_rejection_pct = symbol_data["feature_high_volume_bars_with_rejection_pct"]
        feature_previous_bar_to_highest_high_pct = symbol_data["feature_previous_bar_to_highest_high_pct"]
        feature_bar_volume_to_volume_sum_since_market_open = symbol_data["feature_bar_volume_to_volume_sum_since_market_open"]
        feature_volume_average_to_bar_volume = symbol_data["feature_volume_average_to_bar_volume"]
        feature_volume_per_minute_to_bar_volume = symbol_data["feature_volume_per_minute_to_bar_volume"]
        feature_high_lows_pct = symbol_data["feature_high_lows_pct"]
        feature_bars_with_rejection_inside_entry_bar_range_pct = symbol_data["feature_bars_with_rejection_inside_entry_bar_range_pct"]
        feature_positive_vs_negative_volume = symbol_data["feature_positive_vs_negative_volume"]
        feature_positive_vs_negative_movement = symbol_data["feature_positive_vs_negative_movement"]
        feature_volume_before_middle_point_vs_after_middle_point_pct = symbol_data["feature_volume_before_middle_point_vs_after_middle_point_pct"]
        feature_bars_without_movement_pct = symbol_data["feature_bars_without_movement_pct"]
        feature_last_negative_to_positive_bars_pct = symbol_data["feature_last_negative_to_positive_bars_pct"]
        feature_crossed_any_resistance = symbol_data["feature_crossed_any_resistance"]
        feature_bars_above_vwap_pct = symbol_data["feature_bars_above_vwap_pct"]
        feature_entry_bar_profit_pct = symbol_data["feature_entry_bar_profit_pct"]
        feature_entry_bar_volume_to_highest_bar_volume_pct = symbol_data["feature_entry_bar_volume_to_highest_bar_volume_pct"]
        feature_previous_bar_volume_to_entry_bar_volume_pct = symbol_data["feature_previous_bar_volume_to_entry_bar_volume_pct"]
        feature_bars_closed_under_ema_20_since_highest_high_bar_pct = symbol_data["feature_bars_closed_under_ema_20_since_highest_high_bar_pct"]
        feature_volume_average_change_since_highest_high_pct = symbol_data["feature_volume_average_change_since_highest_high_pct"]
        feature_volume_to_volume_average_ratio_since_highest_high = symbol_data["feature_volume_to_volume_average_ratio_since_highest_high"]
        feature_entry_bar_volume_is_highest_until_now = symbol_data["feature_entry_bar_volume_is_highest_until_now"]
        feature_ema_9_has_been_tested_since_highest_high = symbol_data["feature_ema_9_has_been_tested_since_highest_high"]
        feature_entry_strength_vs_avg = symbol_data["feature_entry_strength_vs_avg"]
        feature_weak_bars_since_highest_high_to_total_pct = symbol_data["feature_weak_bars_since_highest_high_to_total_pct"]
        feature_bars_since_highest_high_to_total_bars_pct = symbol_data["feature_bars_since_highest_high_to_total_bars_pct"]
        feature_weak_bars_to_bars_since_highest_high_to_total_bars = symbol_data["feature_weak_bars_since_highest_high_to_total_pct"]/symbol_data["feature_bars_since_highest_high_to_total_bars_pct"] if symbol_data["feature_bars_since_highest_high_to_total_bars_pct"] > 0 else 0
        feature_bars_ema_above_vwap_pct = symbol_data["feature_bars_ema_above_vwap_pct"]
        feature_positive_bars_close_strong_pct = symbol_data["feature_positive_bars_close_strong_pct"]
        feature_positive_to_negative_histograms_pct = symbol_data["feature_positive_to_negative_histograms_pct"]
        feature_volume_per_minute_to_bar_volume_above_threshold = symbol_data["feature_volume_per_minute_to_bar_volume_above_threshold"]
        feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold = symbol_data["feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold"]
        feature_bars_without_movement_pct_above_threshold = symbol_data["feature_bars_without_movement_pct_above_threshold"]
        feature_crossed_highest_high_of_the_day = symbol_data["feature_crossed_highest_high_of_the_day"]
        feature_crossed_highest_high_of_post_pre_market = symbol_data["feature_crossed_highest_high_of_post_pre_market"]
        feature_potential_bar_volume_greater_than_volume_average = symbol_data["feature_potential_bar_volume_greater_than_volume_average"]
        feature_potential_bar_low_close_to_open = symbol_data["feature_potential_bar_low_close_to_open"]
        feature_potential_bar_wick_is_weak = symbol_data["feature_potential_bar_wick_is_weak"]
        feature_volume_average_goes_up_pct = symbol_data["feature_volume_average_goes_up_pct"]
        feature_overlapped_bars_since_market_open_pct = symbol_data["feature_overlapped_bars_since_market_open_pct"]

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
                    feature_has_positive_more_than_negative_bars,
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
                    feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open,
                    feature_highest_volume_before_to_entry_bar_volume_ratio,
                    feature_highest_average_volume_before_to_entry_bar_average_volume_ratio,
                    feature_highest_average_volume_before_to_entry_bar_volume_ratio,
                    feature_macd_under_signal_line_counter,
                    feature_entry_bar_strengh_pct,
                    feature_ema_9_keeps_going_up_pct,
                    feature_strong_bars_above_volume_average_pct,
                    feature_strong_bars_above_volume_average_to_total_bars_pct,
                    feature_bars_above_volume_average_pct,
                    feature_strong_bars_has_continuation,
                    feature_high_volume_bars_with_rejection_pct,
                    feature_previous_bar_to_highest_high_pct,
                    feature_bar_volume_to_volume_sum_since_market_open,
                    feature_volume_average_to_bar_volume,
                    feature_volume_per_minute_to_bar_volume,
                    feature_high_lows_pct,
                    feature_bars_with_rejection_inside_entry_bar_range_pct,
                    feature_positive_vs_negative_volume,
                    feature_positive_vs_negative_movement,
                    feature_volume_before_middle_point_vs_after_middle_point_pct,
                    feature_bars_without_movement_pct,
                    feature_last_negative_to_positive_bars_pct,
                    feature_crossed_any_resistance,
                    feature_bars_above_vwap_pct,
                    feature_entry_bar_profit_pct,
                    feature_entry_bar_volume_to_highest_bar_volume_pct,
                    feature_previous_bar_volume_to_entry_bar_volume_pct,
                    feature_bars_closed_under_ema_20_since_highest_high_bar_pct,
                    feature_volume_average_change_since_highest_high_pct,
                    feature_volume_to_volume_average_ratio_since_highest_high,
                    feature_entry_bar_volume_is_highest_until_now,
                    feature_ema_9_has_been_tested_since_highest_high,
                    feature_entry_strength_vs_avg,
                    feature_weak_bars_since_highest_high_to_total_pct,
                    feature_bars_since_highest_high_to_total_bars_pct,
                    feature_weak_bars_to_bars_since_highest_high_to_total_bars,
                    feature_bars_ema_above_vwap_pct,
                    feature_positive_bars_close_strong_pct,
                    feature_positive_to_negative_histograms_pct,
                    feature_volume_per_minute_to_bar_volume_above_threshold,
                    feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold,
                    feature_bars_without_movement_pct_above_threshold,
                    feature_crossed_highest_high_of_the_day,
                    feature_crossed_highest_high_of_post_pre_market,
                    feature_potential_bar_volume_greater_than_volume_average,
                    feature_potential_bar_low_close_to_open,
                    feature_potential_bar_wick_is_weak,
                    feature_volume_average_goes_up_pct,
                    feature_overlapped_bars_since_market_open_pct,
                ]
            )

            f.flush()


def load_data_for_training_model() -> list[dict[str, any]]:
    pickled_data: list[dict[str, any]] = []
    files = glob.glob("model/training/data/*")
    for file_path in files:
        with open(file_path, "rb") as f:
            obj = pickle.load(f)
            pickled_data.append(obj)

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
