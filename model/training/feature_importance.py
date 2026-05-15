import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import ks_2samp


pd.set_option('display.max_colwidth', None)
POSITIVE_FILE = "model/training/positive_results.csv"
FALSE_POSITIVE_FILE = "model/training/false_positive_results.csv"

SCORE_COLUMN = "score"
RULES_PASS_COLUMN = "feature_overall_legit_trade"

# Use this if you want to focus only on hard false positives that still pass rules.
ONLY_FALSE_POSITIVES_THAT_PASS_RULES = True

# Use this if you want to focus only on important FPs.
# MIN_FP_SCORE = None
# Example:
# MIN_FP_SCORE = 52
MIN_FP_SCORE = 60

MIN_NON_NULL_ROWS_PER_CLASS = 10

QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]


def clean_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float)

    if series.dtype == "object":
        series = (
            series.astype(str)
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
        pd.to_numeric(series, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .astype(float)
    )


def normalize_bool(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )


def feature_columns(df: pd.DataFrame) -> list[str]:
    ignored = {
        "label",
        "symbol",
        "original_bar_time",
        "expected_confirmation_bar_time",
        "highest_high_one_minute_bar_time",
        "probability",
        "grade",
        "pass_recommended",
        "rules_pass",
        SCORE_COLUMN,
    }

    cols = []

    for col in df.columns:
        if col in ignored:
            continue

        if col.startswith("feature_") or col in {"total_volume", "entry_bar_volume"}:
            s = clean_numeric(df[col])
            if s.notna().sum() >= MIN_NON_NULL_ROWS_PER_CLASS:
                if s.dropna().nunique() > 1:
                    cols.append(col)

    return cols


def cohen_d(pos_values: pd.Series, fp_values: pd.Series) -> float:
    pos_values = pos_values.dropna()
    fp_values = fp_values.dropna()

    n_pos = len(pos_values)
    n_fp = len(fp_values)

    if n_pos < 2 or n_fp < 2:
        return np.nan

    pos_std = pos_values.std(ddof=1)
    fp_std = fp_values.std(ddof=1)

    pooled_std = np.sqrt(
        ((n_pos - 1) * pos_std ** 2 + (n_fp - 1) * fp_std ** 2)
        / (n_pos + n_fp - 2)
    )

    if pooled_std == 0 or not np.isfinite(pooled_std):
        return np.nan

    return (pos_values.mean() - fp_values.mean()) / pooled_std


def safe_auc(pos_values: pd.Series, fp_values: pd.Series) -> float:
    data = pd.concat([
        pd.DataFrame({"value": pos_values, "label": 1}),
        pd.DataFrame({"value": fp_values, "label": 0}),
    ]).dropna()

    if data["label"].nunique() < 2:
        return np.nan

    if data["value"].nunique() <= 1:
        return np.nan

    auc = roc_auc_score(data["label"], data["value"])

    # Make separation direction independent.
    # 0.90 and 0.10 both mean strong separation, just opposite direction.
    return float(max(auc, 1.0 - auc))


def auc_direction(pos_values: pd.Series, fp_values: pd.Series) -> str:
    data = pd.concat([
        pd.DataFrame({"value": pos_values, "label": 1}),
        pd.DataFrame({"value": fp_values, "label": 0}),
    ]).dropna()

    if data["label"].nunique() < 2 or data["value"].nunique() <= 1:
        return "unknown"

    auc = roc_auc_score(data["label"], data["value"])

    if auc >= 0.5:
        return "higher_in_positives"
    return "higher_in_false_positives"


def best_single_threshold(pos_values: pd.Series, fp_values: pd.Series):
    """
    Finds a simple one-feature rule:
        feature <= threshold
    or:
        feature >= threshold

    The objective heavily penalizes killed positives.
    """

    pos_values = pos_values.dropna()
    fp_values = fp_values.dropna()

    combined = pd.concat([pos_values, fp_values]).dropna()

    if combined.nunique() <= 1:
        return None

    thresholds = sorted(set(np.quantile(combined, np.linspace(0.02, 0.98, 49))))

    best = {}

    for threshold in thresholds:
        for op in ["<=", ">="]:
            if op == "<=":
                pos_killed = int((pos_values <= threshold).sum())
                fp_caught = int((fp_values <= threshold).sum())
            else:
                pos_killed = int((pos_values >= threshold).sum())
                fp_caught = int((fp_values >= threshold).sum())

            # Hard-rule style scoring:
            # prefer catching FPs while killing 0 positives.
            score = fp_caught - 20 * pos_killed

            result = {
                "op": op,
                "threshold": float(threshold),
                "fp_caught": fp_caught,
                "pos_killed": pos_killed,
                "rule_score": score,
            }

            if not best or result["rule_score"] > best["rule_score"]:
                best = result

    return best


def analyze_feature(pos_df: pd.DataFrame, fp_df: pd.DataFrame, feature: str) -> dict:
    pos_values = clean_numeric(pos_df[feature])
    fp_values = clean_numeric(fp_df[feature])

    pos_values = pos_values.dropna()
    fp_values = fp_values.dropna()

    if len(pos_values) < MIN_NON_NULL_ROWS_PER_CLASS or len(fp_values) < MIN_NON_NULL_ROWS_PER_CLASS:
        return {}

    pos_quantiles = pos_values.quantile(QUANTILES)
    fp_quantiles = fp_values.quantile(QUANTILES)

    ks_stat, ks_pvalue = ks_2samp(pos_values, fp_values)

    auc_sep = safe_auc(pos_values, fp_values)
    direction = auc_direction(pos_values, fp_values)
    d = cohen_d(pos_values, fp_values)
    best_threshold = best_single_threshold(pos_values, fp_values)

    pos_median = pos_values.median()
    fp_median = fp_values.median()

    median_diff = pos_median - fp_median
    median_ratio = np.nan
    if fp_median != 0:
        median_ratio = pos_median / fp_median

    result = {
        "feature": feature,
        "pos_count": len(pos_values),
        "fp_count": len(fp_values),

        "pos_mean": pos_values.mean(),
        "fp_mean": fp_values.mean(),
        "mean_diff_pos_minus_fp": pos_values.mean() - fp_values.mean(),

        "pos_median": pos_median,
        "fp_median": fp_median,
        "median_diff_pos_minus_fp": median_diff,
        "median_ratio_pos_to_fp": median_ratio,

        "cohen_d_pos_minus_fp": d,
        "abs_cohen_d": abs(d) if pd.notna(d) else np.nan,

        "ks_stat": ks_stat,
        "ks_pvalue": ks_pvalue,

        "auc_separation": auc_sep,
        "auc_direction": direction,
    }

    for q in QUANTILES:
        key = str(int(q * 100))
        result[f"pos_q{key}"] = pos_quantiles.loc[q]
        result[f"fp_q{key}"] = fp_quantiles.loc[q]
        result[f"q{key}_diff_pos_minus_fp"] = pos_quantiles.loc[q] - fp_quantiles.loc[q]

    if best_threshold:
        result["best_rule_op"] = best_threshold["op"]
        result["best_rule_threshold"] = best_threshold["threshold"]
        result["best_rule_fp_caught"] = best_threshold["fp_caught"]
        result["best_rule_pos_killed"] = best_threshold["pos_killed"]
        result["best_rule_score"] = best_threshold["rule_score"]
    else:
        result["best_rule_op"] = None
        result["best_rule_threshold"] = np.nan
        result["best_rule_fp_caught"] = 0
        result["best_rule_pos_killed"] = 0
        result["best_rule_score"] = np.nan

    return result


def main():
    pos_df = pd.read_csv(POSITIVE_FILE)
    fp_df = pd.read_csv(FALSE_POSITIVE_FILE)

    if ONLY_FALSE_POSITIVES_THAT_PASS_RULES:
        if RULES_PASS_COLUMN in fp_df.columns:
            fp_df = fp_df[normalize_bool(fp_df[RULES_PASS_COLUMN])].copy()
        elif "rules_pass" in fp_df.columns:
            fp_df = fp_df[normalize_bool(fp_df["rules_pass"])].copy()

    if MIN_FP_SCORE is not None and SCORE_COLUMN in fp_df.columns:
        fp_df = fp_df[clean_numeric(fp_df[SCORE_COLUMN]) >= MIN_FP_SCORE].copy()

    combined = pd.concat([pos_df, fp_df], ignore_index=True)
    features = feature_columns(combined)

    print(f"Positive rows used: {len(pos_df)}")
    print(f"False-positive rows used: {len(fp_df)}")
    print(f"Features analyzed: {len(features)}")

    rows = []

    for feature in features:
        row = analyze_feature(pos_df, fp_df, feature)
        if row:
            rows.append(row)

    report = pd.DataFrame(rows)

    if report.empty:
        print("No usable features found.")
        return

    report = report.sort_values(
        by=[
            "auc_separation",
            "ks_stat",
            "abs_cohen_d",
            "best_rule_score",
        ],
        ascending=[False, False, False, False],
    )

    report.to_csv("feature_difference_report.csv", index=False)

    print("\nTop features by distribution separation:")
    print(
        report[
            [
                "feature",
                "auc_separation",
                "auc_direction",
                "ks_stat",
                "abs_cohen_d",
                "pos_median",
                "fp_median",
                "median_diff_pos_minus_fp",
                "best_rule_op",
                "best_rule_threshold",
                "best_rule_fp_caught",
                "best_rule_pos_killed",
            ]
        ].head(30).to_string(index=False)
    )

    print("\nSaved: feature_difference_report.csv")


if __name__ == "__main__":
    main()
