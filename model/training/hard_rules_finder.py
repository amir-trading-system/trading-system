from itertools import combinations, product

import pandas as pd
import numpy as np


POSITIVE_FILE = "model/training/positive_results_scored.csv"
FALSE_POSITIVE_FILE = "model/training/false_positive_results_scored.csv"

SCORE_COLUMN = "score"
PASS_COLUMN = "pass_recommended"

HIGH_SCORE_FP_THRESHOLD = 60
LOW_SCORE_POSITIVE_THRESHOLD = 50

MAX_POSITIVES_KILLED = 0
MAX_LOW_SCORE_POSITIVES_KILLED = 0

MIN_TOTAL_FP_CAUGHT = 3
MIN_RECOMMENDED_FP_CAUGHT = 1

# Use quantiles instead of every unique value to avoid overfitting too hard.
QUANTILES = [0.05, 0.10, 0.20, 0.33, 0.50, 0.67, 0.80, 0.90, 0.95]


def load_data():
    pos = pd.read_csv(POSITIVE_FILE)
    fp = pd.read_csv(FALSE_POSITIVE_FILE)
    fp = fp[fp["feature_overall_legit_trade"] == np.True_]

    pos = pos.copy()
    fp = fp.copy()

    pos["label"] = 1
    fp["label"] = 0

    data = pd.concat([pos, fp], ignore_index=True)

    # Normalize boolean pass column if needed.
    if PASS_COLUMN in data.columns:
        data[PASS_COLUMN] = data[PASS_COLUMN].astype(str).str.lower().isin(
            ["true", "1", "yes"]
        )
    else:
        data[PASS_COLUMN] = data[SCORE_COLUMN] >= 50

    return pos, fp, data


def numeric_feature_columns(df):
    ignored = {
        "label",
        "symbol",
        "original_bar_time",
        "expected_confirmation_bar_time",
        "highest_high_one_minute_bar_time",
        SCORE_COLUMN,
        PASS_COLUMN,
        "probability",
        "grade",
        "rules_pass",
    }

    cols = []

    for col in df.columns:
        if col in ignored:
            continue

        if not col.startswith("feature_"):
            continue

        series = clean_numeric(df, col)

        # Must have usable numeric values.
        if series.notna().sum() == 0:
            continue

        # Skip constant columns.
        if series.dropna().nunique() <= 1:
            continue

        cols.append(col)

    return cols


def clean_numeric(df, col):
    s = df[col]

    # Convert actual booleans to 0/1.
    if pd.api.types.is_bool_dtype(s):
        return s.astype(float)

    # Convert string booleans to 0/1.
    if s.dtype == "object":
        s = (
            s.astype(str)
            .str.strip()
            .str.lower()
            .replace({
                "true": "1",
                "false": "0",
                "yes": "1",
                "no": "0",
                "none": np.nan,
                "nan": np.nan,
                "": np.nan,
            })
        )

    return (
        pd.to_numeric(s, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .astype(float)
    )

def thresholds_for_feature(df, col):
    s = clean_numeric(df, col).dropna()

    if s.empty:
        return []

    if s.nunique() <= 1:
        return []

    values = np.quantile(s.astype(float), QUANTILES)

    values = sorted(set(float(v) for v in values if np.isfinite(v)))

    return values


def condition_mask(df, feature, op, threshold):
    s = clean_numeric(df, feature)

    if op == "<=":
        return s <= threshold
    if op == ">=":
        return s >= threshold

    raise ValueError(f"Unsupported operator: {op}")


def evaluate_rule(pos, fp, conditions):
    """
    conditions = [
        ("feature_x", "<=", 1.23),
        ("feature_y", ">=", 4.56),
    ]
    """

    pos_mask = pd.Series(True, index=pos.index)
    fp_mask = pd.Series(True, index=fp.index)

    for feature, op, threshold in conditions:
        pos_mask &= condition_mask(pos, feature, op, threshold)
        fp_mask &= condition_mask(fp, feature, op, threshold)

    positives_killed = int(pos_mask.sum())
    false_positives_caught = int(fp_mask.sum())

    if SCORE_COLUMN in pos.columns:
        low_score_positives_killed = int(
            (pos_mask & (pd.to_numeric(pos[SCORE_COLUMN], errors="coerce") < LOW_SCORE_POSITIVE_THRESHOLD)).sum()
        )
    else:
        low_score_positives_killed = 0

    if SCORE_COLUMN in fp.columns:
        high_score_fps_caught = int(
            (fp_mask & (pd.to_numeric(fp[SCORE_COLUMN], errors="coerce") >= HIGH_SCORE_FP_THRESHOLD)).sum()
        )
    else:
        high_score_fps_caught = 0

    if PASS_COLUMN in fp.columns:
        recommended_fps_caught = int((fp_mask & fp[PASS_COLUMN]).sum())
    else:
        recommended_fps_caught = high_score_fps_caught

    # Weighted score: prioritize useful FP catches and punish killed positives heavily.
    rule_score = (
        false_positives_caught
        + 3 * recommended_fps_caught
        + 4 * high_score_fps_caught
        - 25 * positives_killed
        - 15 * low_score_positives_killed
    )

    return {
        "conditions": conditions,
        "positives_killed": positives_killed,
        "low_score_positives_killed": low_score_positives_killed,
        "false_positives_caught": false_positives_caught,
        "recommended_fps_caught": recommended_fps_caught,
        "high_score_fps_caught": high_score_fps_caught,
        "rule_score": rule_score,
    }


def rule_is_acceptable(result):
    return (
        result["positives_killed"] <= MAX_POSITIVES_KILLED
        and result["low_score_positives_killed"] <= MAX_LOW_SCORE_POSITIVES_KILLED
        and result["false_positives_caught"] >= MIN_TOTAL_FP_CAUGHT
        and result["recommended_fps_caught"] >= MIN_RECOMMENDED_FP_CAUGHT
    )


def format_condition(feature, op, threshold):
    short = feature.replace("feature_", "")
    return f"{short} {op} {threshold:.6g}"


def format_python_rule(result):
    lines = ["if ("]
    for i, (feature, op, threshold) in enumerate(result["conditions"]):
        and_text = "and " if i > 0 else "    "
        lines.append(f"    {and_text}{feature.replace('feature_', '')} {op} {threshold:.10g}")
    lines.append("):")
    lines.append("    return False")
    return "\n".join(lines)


def search_two_condition_rules(pos, fp, features):
    results = []

    feature_thresholds = {
        feature: thresholds_for_feature(pd.concat([pos, fp], ignore_index=True), feature)
        for feature in features
    }

    ops = ["<=", ">="]

    for f1, f2 in combinations(features, 2):
        t1_values = feature_thresholds[f1]
        t2_values = feature_thresholds[f2]

        if not t1_values or not t2_values:
            continue

        for op1, op2 in product(ops, ops):
            for t1 in t1_values:
                for t2 in t2_values:
                    conditions = [
                        (f1, op1, t1),
                        (f2, op2, t2),
                    ]

                    result = evaluate_rule(pos, fp, conditions)

                    if rule_is_acceptable(result):
                        results.append(result)

    return results


def search_three_condition_rules(pos, fp, features, max_feature_combos=500):
    """
    3-condition search can get expensive.
    This keeps it practical by using fewer quantiles and optionally limiting combos.
    """

    results = []

    three_quantiles = [0.05, 0.10, 0.20, 0.33, 0.50, 0.67, 0.80, 0.90, 0.95]
    combined = pd.concat([pos, fp], ignore_index=True)

    def thresholds_3(feature):
        s = clean_numeric(combined, feature).dropna()
        if s.empty:
            return []
        return [float(v) for v in sorted(set(np.quantile(s, three_quantiles))) if np.isfinite(v)]

    feature_thresholds = {feature: thresholds_3(feature) for feature in features}

    ops = ["<=", ">="]

    feature_combos = list(combinations(features, 3))
    if max_feature_combos is not None:
        feature_combos = feature_combos[:max_feature_combos]

    for f1, f2, f3 in feature_combos:
        t1_values = feature_thresholds[f1]
        t2_values = feature_thresholds[f2]
        t3_values = feature_thresholds[f3]

        if not t1_values or not t2_values or not t3_values:
            continue

        for op1, op2, op3 in product(ops, ops, ops):
            for t1 in t1_values:
                for t2 in t2_values:
                    for t3 in t3_values:
                        conditions = [
                            (f1, op1, t1),
                            (f2, op2, t2),
                            (f3, op3, t3),
                        ]

                        result = evaluate_rule(pos, fp, conditions)

                        if rule_is_acceptable(result):
                            results.append(result)

    return results


def remove_near_duplicate_rules(results, max_results=50):
    """
    Basic de-duplication by condition feature/op signature.
    Keeps highest scoring rule per signature.
    """

    best_by_signature = {}

    for result in results:
        signature = tuple((feature, op) for feature, op, _ in result["conditions"])

        existing = best_by_signature.get(signature)
        if existing is None or result["rule_score"] > existing["rule_score"]:
            best_by_signature[signature] = result

    deduped = list(best_by_signature.values())

    deduped.sort(
        key=lambda r: (
            r["recommended_fps_caught"],
            r["high_score_fps_caught"],
            r["false_positives_caught"],
            -r["positives_killed"],
            r["rule_score"],
        ),
        reverse=True,
    )

    return deduped[:max_results]


def print_results(results, title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    for i, result in enumerate(results, start=1):
        condition_text = " AND ".join(
            format_condition(feature, op, threshold)
            for feature, op, threshold in result["conditions"]
        )

        print(f"\n#{i}")
        print(condition_text)
        print(
            f"FP caught: {result['false_positives_caught']} | "
            f"Recommended FP caught: {result['recommended_fps_caught']} | "
            f"High-score FP caught: {result['high_score_fps_caught']} | "
            f"Positives killed: {result['positives_killed']} | "
            f"Low-score positives killed: {result['low_score_positives_killed']} | "
            f"Score: {result['rule_score']}"
        )
        print("\nPython:")
        print(format_python_rule(result))


def main():
    pos, fp, data = load_data()
    features = numeric_feature_columns(data)

    print(f"Positive rows: {len(pos)}")
    print(f"False-positive rows: {len(fp)}")
    print(f"Candidate numeric features: {len(features)}")

    two_condition_results = search_two_condition_rules(pos, fp, features)
    two_condition_results = remove_near_duplicate_rules(two_condition_results, max_results=30)

    print_results(two_condition_results, "BEST 2-CONDITION RULES")

    # Optional: use only the most promising features for triples to avoid huge runtime.
    # promising_features = [
    #     "feature_entry_bar_upper_wick",
    #     "feature_entry_extension_pressure",
    #     "feature_reclaim_close_strength_since_highest_high",
    #     "feature_entry_upper_wick_to_recent_upper_wick_average",
    #     "feature_pullback_depth_vs_pre_high_move",
    #     "feature_entry_body_to_previous_bar_body",
    #     "feature_emas_distances_to_recent_bars_ema_distances",
    #     "feature_entry_close_position_vs_previous_close_position",
    #     "feature_price_movement_from_highest_high_to_lowest_low",
    #     "feature_recent_bars_up_trend_pct",
    #     "feature_current_day_high_to_previous_high",
    #     "feature_entry_bar_open_to_ema_9",
    #     "feature_entry_bar_volume_to_recent_bars_average",
    #     "feature_entry_body_to_highest_high_body",
    #     "feature_entry_bar_ema_9_to_vwap",
    #     "feature_volume_since_highest_high_to_volume_before",
    #     "feature_profit_since_open_to_bars_count_since_open",
    # ]

    # promising_features = [f for f in promising_features if f in features]

    # three_condition_results = search_three_condition_rules(
    #     pos,
    #     fp,
    #     promising_features,
    #     max_feature_combos=None,
    # )

    # three_condition_results = remove_near_duplicate_rules(three_condition_results, max_results=30)

    # print_results(three_condition_results, "BEST 3-CONDITION RULES")


if __name__ == "__main__":
    main()
