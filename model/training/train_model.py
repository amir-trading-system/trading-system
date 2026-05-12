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

pd.set_option('display.max_colwidth', None)
POSITIVE_CSV = "model/training/positive_results.csv"
FALSE_POSITIVE_CSV = "model/training/false_positive_results.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.3

# CV for feature stability + threshold tuning
CV_SPLITS = 5
CV_REPEATS = 10

THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

# Final stable feature filtering
MIN_MEAN_IMPORTANCE = 0.02
MIN_TOP_K_FREQUENCY = 0.5
TOP_K_FOR_STABILITY = 6
MIN_SELECTED_FEATURES = 5

SELECTED_FEATURES = [
    "feature_current_day_vwap_to_recent_days",
    "feature_current_day_high_to_previous_high",
    "feature_current_day_high_to_recent_days_highs",
    "feature_controlled_volume_entry_quality",
    "feature_overall_legit_trade",
    "feature_entry_close_strength_to_highest_high_close_strength",
]

# Optional hard rules for final decision layer
USE_HARD_RULES = True

# ---------------- NEW: threshold-selection logic ----------------
MIN_POSITIVE_PASS_RATE = 0.50
MIN_FALSE_POSITIVE_REJECT_RATE = 0.45
TRADING_SCORE_FP_WEIGHT = 0.5
TRADING_SCORE_POS_WEIGHT = 0.5

# Output files
TRAIN_SCORED_OUTPUT = "model/training/scored_training_dataset.csv"
POSITIVE_SCORED_OUTPUT = "model/training/positive_results_scored.csv"
FALSE_POSITIVE_SCORED_OUTPUT = "model/training/false_positive_results_scored.csv"
MODEL_INFO_OUTPUT = "model/training/model_info.json"
CV_FEATURE_REPORT_OUTPUT = "model/training/cv_feature_report.csv"
CV_FOLD_REPORT_OUTPUT = "model/training/cv_fold_report.csv"

MODEL_PATH = "model/prod/trade_model.pkl"
IMPUTER_PATH = "model/prod/trade_imputer.pkl"
BUNDLE_PATH = "model/prod/trade_model_bundle.pkl"


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
        # if feature.startswith("feature_"):
        if feature in SELECTED_FEATURES:
            final_shares_columns.append(feature)

    return final_shares_columns


def compute_trading_score(positive_pass_rate, false_positive_reject_rate):
    """
    Trading-friendly threshold selection:
    - require minimum useful recall
    - require minimum useful bad-trade filtering
    - then score thresholds with heavier weight on FP rejection
    """
    if np.isnan(positive_pass_rate) or np.isnan(false_positive_reject_rate):
        return -1.0

    if positive_pass_rate < MIN_POSITIVE_PASS_RATE:
        return -1.0

    if false_positive_reject_rate < MIN_FALSE_POSITIVE_REJECT_RATE:
        return -1.0

    return (
        TRADING_SCORE_FP_WEIGHT * false_positive_reject_rate
        + TRADING_SCORE_POS_WEIGHT * positive_pass_rate
    )


def evaluate_threshold_from_probs(y_true, probs, threshold):
    pred = (probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()

    positive_pass_rate = tp / (tp + fn) if (tp + fn) else np.nan
    false_positive_reject_rate = tn / (tn + fp) if (tn + fp) else np.nan
    balanced_score = np.nanmean([positive_pass_rate, false_positive_reject_rate])
    trading_score = compute_trading_score(
        positive_pass_rate=positive_pass_rate,
        false_positive_reject_rate=false_positive_reject_rate,
    )

    return {
        "threshold": float(threshold),
        "positive_pass_rate": float(positive_pass_rate),
        "false_positive_reject_rate": float(false_positive_reject_rate),
        "balanced_score": float(balanced_score),
        "trading_score": float(trading_score),
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

    valid_results = [r for r in results if r["trading_score"] >= 0]

    if valid_results:
        best = max(
            valid_results,
            key=lambda x: (
                x["trading_score"],
                x["false_positive_reject_rate"],
                x["positive_pass_rate"],
                -abs(x["threshold"] - 0.60),  # gentle tie-break toward middle thresholds
            ),
        )
    else:
        # Fallback: if no threshold passes the floors, choose the best balanced score
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
                "trading_score": best_threshold_result["trading_score"],
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

    rules_pass = bool(apply_hard_rules(pd.DataFrame([row])).iloc[0])
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
        grade = "D"
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

selected_features = choose_stable_features(
    feature_report_df=feature_report_df,
)

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

print("\n================ CV THRESHOLD SUMMARY ================\n")
print(f"Mean trading score: {fold_report_df['trading_score'].mean():.4f}")
print(f"Mean positive pass rate: {fold_report_df['positive_pass_rate'].mean():.4f}")
print(f"Mean false positive reject rate: {fold_report_df['false_positive_reject_rate'].mean():.4f}")

# ------------------------------------------------------------
# FINAL HOLDOUT EVALUATION
# ------------------------------------------------------------

test_probs = final_model.predict_proba(X_test_selected_imp)[:, 1]
test_pred_default = (test_probs >= 0.50).astype(int)
test_pred_best = (test_probs >= chosen_threshold).astype(int)
test_pred_052 = (test_probs >= 0.52).astype(int)
test_pred_055 = (test_probs >= 0.55).astype(int)

print("\n================ HOLDOUT TEST REPORT (threshold=0.50) ================\n")
print(classification_report(y_test_holdout, test_pred_default, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test_holdout, test_pred_default))

print(f"\n================ HOLDOUT TEST REPORT (threshold={chosen_threshold:.2f}) ================\n")
print(classification_report(y_test_holdout, test_pred_best, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test_holdout, test_pred_best))

print("\n================ HOLDOUT TEST REPORT (threshold=threshold=0.52) ================\n")
print(classification_report(y_test_holdout, test_pred_052, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test_holdout, test_pred_052))

print("\n================ HOLDOUT TEST REPORT (threshold=threshold=0.55) ================\n")
print(classification_report(y_test_holdout, test_pred_055, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test_holdout,  test_pred_055))

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
    "cv_mean_trading_score": float(fold_report_df["trading_score"].mean()),
    "cv_std_trading_score": float(fold_report_df["trading_score"].std()),
    "cv_mean_positive_pass_rate": float(fold_report_df["positive_pass_rate"].mean()),
    "cv_mean_false_positive_reject_rate": float(fold_report_df["false_positive_reject_rate"].mean()),
    "min_positive_pass_rate": MIN_POSITIVE_PASS_RATE,
    "min_false_positive_reject_rate": MIN_FALSE_POSITIVE_REJECT_RATE,
    "trading_score_fp_weight": TRADING_SCORE_FP_WEIGHT,
    "trading_score_pos_weight": TRADING_SCORE_POS_WEIGHT,
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
        "min_positive_pass_rate": MIN_POSITIVE_PASS_RATE,
        "min_false_positive_reject_rate": MIN_FALSE_POSITIVE_REJECT_RATE,
        "trading_score_fp_weight": TRADING_SCORE_FP_WEIGHT,
        "trading_score_pos_weight": TRADING_SCORE_POS_WEIGHT,
    },
    BUNDLE_PATH,
)

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

# ------------------------------------------------------------
# SAVE HOLDOUT PREDICTIONS FOR DISTRIBUTION ANALYSIS
# ------------------------------------------------------------

y_pred_proba = final_model.predict_proba(X_test_selected_imp)[:, 1]
THRESHOLD = chosen_threshold

y_pred = (y_pred_proba >= THRESHOLD).astype(int)
df_test = pd.DataFrame({
    "label": y_test_holdout.values,
    "probability": y_pred_proba,
    "prediction": y_pred,
})

df_test.to_csv("model/training/test_predictions.csv", index=False)
