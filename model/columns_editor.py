import pandas as pd

df = pd.read_csv('model/positive_results_scored.csv')
false_positive_df = pd.read_csv('model/false_positive_results.csv')

for file_name in [
    'model/positive_results.csv',
    'model/false_positive_results.csv',
]:
    df = pd.read_csv(file_name)

    df["bar_volume_to_volume_sum_since_market_open"] = df["bar_volume"]/(df["feature_volume_sum_since_market_open"] - df["bar_volume"])
    df["volume_average_to_bar_volume"] = df["volume_average"]/df["bar_volume"]
    df["volume_per_minute_to_bar_volume"] = df["volume_per_minute"]/df["bar_volume"]

    df = df.drop(
        columns=[
            "original_bar_time",
            "collection_status",
            "analysis_status",
            "evidence",
            "feature_volume_sum_since_market_open",
            "result",
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
        ],
    )

    df.to_csv(file_name, index=False)
