import pandas as pd

colums_to_drop = [
    "feature_lower_bars_has_lower_volume",
    "feature_lower_bars_has_lower_volume_pct",
]

for file_name in [
    'model/positive_results.csv',
    'model/false_positive_results.csv',
]:
    df = pd.read_csv(file_name)

    df = df.drop(
        columns=colums_to_drop,
    )

    df.to_csv(file_name, index=False)
