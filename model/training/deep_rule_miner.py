# pylint: skip-file
# type: ignore
#!/usr/bin/env python3
"""
Deep zero-FP positive rule miner for hard_rules.py + positive/false-positive CSV files.

COMMAND:
python -m model.training.deep_rule_miner \
  --outdir model/training/mining_results \
  --time-budget-minutes 360 \
  --max-depth 24 \
  --n-estimators 1800 \
  --beam-width 6000 \
  --beam-max-atoms 1400 \
  --beam-max-conditions 24 \
  --reason-max-conditions 6 \
  --reason-top-k 2500 \
  --min-pos-broad 25 \
  --min-pos-untagged 10 \
  --min-untagged 0 \
  --max-selected-rules 60 \
  --min-new-untagged 5 \
  --local-expansion \
  --local-expansion-trials 6000 \
  --n-jobs 4

Purpose
-------
Find candidate success_patterns / positive_reason_groups rules that:
  - cover positive rows,
  - cover 0 false-positive rows,
  - prioritize the broadest possible 0-FP coverage across all positives,
  - still report untagged coverage,
  - optionally refine existing success reasons.

This script is designed for long local runs: 30 minutes to 3+ hours.

Typical command
---------------
python deep_rule_miner.py \
  --outdir mining_out_88 \
  --max-depth 20 \
  --time-budget-minutes 180 \
  --n-jobs -1

Important notes
---------------
1. By default, the script excludes likely target/leakage columns like:
   feature_overall_legit_trade
   because that column can make the search trivial and not production-useful.

2. The script imports your hard_rules.py and calls success_patterns(features_data)
   row by row to determine which positives are currently tagged and which are untagged.

3. It writes CSV files with candidate rules and selected greedy rule sets.

4. The generated conditions are intentionally raw thresholds. You should manually review
   behavior meaning before adding them to production.

Dependencies
------------
pip install pandas numpy scikit-learn joblib tqdm
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import gc
import math
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier, _tree
from tqdm import tqdm


# ======================================================================================
# Config
# ======================================================================================

DEFAULT_EXCLUDE_PATTERNS = [
    r"^feature_overall_legit_trade$",
    # Keep mining on raw feature_* columns only, but exclude known target/meta score features.
    r"^feature_.*positive_score$",
    r"^feature_.*positive_group_score$",
    r"^feature_.*soft_positive_group_score$",
    r"^feature_.*strong_positive_group_score$",
]

DEFAULT_META_COLS = {
    "symbol",
    "ticker",
    "date",
    "datetime",
    "timestamp",
    "entry_time",
    "entry_datetime",
    "trade_id",
    "id",
    "result",
    "label",
    "target",
    "is_positive",
    "is_false_positive",
}


@dataclass(frozen=True)
class Atom:
    feature: str
    op: str
    threshold: float

    def expr(self, var_name: Optional[str] = None) -> str:
        name = var_name or feature_to_var(self.feature)
        if self.op == "<=":
            return f"{name} <= {self.threshold:.10g}"
        if self.op == ">":
            return f"{name} > {self.threshold:.10g}"
        raise ValueError(f"Unsupported op: {self.op}")

    def key(self) -> Tuple[str, str, float]:
        return (self.feature, self.op, round(float(self.threshold), 12))


@dataclass
class Rule:
    name: str
    atoms: List[Atom]
    pos_count: int
    fp_count: int
    untagged_pos_count: int
    tagged_pos_count: int
    score: float
    source: str
    base_reason: Optional[str] = None

    def condition_str(self) -> str:
        return " and ".join(a.expr() for a in self.atoms)

    def python_if_block(self, reason_name: Optional[str] = None, indent: str = "    ") -> str:
        reason_name = reason_name or self.name
        lines = [f"{indent}if ("]
        if self.base_reason:
            lines.append(f'{indent}    "{self.base_reason}" in reasons')
            for atom in self.atoms:
                lines.append(f"{indent}    and {atom.expr()}")
        else:
            for i, atom in enumerate(self.atoms):
                prefix = "" if i == 0 else "and "
                lines.append(f"{indent}    {prefix}{atom.expr()}")
        lines.append(f"{indent}):")
        lines.append(f"{indent}    score += 1")
        lines.append(f'{indent}    reasons.append("{reason_name}")')
        return "\n".join(lines)


# ======================================================================================
# Utilities
# ======================================================================================

def feature_to_var(feature: str) -> str:
    if feature.startswith("feature_"):
        return feature[len("feature_"):]
    return feature


def load_hard_rules(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("loaded_hard_rules", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import hard_rules from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["loaded_hard_rules"] = module
    spec.loader.exec_module(module)
    return module


def get_success_patterns_func(module: Any) -> Callable[[Dict[str, Any]], Tuple[int, List[str]]]:
    if not hasattr(module, "success_patterns"):
        raise AttributeError("hard_rules.py does not contain success_patterns(features_data)")
    fn = getattr(module, "success_patterns")
    return fn


def safe_success_patterns(fn: Callable, features: Dict[str, Any]) -> Tuple[int, List[str]]:
    try:
        out = fn(features)
        if isinstance(out, tuple) and len(out) >= 2:
            score, reasons = out[0], out[1]
            if reasons is None:
                reasons = []
            return int(score), list(reasons)
        if isinstance(out, list):
            return len(out), list(out)
        if isinstance(out, bool):
            return int(out), []
        return int(out), []
    except Exception:
        # If your success_patterns can fail because a feature is missing, treat as no tag.
        # You can change this to raise if you prefer strict debugging.
        return 0, []


def normalize_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Convert bools to 0/1.
    for c in out.columns:
        if out[c].dtype == bool:
            out[c] = out[c].astype(float)

    # Convert numeric-like objects.
    for c in out.columns:
        if out[c].dtype == object:
            converted = pd.to_numeric(out[c], errors="coerce")
            # Keep conversion only if at least 80% non-null after conversion.
            if converted.notna().mean() >= 0.80:
                out[c] = converted

    # Replace inf values with nan.
    num_cols = out.select_dtypes(include=[np.number]).columns
    out[num_cols] = out[num_cols].replace([np.inf, -np.inf], np.nan)

    # Fill numeric nan with median, then 0 fallback.
    for c in num_cols:
        med = out[c].median()
        if pd.isna(med):
            med = 0.0
        out[c] = out[c].fillna(med)

    return out


def discover_feature_cols(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    exclude_regexes: Sequence[str],
) -> List[str]:
    common = [c for c in pos_df.columns if c in fp_df.columns]
    cols = []
    compiled = [re.compile(p) for p in exclude_regexes]

    for c in common:
        # Strict mode for this version: mine ONLY raw columns that start with feature_.
        if not c.startswith("feature_"):
            continue
        if c in DEFAULT_META_COLS:
            continue
        if any(rx.search(c) for rx in compiled):
            continue
        if not pd.api.types.is_numeric_dtype(pos_df[c]) or not pd.api.types.is_numeric_dtype(fp_df[c]):
            continue
        # Avoid constant columns.
        combined = pd.concat([pos_df[c], fp_df[c]], axis=0)
        if combined.nunique(dropna=True) <= 1:
            continue
        cols.append(c)

    return cols


def row_to_features(row: pd.Series) -> Dict[str, Any]:
    return row.to_dict()


def evaluate_current_tags(
    hard_rules_path: Path,
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, List[List[str]], List[List[str]]]:
    module = load_hard_rules(hard_rules_path)
    success_fn = get_success_patterns_func(module)

    # itertuples(..., name=None) is materially faster and lighter than iterrows().
    pos_cols = list(pos_df.columns)
    fp_cols = list(fp_df.columns)

    pos_scores = []
    pos_reasons = []
    for values in tqdm(pos_df.itertuples(index=False, name=None), total=len(pos_df), desc="Evaluating positives with success_patterns"):
        s, r = safe_success_patterns(success_fn, dict(zip(pos_cols, values)))
        pos_scores.append(s)
        pos_reasons.append(r)

    fp_scores = []
    fp_reasons = []
    for values in tqdm(fp_df.itertuples(index=False, name=None), total=len(fp_df), desc="Evaluating FPs with success_patterns"):
        s, r = safe_success_patterns(success_fn, dict(zip(fp_cols, values)))
        fp_scores.append(s)
        fp_reasons.append(r)

    return (
        np.array(pos_scores, dtype=int),
        np.array(fp_scores, dtype=int),
        pos_reasons,
        fp_reasons,
    )


def build_reason_matrix(reasons_list: List[List[str]]) -> Dict[str, np.ndarray]:
    all_reasons = sorted({r for row in reasons_list for r in row})
    mat = {}
    for reason in all_reasons:
        mat[reason] = np.array([reason in row for row in reasons_list], dtype=bool)
    return mat


def mask_for_atom(values: np.ndarray, atom: Atom) -> np.ndarray:
    if atom.op == "<=":
        return values <= atom.threshold
    if atom.op == ">":
        return values > atom.threshold
    raise ValueError(atom.op)


def make_atom_masks(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    quantiles: Sequence[float],
    min_pos_atom: int,
    max_fp_atom_rate: float,
) -> Tuple[List[Atom], List[np.ndarray], List[np.ndarray]]:
    atoms: List[Atom] = []
    pos_masks: List[np.ndarray] = []
    fp_masks: List[np.ndarray] = []

    for feat in tqdm(feature_cols, desc="Building atom masks"):
        pv = pos_df[feat].to_numpy(float)
        fv = fp_df[feat].to_numpy(float)
        combined = np.concatenate([pv, fv])
        thresholds = np.unique(np.nanquantile(combined, quantiles))
        thresholds = thresholds[np.isfinite(thresholds)]

        for t in thresholds:
            for op in ("<=", ">"):
                atom = Atom(feat, op, float(t))
                pm = mask_for_atom(pv, atom)
                fm = mask_for_atom(fv, atom)

                if pm.sum() < min_pos_atom:
                    continue
                if fm.mean() > max_fp_atom_rate:
                    continue

                atoms.append(atom)
                pos_masks.append(pm)
                fp_masks.append(fm)

    # Deduplicate atoms.
    seen = set()
    out_atoms, out_pm, out_fm = [], [], []
    for a, pm, fm in zip(atoms, pos_masks, fp_masks):
        k = a.key()
        if k in seen:
            continue
        seen.add(k)
        out_atoms.append(a)
        out_pm.append(pm)
        out_fm.append(fm)

    return out_atoms, out_pm, out_fm


def rule_from_masks(
    name: str,
    atoms: List[Atom],
    pos_mask: np.ndarray,
    fp_mask: np.ndarray,
    untagged_pos_mask: np.ndarray,
    source: str,
    base_reason: Optional[str] = None,
) -> Rule:
    pos_count = int(pos_mask.sum())
    fp_count = int(fp_mask.sum())
    untagged = int((pos_mask & untagged_pos_mask).sum())
    tagged = pos_count - untagged
    # Objective favors the broadest 0-FP rules across ALL positives.
    # Untagged coverage is still a useful secondary signal, but it is not the main target.
    score = pos_count * 10.0 + untagged * 2.0 - len(atoms) * 0.20
    if fp_count > 0:
        score -= fp_count * 100000
    return Rule(
        name=name,
        atoms=atoms,
        pos_count=pos_count,
        fp_count=fp_count,
        untagged_pos_count=untagged,
        tagged_pos_count=tagged,
        score=score,
        source=source,
        base_reason=base_reason,
    )


def rule_to_row(r: Rule, include_python_if: bool = False) -> Dict[str, Any]:
    """Convert one rule to a lightweight CSV/DataFrame row.

    The expensive python_if string is intentionally optional. For large candidate
    exports it can dominate both runtime and RAM. Keep it for selected rules only.
    """
    row = {
        "name": r.name,
        "source": r.source,
        "base_reason": r.base_reason or "",
        "pos_count": int(r.pos_count),
        "fp_count": int(r.fp_count),
        "untagged_pos_count": int(r.untagged_pos_count),
        "tagged_pos_count": int(r.tagged_pos_count),
        "n_conditions": int(len(r.atoms)),
        "score": float(r.score),
        "condition": r.condition_str(),
    }
    if include_python_if:
        row["python_if"] = r.python_if_block()
    return row


def rules_to_frame(
    rules: Sequence[Rule],
    include_python_if: bool = False,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    if max_rows is not None:
        rules = list(rules)[:max_rows]
    return pd.DataFrame.from_records(rule_to_row(r, include_python_if=include_python_if) for r in rules)


def write_rules_csv_streaming(
    rules: Sequence[Rule],
    path: Path,
    include_python_if: bool = False,
    chunk_size: int = 5000,
    max_rows: Optional[int] = None,
) -> None:
    """Write rules without materializing one massive rows list/DataFrame."""
    first = True
    chunk: List[Dict[str, Any]] = []
    written = 0
    t0 = time.time()

    for r in rules:
        if max_rows is not None and written >= max_rows:
            break
        chunk.append(rule_to_row(r, include_python_if=include_python_if))
        written += 1

        if len(chunk) >= chunk_size:
            pd.DataFrame.from_records(chunk).to_csv(path, mode="w" if first else "a", header=first, index=False)
            first = False
            chunk.clear()

            if written % (chunk_size * 10) == 0:
                print(f"[csv] wrote {written:,} rows to {path.name} in {(time.time() - t0):.1f}s", flush=True)

    if chunk or first:
        pd.DataFrame.from_records(chunk).to_csv(path, mode="w" if first else "a", header=first, index=False)

    print(f"[csv] done {path.name}: {written:,} rows in {(time.time() - t0):.1f}s", flush=True)


def greedy_select_rules(
    rules: Sequence[Rule],
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    untagged_pos_mask: np.ndarray,
    max_rules: int,
    min_new_untagged: int,
) -> List[Rule]:
    # Greedy objective for this broad version:
    # maximize NEW unique positive coverage first, then total breadth, then untagged coverage, then simplicity.
    selected: List[Rule] = []
    covered_pos = np.zeros(len(pos_df), dtype=bool)

    rule_masks = []
    for r in rules:
        pm = np.ones(len(pos_df), dtype=bool)
        fm = np.ones(len(fp_df), dtype=bool)
        for a in r.atoms:
            pm &= mask_for_atom(pos_df[a.feature].to_numpy(float), a)
            fm &= mask_for_atom(fp_df[a.feature].to_numpy(float), a)
        rule_masks.append((r, pm, fm))

    candidates = [(r, pm, fm) for r, pm, fm in rule_masks if fm.sum() == 0]
    for _ in range(max_rules):
        best = None
        best_gain = 0
        best_key = None
        for r, pm, fm in candidates:
            if r in selected:
                continue
            new_pos = int((pm & ~covered_pos).sum())
            new_untagged = int((pm & untagged_pos_mask & ~covered_pos).sum())
            if new_pos < min_new_untagged:
                continue
            key = (new_pos, r.pos_count, new_untagged, r.untagged_pos_count, -len(r.atoms), r.score)
            if best_key is None or key > best_key:
                best = (r, pm, fm)
                best_key = key
                best_gain = new_untagged
        if best is None:
            break
        r, pm, fm = best
        selected.append(r)
        covered_pos |= pm

    return selected


# ======================================================================================
# Pass 1: existing-reason refinements
# ======================================================================================

def mine_reason_refinements(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    pos_reasons: List[List[str]],
    fp_reasons: List[List[str]],
    untagged_pos_mask: np.ndarray,
    quantiles: Sequence[float],
    min_pos: int,
    max_conditions: int,
    top_k_per_reason: int,
) -> List[Rule]:
    pos_reason_mat = build_reason_matrix(pos_reasons)
    fp_reason_mat = build_reason_matrix(fp_reasons)
    rules: List[Rule] = []

    atoms, pos_atom_masks, fp_atom_masks = make_atom_masks(
        pos_df, fp_df, feature_cols, quantiles,
        min_pos_atom=max(5, min_pos // 3),
        max_fp_atom_rate=0.95,
    )

    for reason, base_pm in tqdm(pos_reason_mat.items(), desc="Mining reason refinements"):
        base_fm = fp_reason_mat.get(reason, np.zeros(len(fp_df), dtype=bool))
        if base_pm.sum() < min_pos:
            continue
        if base_fm.sum() == 0:
            # Already safe, no need to refine unless you want duplicate patterns.
            continue

        # Depth 1 candidates.
        frontier = [(tuple(), base_pm.copy(), base_fm.copy())]

        for depth in range(1, max_conditions + 1):
            new_frontier = []
            for idxs, pm, fm in frontier:
                start = idxs[-1] + 1 if idxs else 0
                for j in range(start, len(atoms)):
                    npm = pm & pos_atom_masks[j]
                    if npm.sum() < min_pos:
                        continue
                    nfm = fm & fp_atom_masks[j]
                    nidxs = idxs + (j,)

                    if nfm.sum() == 0:
                        ratoms = [atoms[k] for k in nidxs]
                        r = rule_from_masks(
                            name=f"safe_{reason}_{len(rules)+1}",
                            atoms=ratoms,
                            pos_mask=npm,
                            fp_mask=nfm,
                            untagged_pos_mask=untagged_pos_mask,
                            source="reason_refinement",
                            base_reason=reason,
                        )
                        rules.append(r)
                    else:
                        # Keep promising partials only.
                        fp_rate = nfm.sum() / max(1, npm.sum())
                        if fp_rate <= 2.0 and npm.sum() >= min_pos:
                            new_frontier.append((nidxs, npm, nfm))

            # Prune frontier to avoid blowup.
            new_frontier.sort(
                key=lambda x: (
                    -int((x[1] & untagged_pos_mask).sum()),
                    -int(x[1].sum()),
                    int(x[2].sum()),
                    len(x[0]),
                )
            )
            frontier = new_frontier[:top_k_per_reason]
            if not frontier:
                break

    # Deduplicate by condition/base_reason.
    unique = {}
    for r in rules:
        key = (r.base_reason, tuple(a.key() for a in r.atoms))
        if key not in unique or r.score > unique[key].score:
            unique[key] = r
    return sorted(unique.values(), key=lambda r: (-r.untagged_pos_count, -r.pos_count, len(r.atoms), -r.score))


# ======================================================================================
# Pass 2: untagged-heavy beam search with bitmasks
# ======================================================================================

def mine_untagged_beam(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    untagged_pos_mask: np.ndarray,
    quantiles: Sequence[float],
    min_pos: int,
    min_untagged: int,
    max_conditions: int,
    beam_width: int,
    max_atoms: int,
    time_deadline: Optional[float],
) -> List[Rule]:
    atoms, pos_masks, fp_masks = make_atom_masks(
        pos_df, fp_df, feature_cols, quantiles,
        min_pos_atom=min_pos,
        max_fp_atom_rate=0.85,
    )

    # Rank atoms by untagged usefulness and FP reduction.
    atom_rows = []
    for i, (a, pm, fm) in enumerate(zip(atoms, pos_masks, fp_masks)):
        pos = int(pm.sum())
        unt = int((pm & untagged_pos_mask).sum())
        tag = pos - unt
        fp = int(fm.sum())
        if unt < max(2, min_untagged // 3):
            continue
        score = pos * 10 + unt * 2 - fp * 0.05
        atom_rows.append((score, i))
    atom_rows.sort(reverse=True)
    keep_idxs = [i for _, i in atom_rows[:max_atoms]]
    atoms = [atoms[i] for i in keep_idxs]
    pos_masks = [pos_masks[i] for i in keep_idxs]
    fp_masks = [fp_masks[i] for i in keep_idxs]

    rules: List[Rule] = []
    frontier = [(tuple(), np.ones(len(pos_df), dtype=bool), np.ones(len(fp_df), dtype=bool))]

    for depth in range(1, max_conditions + 1):
        if time_deadline is not None and time.time() > time_deadline:
            print(f"[beam] Hit time deadline at depth {depth}")
            break

        new_frontier = []
        for idxs, pm, fm in tqdm(frontier, desc=f"Untagged beam depth {depth}", leave=False):
            start = idxs[-1] + 1 if idxs else 0
            for j in range(start, len(atoms)):
                npm = pm & pos_masks[j]
                pos_count = int(npm.sum())
                if pos_count < min_pos:
                    continue
                unt = int((npm & untagged_pos_mask).sum())

                nfm = fm & fp_masks[j]
                fp_count = int(nfm.sum())
                nidxs = idxs + (j,)

                if fp_count == 0:
                    ratoms = [atoms[k] for k in nidxs]
                    r = rule_from_masks(
                        name=f"untagged_beam_{len(rules)+1}",
                        atoms=ratoms,
                        pos_mask=npm,
                        fp_mask=nfm,
                        untagged_pos_mask=untagged_pos_mask,
                        source="untagged_beam",
                    )
                    rules.append(r)
                else:
                    # Keep partials that are still promising.
                    fp_per_unt = fp_count / max(1, unt)
                    if fp_per_unt <= 5.0:
                        new_frontier.append((nidxs, npm, nfm))

        new_frontier.sort(
            key=lambda x: (
                -int(x[1].sum()),
                int(x[2].sum()),
                -int((x[1] & untagged_pos_mask).sum()),
                len(x[0]),
            )
        )
        frontier = new_frontier[:beam_width]
        print(f"[beam] depth={depth} frontier={len(frontier)} rules={len(rules)}")
        if not frontier:
            break

    unique = {}
    for r in rules:
        key = tuple(a.key() for a in r.atoms)
        if key not in unique or r.score > unique[key].score:
            unique[key] = r
    return sorted(unique.values(), key=lambda r: (-r.untagged_pos_count, -r.pos_count, len(r.atoms), -r.score))


# ======================================================================================
# Pass 3: deep tree / forest path mining up to max_depth
# ======================================================================================

def extract_tree_rules(
    tree_model: DecisionTreeClassifier,
    feature_cols: Sequence[str],
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    untagged_pos_mask: np.ndarray,
    source: str,
    min_pos: int,
    min_untagged: int,
    require_untagged_heavy: bool,
) -> List[Rule]:
    tree = tree_model.tree_
    rules: List[Rule] = []

    def recurse(node: int, atoms: List[Atom]):
        if tree.feature[node] != _tree.TREE_UNDEFINED:
            feat_idx = tree.feature[node]
            feat = feature_cols[feat_idx]
            thr = float(tree.threshold[node])

            recurse(node=tree.children_left[node], atoms=atoms + [Atom(feat, "<=", thr)])
            recurse(node=tree.children_right[node], atoms=atoms + [Atom(feat, ">", thr)])
        else:
            # Leaf: evaluate exact rule against full data.
            if not atoms:
                return
            pm = np.ones(len(pos_df), dtype=bool)
            fm = np.ones(len(fp_df), dtype=bool)
            for a in atoms:
                pm &= mask_for_atom(pos_df[a.feature].to_numpy(float), a)
                fm &= mask_for_atom(fp_df[a.feature].to_numpy(float), a)

            pos_count = int(pm.sum())
            if pos_count < min_pos:
                return
            fp_count = int(fm.sum())
            if fp_count != 0:
                return
            unt = int((pm & untagged_pos_mask).sum())
            tagged = pos_count - unt
            if require_untagged_heavy:
                if unt < min_untagged:
                    return
                if unt <= tagged:
                    return

            r = rule_from_masks(
                name=f"deep_tree_{len(rules)+1}",
                atoms=compress_atoms(atoms),
                pos_mask=pm,
                fp_mask=fm,
                untagged_pos_mask=untagged_pos_mask,
                source=source,
            )
            rules.append(r)

    recurse(0, [])
    return rules


def compress_atoms(atoms: List[Atom]) -> List[Atom]:
    """Combine repeated thresholds on the same feature into the tightest interval."""
    lower: Dict[str, float] = {}
    upper: Dict[str, float] = {}

    for a in atoms:
        if a.op == ">":
            lower[a.feature] = max(lower.get(a.feature, -np.inf), a.threshold)
        elif a.op == "<=":
            upper[a.feature] = min(upper.get(a.feature, np.inf), a.threshold)

    out: List[Atom] = []
    for feat in sorted(set(lower) | set(upper)):
        if feat in lower and np.isfinite(lower[feat]):
            out.append(Atom(feat, ">", float(lower[feat])))
        if feat in upper and np.isfinite(upper[feat]):
            out.append(Atom(feat, "<=", float(upper[feat])))
    return out


def mine_deep_tree_paths(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    untagged_pos_mask: np.ndarray,
    max_depth: int,
    min_pos: int,
    min_untagged: int,
    n_estimators: int,
    n_jobs: int,
    random_state: int,
    require_untagged_heavy: bool,
) -> Tuple[List[Rule], pd.DataFrame]:
    X = pd.concat([pos_df[feature_cols], fp_df[feature_cols]], axis=0).to_numpy(float)
    y = np.r_[np.ones(len(pos_df), dtype=int), np.zeros(len(fp_df), dtype=int)]

    # Weight untagged positives more heavily to make trees discover those pockets.
    sample_weight = np.ones(len(y), dtype=float)
    sample_weight[:len(pos_df)][untagged_pos_mask] = 5.0

    forests = [
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_leaf=max(1, min_pos // 4),
                class_weight={0: 1.0, 1: 2.0},
                max_features="sqrt",
                bootstrap=True,
                n_jobs=n_jobs,
                random_state=random_state,
            ),
        ),
        (
            "extra_trees",
            ExtraTreesClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_leaf=max(1, min_pos // 4),
                class_weight={0: 1.0, 1: 2.0},
                max_features="sqrt",
                bootstrap=False,
                n_jobs=n_jobs,
                random_state=random_state + 123,
            ),
        ),
    ]

    all_rules: List[Rule] = []
    importances = []

    for name, model in forests:
        print(f"Fitting {name}...")
        model.fit(X, y, sample_weight=sample_weight)

        imp = pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_,
            "model": name,
        })
        importances.append(imp)

        print(f"Extracting rules from {name}...")
        extracted_batches = Parallel(n_jobs=n_jobs)(
            delayed(extract_tree_rules)(
                est,
                feature_cols,
                pos_df,
                fp_df,
                untagged_pos_mask,
                f"{name}_path",
                min_pos,
                min_untagged,
                require_untagged_heavy,
            )
            for est in tqdm(model.estimators_, desc=f"trees:{name}")
        )
        for batch in extracted_batches:
            all_rules.extend(batch)

    # Deduplicate.
    unique = {}
    for r in all_rules:
        key = tuple(a.key() for a in r.atoms)
        if key not in unique or r.score > unique[key].score:
            unique[key] = r

    feature_importance = pd.concat(importances, ignore_index=True)
    feature_importance = (
        feature_importance
        .groupby("feature", as_index=False)["importance"]
        .mean()
        .sort_values("importance", ascending=False)
    )

    return sorted(unique.values(), key=lambda r: (-r.untagged_pos_count, -r.pos_count, len(r.atoms), -r.score)), feature_importance


# ======================================================================================
# Pass 4: local rule expansion from selected candidates
# ======================================================================================

def local_expand_rules(
    seed_rules: Sequence[Rule],
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    untagged_pos_mask: np.ndarray,
    quantiles: Sequence[float],
    max_conditions: int,
    min_pos: int,
    min_untagged: int,
    max_trials_per_seed: int,
    rng: random.Random,
) -> List[Rule]:
    """
    Tries to slightly loosen/tighten/augment tree-discovered rules.
    This can find variants that are broader than the exact tree leaf.
    """
    atoms, pos_masks, fp_masks = make_atom_masks(
        pos_df, fp_df, feature_cols, quantiles,
        min_pos_atom=max(3, min_pos // 2),
        max_fp_atom_rate=0.95,
    )

    atom_by_key = {a.key(): i for i, a in enumerate(atoms)}
    rules: List[Rule] = []

    for seed in tqdm(seed_rules, desc="Local expanding selected rules"):
        # Evaluate seed.
        seed_atom_keys = [a.key() for a in seed.atoms]
        seed_idxs = [atom_by_key[k] for k in seed_atom_keys if k in atom_by_key]

        candidates = list(range(len(atoms)))
        # Prefer atoms involving same features or top tree features.
        same_feature_idxs = [i for i, a in enumerate(atoms) if a.feature in {sa.feature for sa in seed.atoms}]
        if same_feature_idxs:
            candidates = same_feature_idxs + rng.sample(candidates, min(len(candidates), max_trials_per_seed))

        for _ in range(max_trials_per_seed):
            # Randomly drop some seed atoms and add some candidates, keeping <= max_conditions.
            chosen = set(seed_idxs)
            for idx in list(chosen):
                if rng.random() < 0.15:
                    chosen.remove(idx)
            add_count = rng.randint(0, max(0, max_conditions - len(chosen)))
            for idx in rng.sample(candidates, min(add_count, len(candidates))):
                chosen.add(idx)
            if not chosen or len(chosen) > max_conditions:
                continue

            pm = np.ones(len(pos_df), dtype=bool)
            fm = np.ones(len(fp_df), dtype=bool)
            for idx in chosen:
                pm &= pos_masks[idx]
                fm &= fp_masks[idx]

            if fm.sum() != 0:
                continue
            if pm.sum() < min_pos:
                continue
            unt = int((pm & untagged_pos_mask).sum())

            ratoms = [atoms[i] for i in sorted(chosen)]
            r = rule_from_masks(
                name=f"expanded_untagged_{len(rules)+1}",
                atoms=ratoms,
                pos_mask=pm,
                fp_mask=fm,
                untagged_pos_mask=untagged_pos_mask,
                source="local_expansion",
            )
            rules.append(r)

    unique = {}
    for r in rules:
        key = tuple(a.key() for a in r.atoms)
        if key not in unique or r.score > unique[key].score:
            unique[key] = r
    return sorted(unique.values(), key=lambda r: (-r.untagged_pos_count, -r.pos_count, len(r.atoms), -r.score))


# ======================================================================================
# Output helpers
# ======================================================================================

def write_variable_declarations(feature_cols: Sequence[str], outpath: Path) -> None:
    lines = [
        f"{"#type: ignore"}\n",
        f"{"#pylint: skip-file"}\n",
    ]
    for feat in sorted(feature_cols):
        var = feature_to_var(feat)
        lines.append(f'{var} = features_data["{feat}"]')
    outpath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_python_blocks(rules: Sequence[Rule], outpath: Path, prefix: str) -> None:
    chunks = []
    for i, r in enumerate(rules, start=1):
        reason = f"{prefix}_{i:02d}"
        chunks.append("# " + "=" * 88)
        chunks.append(f"# {reason}")
        chunks.append(
            f"# Covers: {r.pos_count} positives / {r.fp_count} FP / "
            f"{r.untagged_pos_count} untagged / {r.tagged_pos_count} tagged / "
            f"{len(r.atoms)} conditions / source={r.source}"
        )
        chunks.append(r.python_if_block(reason_name=reason))
        chunks.append("")
    outpath.write_text("\n".join(chunks), encoding="utf-8")


def checkpoint_rules(
    rules: Sequence[Rule],
    path: Path,
    include_python_if: bool = False,
    chunk_size: int = 5000,
    max_rows: Optional[int] = None,
) -> None:
    """Sort and stream candidate rules to CSV.

    Important: candidate files default to include_python_if=False to avoid generating
    huge Python source strings for every candidate. Selected rules can still include it.
    """
    if not rules:
        pd.DataFrame().to_csv(path, index=False)
        return

    sorted_rules = sorted(
        rules,
        key=lambda r: (
            r.fp_count,
            -r.untagged_pos_count,
            -r.pos_count,
            len(r.atoms),
            -r.score,
        ),
    )
    if max_rows is not None:
        sorted_rules = sorted_rules[:max_rows]

    write_rules_csv_streaming(
        sorted_rules,
        path,
        include_python_if=include_python_if,
        chunk_size=chunk_size,
        max_rows=None,
    )
    del sorted_rules
    gc.collect()


# ======================================================================================
# Main
# ======================================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deep broad zero-FP positive rule miner; mines feature_* columns only")
    p.add_argument("--outdir", required=True, type=Path)

    p.add_argument("--time-budget-minutes", type=float, default=180.0)
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--n-jobs", type=int, default=-1)

    p.add_argument("--min-pos-broad", type=int, default=25)
    p.add_argument("--min-pos-untagged", type=int, default=8)
    p.add_argument("--min-untagged", type=int, default=8)

    p.add_argument("--reason-max-conditions", type=int, default=3)
    p.add_argument("--reason-top-k", type=int, default=500)

    p.add_argument("--beam-max-conditions", type=int, default=20)
    p.add_argument("--beam-width", type=int, default=5000)
    p.add_argument("--beam-max-atoms", type=int, default=1200)

    p.add_argument("--max-depth", type=int, default=20)
    p.add_argument("--n-estimators", type=int, default=1000)

    p.add_argument("--local-expansion", action="store_true")
    p.add_argument("--local-expansion-trials", type=int, default=2000)

    p.add_argument("--max-selected-rules", type=int, default=30)
    p.add_argument("--min-new-untagged", type=int, default=3, help="In this broad version, this means minimum NEW positives per selected rule.")

    p.add_argument("--checkpoint-chunk-size", type=int, default=5000)
    # p.add_argument(
    #     "--max-checkpoint-rules",
    #     type=int,
    #     default=200000,
    #     help="Maximum rows to write per large candidate checkpoint. Use 0 for unlimited.",
    # )
    p.add_argument(
        "--candidate-python-if",
        action="store_true",
        help="Also export python_if for candidate CSVs. Much slower and heavier; selected rules always get Python blocks separately.",
    )

    p.add_argument(
        "--exclude-regex",
        action="append",
        default=[],
        help="Additional regex for feature columns to exclude. Can be passed multiple times.",
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    deadline = started + args.time_budget_minutes * 60.0 if args.time_budget_minutes > 0 else None
    max_checkpoint_rules = None

    print("Loading CSV files...")
    pos_raw = pd.read_csv("model/training/positive_results.csv")
    fp_raw = pd.read_csv("model/training/false_positive_results.csv")

    pos_df = normalize_feature_frame(pos_raw)
    fp_df = normalize_feature_frame(fp_raw)

    exclude_regexes = DEFAULT_EXCLUDE_PATTERNS + list(args.exclude_regex or [])
    feature_cols = discover_feature_cols(pos_df, fp_df, exclude_regexes)
    print(f"Feature columns used: {len(feature_cols)}")

    (args.outdir / "feature_columns_used.json").write_text(
        json.dumps(feature_cols, indent=2), encoding="utf-8"
    )
    write_variable_declarations(feature_cols, args.outdir / "variable_declarations.py")

    print("Evaluating current success_patterns...")
    pos_scores, fp_scores, pos_reasons, fp_reasons = evaluate_current_tags("model/training/hard_rules.py", pos_df, fp_df)
    tagged_pos_mask = pos_scores > 0
    untagged_pos_mask = ~tagged_pos_mask

    baseline = {
        "positives": int(len(pos_df)),
        "false_positives": int(len(fp_df)),
        "tagged_positives": int(tagged_pos_mask.sum()),
        "untagged_positives": int(untagged_pos_mask.sum()),
        "success_pattern_fps": int((fp_scores > 0).sum()),
        "feature_count": int(len(feature_cols)),
    }
    print("Baseline:", baseline)
    (args.outdir / "baseline.json").write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    pd.DataFrame({
        "row_index": np.arange(len(pos_df)),
        "success_score": pos_scores,
        "is_tagged": tagged_pos_mask,
        "reasons": ["|".join(r) for r in pos_reasons],
    }).to_csv(args.outdir / "positive_current_tags.csv", index=False)

    pd.DataFrame({
        "row_index": np.arange(len(fp_df)),
        "success_score": fp_scores,
        "is_tagged": fp_scores > 0,
        "reasons": ["|".join(r) for r in fp_reasons],
    }).to_csv(args.outdir / "fp_current_tags.csv", index=False)

    # Quantiles: dense enough for long local run.
    broad_quantiles = np.unique(np.r_[
        np.linspace(0.01, 0.99, 99),
        [0.001, 0.0025, 0.005, 0.995, 0.9975, 0.999],
    ])
    beam_quantiles = np.unique(np.r_[
        np.linspace(0.005, 0.995, 199),
        [0.001, 0.0025, 0.9975, 0.999],
    ])

    all_rules: List[Rule] = []

    # ----------------------------------------------------------------------------------
    # Pass 1: broad reason refinements
    # ----------------------------------------------------------------------------------
    print("\n=== Pass 1: existing-reason refinements ===")
    reason_rules = mine_reason_refinements(
        pos_df=pos_df,
        fp_df=fp_df,
        feature_cols=feature_cols,
        pos_reasons=pos_reasons,
        fp_reasons=fp_reasons,
        untagged_pos_mask=untagged_pos_mask,
        quantiles=broad_quantiles,
        min_pos=args.min_pos_broad,
        max_conditions=args.reason_max_conditions,
        top_k_per_reason=args.reason_top_k,
    )
    checkpoint_rules(reason_rules, args.outdir / "pass1_reason_refinement_candidates.csv", include_python_if=args.candidate_python_if, chunk_size=args.checkpoint_chunk_size, max_rows=max_checkpoint_rules)
    all_rules.extend(reason_rules)
    print(f"Pass 1 rules: {len(reason_rules)}")
    gc.collect()

    # ----------------------------------------------------------------------------------
    # Pass 2: untagged-heavy beam search
    # ----------------------------------------------------------------------------------
    print("\n=== Pass 2: untagged-heavy beam search ===")
    beam_rules = mine_untagged_beam(
        pos_df=pos_df,
        fp_df=fp_df,
        feature_cols=feature_cols,
        untagged_pos_mask=untagged_pos_mask,
        quantiles=beam_quantiles,
        min_pos=args.min_pos_untagged,
        min_untagged=args.min_untagged,
        max_conditions=args.beam_max_conditions,
        beam_width=args.beam_width,
        max_atoms=args.beam_max_atoms,
        time_deadline=deadline,
    )
    checkpoint_rules(beam_rules, args.outdir / "pass2_untagged_beam_candidates.csv", include_python_if=args.candidate_python_if, chunk_size=args.checkpoint_chunk_size, max_rows=max_checkpoint_rules)
    all_rules.extend(beam_rules)
    print(f"Pass 2 rules: {len(beam_rules)}")
    gc.collect()

    # ----------------------------------------------------------------------------------
    # Pass 3: deep forest/path mining
    # ----------------------------------------------------------------------------------
    print("\n=== Pass 3: deep forest/path mining ===")
    tree_rules, importance_df = mine_deep_tree_paths(
        pos_df=pos_df,
        fp_df=fp_df,
        feature_cols=feature_cols,
        untagged_pos_mask=untagged_pos_mask,
        max_depth=args.max_depth,
        min_pos=args.min_pos_untagged,
        min_untagged=0,
        n_estimators=args.n_estimators,
        n_jobs=args.n_jobs,
        random_state=args.random_state,
        require_untagged_heavy=False,
    )
    checkpoint_rules(tree_rules, args.outdir / "pass3_deep_tree_candidates.csv", include_python_if=args.candidate_python_if, chunk_size=args.checkpoint_chunk_size, max_rows=max_checkpoint_rules)
    importance_df.to_csv(args.outdir / "pass3_feature_importance.csv", index=False)
    all_rules.extend(tree_rules)
    print(f"Pass 3 rules: {len(tree_rules)}")
    gc.collect()

    # ----------------------------------------------------------------------------------
    # Pass 4: optional local expansion
    # ----------------------------------------------------------------------------------
    if args.local_expansion:
        print("\n=== Pass 4: local expansion from top tree/beam seeds ===")
        seed_rules = sorted(
            [r for r in all_rules if r.fp_count == 0],
            key=lambda r: (-r.pos_count, -r.untagged_pos_count, len(r.atoms), -r.score),
        )[:100]
        expanded_rules = local_expand_rules(
            seed_rules=seed_rules,
            pos_df=pos_df,
            fp_df=fp_df,
            feature_cols=feature_cols,
            untagged_pos_mask=untagged_pos_mask,
            quantiles=beam_quantiles,
            max_conditions=args.beam_max_conditions,
            min_pos=args.min_pos_untagged,
            min_untagged=args.min_untagged,
            max_trials_per_seed=args.local_expansion_trials,
            rng=random.Random(args.random_state),
        )
        checkpoint_rules(expanded_rules, args.outdir / "pass4_local_expansion_candidates.csv", include_python_if=args.candidate_python_if, chunk_size=args.checkpoint_chunk_size, max_rows=max_checkpoint_rules)
        all_rules.extend(expanded_rules)
        print(f"Pass 4 rules: {len(expanded_rules)}")
        gc.collect()

    # ----------------------------------------------------------------------------------
    # Final aggregation and greedy selected set
    # ----------------------------------------------------------------------------------
    print("\n=== Final aggregation ===")
    unique = {}
    for r in all_rules:
        if r.fp_count != 0:
            continue
        key = (r.base_reason or "", tuple(a.key() for a in r.atoms))
        if key not in unique or r.score > unique[key].score:
            unique[key] = r

    final_rules = sorted(
        unique.values(),
        key=lambda r: (-r.pos_count, -r.untagged_pos_count, len(r.atoms), -r.score),
    )
    checkpoint_rules(final_rules, args.outdir / "all_zero_fp_candidates.csv", include_python_if=args.candidate_python_if, chunk_size=args.checkpoint_chunk_size, max_rows=max_checkpoint_rules)

    selected = greedy_select_rules(
        rules=final_rules,
        pos_df=pos_df,
        fp_df=fp_df,
        untagged_pos_mask=untagged_pos_mask,
        max_rules=args.max_selected_rules,
        min_new_untagged=args.min_new_untagged,
    )
    checkpoint_rules(selected, args.outdir / "selected_zero_fp_rules.csv", include_python_if=True, chunk_size=args.checkpoint_chunk_size, max_rows=None)
    write_python_blocks(selected, args.outdir / "selected_rules_python_blocks.py", prefix="mined_broad_rule")

    selected_pos_mask = np.zeros(len(pos_df), dtype=bool)
    selected_untagged_mask = np.zeros(len(pos_df), dtype=bool)
    for r in selected:
        pm = np.ones(len(pos_df), dtype=bool)
        for a in r.atoms:
            pm &= mask_for_atom(pos_df[a.feature].to_numpy(float), a)
        selected_pos_mask |= pm
        selected_untagged_mask |= (pm & untagged_pos_mask)

    final_summary = {
        **baseline,
        "all_zero_fp_candidates": int(len(final_rules)),
        "selected_rules": int(len(selected)),
        "selected_unique_positives_covered": int(selected_pos_mask.sum()),
        "selected_unique_untagged_covered": int(selected_untagged_mask.sum()),
        "selected_unique_untagged_coverage_pct": float(selected_untagged_mask.sum() / max(1, untagged_pos_mask.sum())),
        "elapsed_minutes": round((time.time() - started) / 60.0, 2),
    }
    print("Final summary:", final_summary)
    (args.outdir / "final_summary.json").write_text(json.dumps(final_summary, indent=2), encoding="utf-8")

    print("\nDone. Main outputs:")
    print(f"  {args.outdir / 'all_zero_fp_candidates.csv'}")
    print(f"  {args.outdir / 'selected_zero_fp_rules.csv'}")
    print(f"  {args.outdir / 'selected_rules_python_blocks.py'}")
    print(f"  {args.outdir / 'final_summary.json'}")


if __name__ == "__main__":
    main()
