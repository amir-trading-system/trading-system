import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

pd.set_option('display.max_colwidth', None)

POSITIVE_CSV = "model/training/positive_results.csv"
FALSE_POSITIVE_CSV = "model/training/false_positive_results.csv"

OUTPUT_RESULTS_CSV = "model/training/feature_search_results.csv"
OUTPUT_BEST_CSV = "model/training/best_feature_set.csv"


# =============================
# Load data
# =============================

def load_dataset():
    positive_df = pd.read_csv(POSITIVE_CSV)
    negative_df = pd.read_csv(FALSE_POSITIVE_CSV)

    positive_df["label"] = 1
    negative_df["label"] = 0

    df = pd.concat([positive_df, negative_df], ignore_index=True)

    feature_columns = [
        col for col in df.columns
        if col.startswith("feature_")
    ]

    df = df.dropna(subset=feature_columns + ["label"])

    X = df[feature_columns].copy()
    y = df["label"].astype(int).copy()

    print(f"Total samples: {len(df)}")
    print(f"Positive samples: {(y == 1).sum()}")
    print(f"Negative samples: {(y == 0).sum()}")
    print(f"Total features: {len(feature_columns)}")

    return X, y, feature_columns


# =============================
# Metrics
# =============================

def evaluate_predictions(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    ).ravel()

    positive_pass_rate = tp / (tp + fn) if (tp + fn) else 0.0
    false_positive_reject_rate = tn / (tn + fp) if (tn + fp) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0

    false_positive_rate = fp / (fp + tn) if (fp + tn) else 0.0

    balanced_score = (
        0.5 * positive_pass_rate
        + 0.5 * false_positive_reject_rate
    )

    trading_score = (
        2.00 * positive_pass_rate
        + 1.00 * false_positive_reject_rate
        + 0.25 * precision
        - 0.50 * false_positive_rate
    )

    return {
        "threshold": threshold,
        "positive_pass_rate": positive_pass_rate,
        "false_positive_reject_rate": false_positive_reject_rate,
        "precision": precision,
        "balanced_score": balanced_score,
        "trading_score": trading_score,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


# =============================
# Evaluate one feature set
# =============================

def evaluate_feature_set(
    X,
    y,
    features,
    thresholds=np.arange(0.40, 0.86, 0.05),
    n_splits=5,
    random_state=42,
):
    rows = []

    cv = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    for fold, (train_idx, val_idx) in enumerate(cv.split(X[features], y), start=1):
        X_train = X.iloc[train_idx][features]
        X_val = X.iloc[val_idx][features]
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]

        model = RandomForestClassifier(
            n_estimators=500,
            max_depth=4,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state + fold,
            n_jobs=-1,
        )

        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_val)[:, 1]

        for threshold in thresholds:
            metrics = evaluate_predictions(y_val, y_prob, threshold)
            metrics["fold"] = fold
            rows.append(metrics)

    result = pd.DataFrame(rows)

    summary = (
        result
        .groupby("threshold")
        .agg({
            "positive_pass_rate": "mean",
            "false_positive_reject_rate": "mean",
            "precision": "mean",
            "balanced_score": "mean",
            "trading_score": "mean",
            "tp": "mean",
            "fp": "mean",
            "tn": "mean",
            "fn": "mean",
        })
        .reset_index()
        .sort_values("trading_score", ascending=False)
    )

    best = summary.iloc[0].to_dict()
    best["features"] = tuple(features)
    best["num_features"] = len(features)

    return best


# =============================
# Random feature search
# =============================

def random_feature_search(
    X,
    y,
    candidate_features,
    min_features=6,
    max_features=14,
    n_trials=300,
    random_state=42,
):
    rng = np.random.default_rng(random_state)
    results = []

    for trial in range(n_trials):
        k = int(rng.integers(min_features, max_features + 1))

        features = list(
            rng.choice(
                candidate_features,
                size=k,
                replace=False,
            )
        )

        best = evaluate_feature_set(
            X=X,
            y=y,
            features=features,
            thresholds=[0.55],  # lock threshold
            random_state=random_state,
        )
        if best["positive_pass_rate"] < 0.25:
            continue

        if best["false_positive_reject_rate"] < 0.70:
            continue

        best["trial"] = trial
        results.append(best)

        print(
            f"Trial {trial + 1}/{n_trials} | "
            f"features={k} | "
            f"score={best['trading_score']:.4f} | "
            f"pos_pass={best['positive_pass_rate']:.4f} | "
            f"fp_reject={best['false_positive_reject_rate']:.4f} | "
            f"threshold={best['threshold']:.2f}"
        )

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("trading_score", ascending=False)

    return results_df


# =============================
# Backward elimination
# =============================

def backward_elimination(
    X,
    y,
    initial_features,
    min_features=6,
    random_state=42,
):
    selected = list(initial_features)
    history = []

    current_best = evaluate_feature_set(
        X=X,
        y=y,
        features=selected,
        random_state=random_state,
    )

    best_score = current_best["trading_score"]
    history.append(current_best)

    improved = True

    while improved and len(selected) > min_features:
        improved = False
        candidates = []

        for feature in selected:
            test_features = [f for f in selected if f != feature]

            result = evaluate_feature_set(
                X=X,
                y=y,
                features=test_features,
                random_state=random_state,
            )

            result["removed_feature"] = feature
            candidates.append(result)

        candidates_df = pd.DataFrame(candidates)

        candidates_df = candidates_df[
            (candidates_df["positive_pass_rate"] >= 0.25) &
            (candidates_df["false_positive_reject_rate"] >= 0.70) &
            (candidates_df["precision"] >= 0.60)
        ]

        if candidates_df.empty:
            break

        winner = candidates_df.sort_values(
            "trading_score",
            ascending=False,
        ).iloc[0]

        if winner["trading_score"] > best_score:
            removed_feature = winner["removed_feature"]

            selected.remove(removed_feature)
            best_score = winner["trading_score"]
            history.append(winner.to_dict())
            improved = True

            print(
                f"Removed {removed_feature} | "
                f"new_score={best_score:.4f} | "
                f"features_left={len(selected)}"
            )

    return pd.DataFrame(history).sort_values(
        "trading_score",
        ascending=False,
    )


# =============================
# Main
# =============================

def main():
    X, y, candidate_features = load_dataset()

    max_features = min(14, len(candidate_features))

    random_results = random_feature_search(
        X=X,
        y=y,
        candidate_features=candidate_features,
        min_features=6,
        max_features=max_features,
        n_trials=300,
        random_state=42,
    )
    filtered = random_results[
        (random_results["positive_pass_rate"] >= 0.25) &
        (random_results["false_positive_reject_rate"] >= 0.70)
    ].sort_values("trading_score", ascending=False)

    print(filtered.head(20))

    random_results.to_csv(OUTPUT_RESULTS_CSV, index=False)

    print("\n================ BEST RANDOM RESULTS ================\n")
    print(
        random_results[
            [
                "trading_score",
                "positive_pass_rate",
                "false_positive_reject_rate",
                "precision",
                "threshold",
                "num_features",
                "features",
            ]
        ].head(20)
    )

    best_features = list(random_results.iloc[0]["features"])

    print("\n================ BACKWARD ELIMINATION ================\n")

    backward_results = backward_elimination(
        X=X,
        y=y,
        initial_features=best_features,
        min_features=6,
        random_state=999,
    )

    backward_results.to_csv(OUTPUT_BEST_CSV, index=False)

    best = backward_results.iloc[0]

    print("\n================ FINAL BEST FEATURE SET ================\n")
    print(f"Trading score: {best['trading_score']:.4f}")
    print(f"Positive pass rate: {best['positive_pass_rate']:.4f}")
    print(f"False positive reject rate: {best['false_positive_reject_rate']:.4f}")
    print(f"Precision: {best['precision']:.4f}")
    print(f"Threshold: {best['threshold']:.2f}")
    print(f"Num features: {best['num_features']}")

    print("\nFeatures:")
    for feature in best["features"]:
        print(f"- {feature}")


if __name__ == "__main__":
    main()
