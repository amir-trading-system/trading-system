import pandas as pd

def compute_thresholds_from_positives(df):
    return {
        "volume": df["feature_positive_vs_negative_volume"].quantile(0.7),
        "movement": df["feature_positive_vs_negative_movement"].quantile(0.7),
        "entry": df["feature_entry_point_size_to_bars_size_average"].quantile(0.7),
        "vwap": df["feature_price_minus_vwap_at_entry"].quantile(0.6),
    }

def compute_quality_score(df, thresholds):
    score = (
        (df["feature_positive_vs_negative_volume"] > thresholds["volume"]).astype(int)
        + (df["feature_positive_vs_negative_movement"] > thresholds["movement"]).astype(int)
        + (df["feature_entry_point_size_to_bars_size_average"] > thresholds["entry"]).astype(int)
        + (df["feature_price_minus_vwap_at_entry"] > thresholds["vwap"]).astype(int)
    )

    return score

positive_df = pd.read_csv('model/training/positive_results_scored.csv')
false_positive_df = pd.read_csv('model/training/false_positive_results_scored.csv')

thresholds = compute_thresholds_from_positives(positive_df)
print(thresholds)

positive_df["quality_score"] = compute_quality_score(positive_df, thresholds)
false_positive_df["quality_score"] = compute_quality_score(false_positive_df, thresholds)

print("POSITIVE SCORE:")
print(positive_df["quality_score"].describe())

print("\nFALSE POSITIVE SCORE:")
print(false_positive_df["quality_score"].describe())

pos_pass_rate = (positive_df["quality_score"] >= 3).mean()
fp_pass_rate = (false_positive_df["quality_score"] >= 3).mean()

print("positive pass:", pos_pass_rate)
print("false positive pass:", fp_pass_rate)

positive_df.to_csv('model/training/positive_results_scored.csv', index=False)
false_positive_df.to_csv('model/training/false_positive_results_scored.csv', index=False)

print(positive_df["quality_score"].describe())
print(false_positive_df["quality_score"].describe())

# for file_name in [
#     'model/training/positive_results_scored.csv',
#     'model/training/false_positive_results_scored.csv',
# ]:
#     df = pd.read_csv(file_name)
#     thresholds = compute_thresholds_from_positives(df)
#     df["passes_quality_filter"] = compute_quality_filter_df_v2(df, thresholds)

#     df.to_csv(file_name, index=False)
