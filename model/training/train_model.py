import json
import os
from pathlib import Path
from collections import defaultdict

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split


# ============================================================
# CONFIG
# ============================================================

POSITIVE_CSV = "model/training/positive_results.csv"
FALSE_POSITIVE_CSV = "model/training/false_positive_results.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.30

# CV for feature stability + threshold tuning
CV_SPLITS = 5
CV_REPEATS = 10

THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

# Final stable feature filtering
MIN_MEAN_IMPORTANCE = 0.02
MIN_TOP_K_FREQUENCY = 0.5
TOP_K_FOR_STABILITY = 20
MIN_SELECTED_FEATURES = 8

# Optional hard rules for final decision layer
USE_HARD_RULES = True

# Output files
TRAIN_SCORED_OUTPUT = "model/training/scored_training_dataset.csv"
POSITIVE_SCORED_OUTPUT = "model/training/positive_results_scored.csv"
FALSE_POSITIVE_SCORED_OUTPUT = "model/training/false_positive_results_scored.csv"
MODEL_INFO_OUTPUT = "model/training/model_info.json"
CV_FEATURE_REPORT_OUTPUT = "model/training/cv_feature_report.csv"
CV_FOLD_REPORT_OUTPUT = "model/training/cv_fold_report.csv"

MODEL_PATH = "model/trade_model.pkl"
IMPUTER_PATH = "model/trade_imputer.pkl"
BUNDLE_PATH = "model/trade_model_bundle.pkl"


# ============================================================
# HELPERS
# ============================================================

def cleanup_old_outputs():
    for path in [
        TRAIN_SCORED_OUTPUT,
        POSITIVE_SCORED_OUTPUT,
        FALSE_POSITIVE_SCORED_OUTPUT,
        MODEL_INFO_OUTPUT,
        CV_FEATURE_REPORT_OUTPUT,
        CV_FOLD_REPORT_OUTPUT,
        MODEL_PATH,
        IMPUTER_PATH,
        BUNDLE_PATH,
    ]:
        if os.path.exists(path):
            os.remove(path)


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def convert_bool_like_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts object columns that look like booleans to numeric 0/1.
    """
    temp = df.copy()

    for col in temp.columns:
        if temp[col].dtype == object:
            lowered = temp[col].astype(str).str.strip().str.lower()
            unique_values = set(lowered.dropna().unique())

            if unique_values.issubset({"true", "false"}):
                temp[col] = lowered.map({"true": 1.0, "false": 0.0})

    return temp


def find_candidate_numeric_features(pos_df: pd.DataFrame, neg_df: pd.DataFrame):
    """
    Find all shared numeric/bool columns automatically.
    Do not hardcode a final list here.
    """
    pos_num = set(pos_df.select_dtypes(include=[np.number, "bool"]).columns)
    neg_num = set(neg_df.select_dtypes(include=[np.number, "bool"]).columns)
    shared = sorted((pos_num & neg_num) - {"label"})

    final_shares_columns = []
    for feature in shared:
        if str(feature) in [
            "feature_volume_per_minute_to_bar_volume_above_threshold",
            "feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold",
            "feature_bars_without_movement_pct_above_threshold",
            "feature_potential_bar_low_close_to_open",
            "feature_volume_average_goes_up_pct",
            "feature_overlapped_bars_since_market_open_pct",
            "feature_bars_with_rejection_inside_entry_bar_range_pct",
            "feature_positive_vs_negative_volume",
            "feature_positive_vs_negative_movement",
            "feature_has_positive_more_than_negative_bars",
            "feature_price_minus_vwap_at_entry",
            "feature_histogram_negative_momentum_pct",
            "feature_bars_with_at_least_50_pct_wick_pct",
            "feature_bars_with_lower_volume_average_pct",
            "feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open", #[6-2] [5-11]
            "feature_entry_bar_strengh_pct",
            "feature_strong_bars_above_volume_average_pct",
            "feature_high_volume_bars_with_rejection_pct", #[8-0] [6-10]
            "feature_entry_strength_vs_avg", #[8-0] [6-10]
            "feature_volume_per_minute_to_bar_volume", #[8-0] [5-11]
            "feature_crossed_highest_high",
            "feature_entry_bar_volume_average_above_threshold",
            "feature_volume_avergae_above_10000_pct_above_threshold",
            "feature_crossed_highest_high_since_market_open",
        ]:
            final_shares_columns.append(feature)

    return final_shares_columns


def evaluate_threshold_from_probs(y_true, probs, threshold):
    pred = (probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()

    positive_pass_rate = tp / (tp + fn) if (tp + fn) else np.nan
    false_positive_reject_rate = tn / (tn + fp) if (tn + fp) else np.nan
    balanced_score = np.nanmean([positive_pass_rate, false_positive_reject_rate])

    return {
        "threshold": float(threshold),
        "positive_pass_rate": float(positive_pass_rate),
        "false_positive_reject_rate": float(false_positive_reject_rate),
        "balanced_score": float(balanced_score),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def train_rf_model(X_train: pd.DataFrame, y_train: pd.Series, random_state: int):
    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=7,
        min_samples_leaf=4,
        min_samples_split=8,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def select_best_threshold(y_true, probs):
    results = [evaluate_threshold_from_probs(y_true, probs, th) for th in THRESHOLDS]
    best = max(results, key=lambda x: x["balanced_score"])
    return best, results


def run_feature_stability_cv(X: pd.DataFrame, y: pd.Series, candidate_features: list[str]):
    """
    Run repeated CV on the training set only.
    Tracks:
    - best threshold per fold
    - fold scores
    - feature importances
    - how often a feature appears in top-k importance
    """
    cv = RepeatedStratifiedKFold(
        n_splits=CV_SPLITS,
        n_repeats=CV_REPEATS,
        random_state=RANDOM_STATE,
    )

    feature_importances = defaultdict(list)
    feature_topk_hits = defaultdict(int)
    fold_rows = []

    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y), start=1):
        X_train = X.iloc[train_idx][candidate_features].copy()
        X_val = X.iloc[val_idx][candidate_features].copy()
        y_train = y.iloc[train_idx].copy()
        y_val = y.iloc[val_idx].copy()

        imputer = SimpleImputer(strategy="median")
        X_train_imp = pd.DataFrame(
            imputer.fit_transform(X_train),
            columns=candidate_features,
            index=X_train.index,
        )
        X_val_imp = pd.DataFrame(
            imputer.transform(X_val),
            columns=candidate_features,
            index=X_val.index,
        )

        model = train_rf_model(X_train_imp, y_train, RANDOM_STATE + fold_idx)

        val_probs = model.predict_proba(X_val_imp)[:, 1]
        best_threshold_result, threshold_rows = select_best_threshold(y_val.values, val_probs)

        importances = pd.Series(
            model.feature_importances_,
            index=candidate_features,
        ).sort_values(ascending=False)

        top_k_features = set(importances.head(TOP_K_FOR_STABILITY).index)

        for feature, importance in importances.items():
            feature_importances[feature].append(float(importance))
            if feature in top_k_features:
                feature_topk_hits[feature] += 1

        fold_rows.append(
            {
                "fold": fold_idx,
                "best_threshold": best_threshold_result["threshold"],
                "positive_pass_rate": best_threshold_result["positive_pass_rate"],
                "false_positive_reject_rate": best_threshold_result["false_positive_reject_rate"],
                "balanced_score": best_threshold_result["balanced_score"],
                "tn": best_threshold_result["tn"],
                "fp": best_threshold_result["fp"],
                "fn": best_threshold_result["fn"],
                "tp": best_threshold_result["tp"],
            }
        )

    total_folds = len(fold_rows)

    feature_rows = []
    for feature in candidate_features:
        vals = feature_importances[feature]
        feature_rows.append(
            {
                "feature": feature,
                "mean_importance": float(np.mean(vals)),
                "std_importance": float(np.std(vals)),
                "top_k_frequency": float(feature_topk_hits[feature] / total_folds),
            }
        )

    feature_report_df = pd.DataFrame(feature_rows).sort_values(
        ["mean_importance", "top_k_frequency"],
        ascending=[False, False],
    )

    fold_report_df = pd.DataFrame(fold_rows)

    return feature_report_df, fold_report_df


def choose_stable_features(feature_report_df: pd.DataFrame):
    selected = feature_report_df[
        (feature_report_df["mean_importance"] >= MIN_MEAN_IMPORTANCE) &
        (feature_report_df["top_k_frequency"] >= MIN_TOP_K_FREQUENCY)
    ]["feature"].tolist()

    # fallback: always keep at least a minimum number of strongest features
    if len(selected) < MIN_SELECTED_FEATURES:
        selected = feature_report_df.head(MIN_SELECTED_FEATURES)["feature"].tolist()

    return selected


def apply_hard_rules(df: pd.DataFrame) -> pd.Series:
    """
    Return True for rows that are allowed to pass.
    Adjust rules only if they generalize.
    """
    allowed = pd.Series(True, index=df.index)

    if not USE_HARD_RULES:
        return allowed

    # Example from your recent filter idea.
    weak_col = "feature_weak_bars_to_bars_since_highest_high_to_total_bars"
    if weak_col in df.columns:
        allowed &= df[weak_col].fillna(0) < 0.95

    return allowed


def score_dataframe(raw_df, features, model, imputer, threshold, label_value=None):
    temp = raw_df.copy()

    for col in features:
        if col not in temp.columns:
            temp[col] = np.nan

    temp_x = temp[features].copy()
    temp_x_imputed = pd.DataFrame(
        imputer.transform(temp_x),
        columns=features,
        index=temp.index,
    )

    probs = model.predict_proba(temp_x_imputed)[:, 1]
    temp["probability"] = probs
    temp["score"] = (temp["probability"] * 100.0).round(2)

    model_pass = temp["probability"] >= threshold
    rules_pass = apply_hard_rules(temp)

    temp["model_pass"] = model_pass
    temp["rules_pass"] = rules_pass
    temp["pass_recommended"] = model_pass & rules_pass

    if label_value is not None:
        temp["label"] = label_value

    return temp


def probability_from_row(row: pd.Series, features, model, imputer) -> float:
    row_dict = {}
    for col in features:
        row_dict[col] = row[col] if col in row.index else np.nan

    row_df = pd.DataFrame([row_dict], columns=features)
    row_df_imputed = pd.DataFrame(
        imputer.transform(row_df),
        columns=features,
    )

    prob = float(model.predict_proba(row_df_imputed)[0, 1])
    return prob


def classify_row(row: pd.Series, features, model, imputer, threshold):
    prob = probability_from_row(row, features, model, imputer)
    score = round(prob * 100.0, 2)

    rules_pass = bool(apply_hard_rules(pd.DataFrame([row]))[0])
    passed = (prob >= threshold) and rules_pass

    if prob >= 0.85:
        grade = "A+"
    elif prob >= 0.75:
        grade = "A"
    elif prob >= 0.65:
        grade = "B"
    elif prob >= threshold:
        grade = "C"
    elif prob >= threshold - 0.03:
        grade = "D"   # near-miss
    else:
        grade = "REJECT"

    return {
        "probability": round(prob, 6),
        "score": score,
        "threshold": threshold,
        "rules_pass": rules_pass,
        "pass_recommended": passed,
        "grade": grade,
    }


# ============================================================
# MAIN
# ============================================================

cleanup_old_outputs()

pos_path = Path(POSITIVE_CSV)
neg_path = Path(FALSE_POSITIVE_CSV)

if not pos_path.exists():
    raise FileNotFoundError(f"Could not find {POSITIVE_CSV}")
if not neg_path.exists():
    raise FileNotFoundError(f"Could not find {FALSE_POSITIVE_CSV}")

positive_df = pd.read_csv(pos_path)
false_positive_df = pd.read_csv(neg_path)

positive_df["label"] = 1
false_positive_df["label"] = 0

positive_df = convert_bool_like_columns(positive_df)
false_positive_df = convert_bool_like_columns(false_positive_df)

positive_raw = positive_df.copy()
false_positive_raw = false_positive_df.copy()

candidate_features = find_candidate_numeric_features(positive_df, false_positive_df)
if not candidate_features:
    raise ValueError("No shared numeric features found.")

df = pd.concat([positive_df, false_positive_df], ignore_index=True).copy()
X_all = df[candidate_features].copy()
y_all = df["label"].copy()

# ------------------------------------------------------------
# FINAL HOLDOUT SPLIT
# ------------------------------------------------------------

X_train_full, X_test_holdout, y_train_full, y_test_holdout = train_test_split(
    X_all,
    y_all,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y_all,
)

print("\n================ CANDIDATE FEATURES ================\n")
print(f"Total candidate features: {len(candidate_features)}")

# ------------------------------------------------------------
# CV FEATURE STABILITY ON TRAINING SET ONLY
# ------------------------------------------------------------

feature_report_df, fold_report_df = run_feature_stability_cv(
    X_train_full,
    y_train_full,
    candidate_features,
)

selected_features = choose_stable_features(feature_report_df)

print("\n================ FEATURE STABILITY REPORT ================\n")
print(feature_report_df.head(50))
print("\nSelected stable features:")
for f in selected_features:
    print(f"- {f}")

print("\n================ CV FOLD REPORT ================\n")
print(fold_report_df.describe(include="all"))

# ------------------------------------------------------------
# TRAIN FINAL MODEL ON TRAINING SET USING STABLE FEATURES
# ------------------------------------------------------------

final_imputer = SimpleImputer(strategy="median")

X_train_selected = X_train_full[selected_features].copy()
X_test_selected = X_test_holdout[selected_features].copy()

X_train_selected_imp = pd.DataFrame(
    final_imputer.fit_transform(X_train_selected),
    columns=selected_features,
    index=X_train_selected.index,
)

X_test_selected_imp = pd.DataFrame(
    final_imputer.transform(X_test_selected),
    columns=selected_features,
    index=X_test_selected.index,
)

final_model = train_rf_model(
    X_train_selected_imp,
    y_train_full,
    RANDOM_STATE,
)

# ------------------------------------------------------------
# CHOOSE THRESHOLD ON TRAINING SET OUT-OF-FOLD STYLE SUMMARY
# ------------------------------------------------------------

chosen_threshold = float(fold_report_df["best_threshold"].median())

print("\n================ CHOSEN THRESHOLD ================\n")
print(f"Median best CV threshold: {chosen_threshold:.2f}")

# ------------------------------------------------------------
# FINAL HOLDOUT EVALUATION
# ------------------------------------------------------------

test_probs = final_model.predict_proba(X_test_selected_imp)[:, 1]
test_pred_default = (test_probs >= 0.50).astype(int)
test_pred_best = (test_probs >= chosen_threshold).astype(int)

print("\n================ HOLDOUT TEST REPORT (threshold=0.50) ================\n")
print(classification_report(y_test_holdout, test_pred_default, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test_holdout, test_pred_default))

print(f"\n================ HOLDOUT TEST REPORT (threshold={chosen_threshold:.2f}) ================\n")
print(classification_report(y_test_holdout, test_pred_best, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test_holdout, test_pred_best))

# ------------------------------------------------------------
# FINAL FEATURE IMPORTANCE
# ------------------------------------------------------------

final_feature_importance = pd.Series(
    final_model.feature_importances_,
    index=selected_features,
).sort_values(ascending=False)

print("\n================ FINAL FEATURE IMPORTANCE ================\n")
print(final_feature_importance.head(100))

# ------------------------------------------------------------
# SCORE FULL DATASET + ORIGINAL FILES
# ------------------------------------------------------------

# fit scoring imputer/model on ALL DATA using selected features
full_imputer = SimpleImputer(strategy="median")
X_all_selected_imp = pd.DataFrame(
    full_imputer.fit_transform(X_all[selected_features]),
    columns=selected_features,
    index=X_all.index,
)

full_model = train_rf_model(
    X_all_selected_imp,
    y_all,
    RANDOM_STATE,
)

full_probs = full_model.predict_proba(X_all_selected_imp)[:, 1]

scored_df = df.copy()
scored_df["probability"] = full_probs
scored_df["score"] = (scored_df["probability"] * 100.0).round(2)
scored_df["model_pass"] = scored_df["probability"] >= chosen_threshold
scored_df["rules_pass"] = apply_hard_rules(scored_df)
scored_df["pass_recommended"] = scored_df["model_pass"] & scored_df["rules_pass"]

positive_scored = score_dataframe(
    positive_raw,
    selected_features,
    full_model,
    full_imputer,
    chosen_threshold,
    label_value=1,
)
false_positive_scored = score_dataframe(
    false_positive_raw,
    selected_features,
    full_model,
    full_imputer,
    chosen_threshold,
    label_value=0,
)

# ------------------------------------------------------------
# SAVE OUTPUTS
# ------------------------------------------------------------

scored_df.to_csv(TRAIN_SCORED_OUTPUT, index=False)
positive_scored.to_csv(POSITIVE_SCORED_OUTPUT, index=False)
false_positive_scored.to_csv(FALSE_POSITIVE_SCORED_OUTPUT, index=False)
feature_report_df.to_csv(CV_FEATURE_REPORT_OUTPUT, index=False)
fold_report_df.to_csv(CV_FOLD_REPORT_OUTPUT, index=False)

model_info = {
    "candidate_feature_count": len(candidate_features),
    "selected_feature_count": len(selected_features),
    "selected_features": selected_features,
    "chosen_threshold": chosen_threshold,
    "cv_mean_balanced_score": float(fold_report_df["balanced_score"].mean()),
    "cv_std_balanced_score": float(fold_report_df["balanced_score"].std()),
    "cv_mean_positive_pass_rate": float(fold_report_df["positive_pass_rate"].mean()),
    "cv_mean_false_positive_reject_rate": float(fold_report_df["false_positive_reject_rate"].mean()),
    "final_holdout_threshold": chosen_threshold,
    "top_25_feature_importance": final_feature_importance.head(25).to_dict(),
    "random_state": RANDOM_STATE,
    "test_size": TEST_SIZE,
    "cv_splits": CV_SPLITS,
    "cv_repeats": CV_REPEATS,
}

with open(MODEL_INFO_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(model_info, f, indent=2)

joblib.dump(full_model, MODEL_PATH)
joblib.dump(full_imputer, IMPUTER_PATH)
joblib.dump(
    {
        "features": selected_features,
        "threshold": chosen_threshold,
        "use_hard_rules": USE_HARD_RULES,
    },
    BUNDLE_PATH,
)

print("\n================ FILES SAVED ================\n")
print(TRAIN_SCORED_OUTPUT)
print(POSITIVE_SCORED_OUTPUT)
print(FALSE_POSITIVE_SCORED_OUTPUT)
print(CV_FEATURE_REPORT_OUTPUT)
print(CV_FOLD_REPORT_OUTPUT)
print(MODEL_INFO_OUTPUT)
print(MODEL_PATH)
print(IMPUTER_PATH)
print(BUNDLE_PATH)

# ------------------------------------------------------------
# SAMPLE LIVE OUTPUT
# ------------------------------------------------------------

print("\n================ SAMPLE LIVE OUTPUT ================\n")
sample_row = positive_scored.iloc[0]
classified_row = classify_row(
    sample_row,
    selected_features,
    full_model,
    full_imputer,
    chosen_threshold,
)
print(classified_row)
