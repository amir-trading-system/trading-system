import pandas as pd

# colums_to_drop = [
#     "feature_lower_bars_has_lower_volume",
#     "feature_lower_bars_has_lower_volume_pct",
# ]

for file_name in [
    'model/positive_results.csv',
    'model/false_positive_results.csv',
]:
    df = pd.read_csv(file_name)

    df["feature_has_positive_more_than_negative_bars"] = df["feature_positive_bars_pct"] > df["feature_negative_bars_pct"]
    df["feature_has_more_positive_volume_than_negative"] = df["feature_positive_volume_pct"] > df["feature_negative_volume_pct"]
    df["volume_greater_than_million"] = df["volume_until_now"] > 1000000

    # df = df.drop(
    #     columns=colums_to_drop,
    # )

    df.to_csv(file_name, index=False)
