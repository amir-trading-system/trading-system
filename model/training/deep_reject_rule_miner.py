# pylint: skip-file
# type: ignore
#!/usr/bin/env python3
"""
Feature-only reject-rule miner for false positives.

Purpose
-------
This script is the reject-side equivalent of the positive pattern miner.

It finds hard reject rules that:
  - match false_positive_results rows,
  - match 0 positive_results rows,
  - use only columns that start with "feature_",
  - output paste-ready `if (...): return True` blocks.

It also analyzes the current `should_be_rejected_by_hard_rules` function and reports:
  - how many positives it rejects,
  - how many FPs it rejects,
  - which existing reject rules are actually first-hit,
  - which existing reject rules are currently unreachable/shadowed by earlier rules.

Typical command
---------------
python -m model.training.deep_reject_rule_miner \
  --outdir model/training/mining_results \
  --time-budget-minutes 360 \
  --max-depth 60 \
  --n-estimators 10000 \
  --beam-width 20000 \
  --beam-max-atoms 20000 \
  --beam-max-conditions 60 \
  --min-fp 10 \
  --max-selected-rules 40 \
  --min-new-fp 1 \
  --local-expansion \
  --local-expansion-trials 10000 \
  --n-jobs 4

If you only want to mine rules for FPs not already rejected by the current hard rules:
  --target-mode currently_unrejected_fps

If you want to mine broad reject rules specifically for FPs that currently have
feature_overall_legit_trade == True, add:
  --target-overall-legit-trade-fps

Command for feature_overall_legit_trade == True:
python -m model.training.deep_reject_rule_miner \
  --outdir model/training/mining_results \
  --time-budget-minutes 360 \
  --max-depth 60 \
  --n-estimators 10000 \
  --beam-width 30000 \
  --beam-max-atoms 6000 \
  --beam-max-conditions 60 \
  --min-fp 10 \
  --max-selected-rules 60 \
  --min-new-fp 1 \
  --local-expansion \
  --local-expansion-trials 30000 \
  --target-overall-legit-trade-fps \
  --n-jobs 4

This keeps the normal zero-positive-damage requirement, but the greedy objective
focuses coverage on that FP subset even if those rows are already rejected by
existing rules. Default behavior is unchanged when the flag is not used.

Default target mode is all_fps, which is better for finding broader/simpler replacement reject rules.

Dependencies
------------
pip install pandas numpy scikit-learn joblib tqdm
"""

from __future__ import annotations

import argparse
import ast
import copy
import importlib.util
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.tree import _tree
from tqdm import tqdm


# ======================================================================================
# Defaults
# ======================================================================================

DEFAULT_EXCLUDE_FEATURE_REGEXES = [
    r"^feature_overall_legit_trade$",
    r"positive_score$",
    r"positive_group_score$",
    r"soft_positive_group_score$",
    r"strong_positive_group_score$",
]


@dataclass(frozen=True)
class Atom:
    feature: str
    op: str
    threshold: float

    def expr(self) -> str:
        var = feature_to_var(self.feature)
        if self.op == "<=":
            return f"{var} <= {self.threshold:.10g}"
        if self.op == ">":
            return f"{var} > {self.threshold:.10g}"
        raise ValueError(self.op)

    def key(self) -> Tuple[str, str, float]:
        return (self.feature, self.op, round(float(self.threshold), 12))


@dataclass
class Rule:
    name: str
    atoms: List[Atom]
    fp_count: int
    pos_count: int
    score: float
    source: str
    new_fp_gain: int = 0

    def condition_str(self) -> str:
        return " and ".join(a.expr() for a in self.atoms)

    def python_if_block(self, reason_name: Optional[str] = None, indent: str = "    ") -> str:
        reason_name = reason_name or self.name
        lines = []
        lines.append(f"{indent}# Mined Reject Rule: {reason_name}")
        lines.append(f"{indent}# Rejects: {self.fp_count} FPs / {self.pos_count} positives")
        lines.append(f"{indent}# Conditions: {len(self.atoms)}")
        lines.append(f"{indent}if (")
        for i, atom in enumerate(self.atoms):
            prefix = "" if i == 0 else "and "
            lines.append(f"{indent}    {prefix}{atom.expr()}")
        lines.append(f"{indent}):")
        lines.append(f"{indent}    return True")
        return "\n".join(lines)


# ======================================================================================
# General helpers
# ======================================================================================

def feature_to_var(feature: str) -> str:
    if feature.startswith("feature_"):
        return feature[len("feature_"):]
    return feature


def normalize_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for c in out.columns:
        if out[c].dtype == bool:
            out[c] = out[c].astype(float)

    for c in out.columns:
        if out[c].dtype == object:
            converted = pd.to_numeric(out[c], errors="coerce")
            if converted.notna().mean() >= 0.80:
                out[c] = converted

    num_cols = out.select_dtypes(include=[np.number]).columns
    out[num_cols] = out[num_cols].replace([np.inf, -np.inf], np.nan)

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
    compiled = [re.compile(p) for p in exclude_regexes]
    common = [c for c in pos_df.columns if c in fp_df.columns]

    cols = []
    for c in common:
        if not c.startswith("feature_"):
            continue
        if any(rx.search(c) for rx in compiled):
            continue
        if not pd.api.types.is_numeric_dtype(pos_df[c]) or not pd.api.types.is_numeric_dtype(fp_df[c]):
            continue

        combined = pd.concat([pos_df[c], fp_df[c]], axis=0)
        if combined.nunique(dropna=True) <= 1:
            continue

        cols.append(c)

    return cols


def mask_for_atom_values(values: np.ndarray, atom: Atom) -> np.ndarray:
    if atom.op == "<=":
        return values <= atom.threshold
    if atom.op == ">":
        return values > atom.threshold
    raise ValueError(atom.op)


def mask_for_atom_df(df: pd.DataFrame, atom: Atom) -> np.ndarray:
    return mask_for_atom_values(df[atom.feature].to_numpy(float), atom)


def load_hard_rules(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("loaded_hard_rules_reject_miner", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import hard_rules from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["loaded_hard_rules_reject_miner"] = module
    spec.loader.exec_module(module)
    return module


def safe_reject(fn: Callable, features: Dict[str, Any]) -> bool:
    try:
        return bool(fn(features))
    except Exception:
        return False


# ======================================================================================
# Current hard-rule instrumentation
# ======================================================================================

class RejectRuleInstrumenter(ast.NodeTransformer):
    """
    Instruments should_be_rejected_by_hard_rules so it returns:
      (bool_result, hit_rule_indexes)

    It records the index of an if-block when that if-block directly returns True.
    Since the original function exits on the first True, these are first-hit stats.
    """

    def __init__(self, source: str):
        self.source = source
        self.rule_index = 0
        self.rule_map: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if node.name != "should_be_rejected_by_hard_rules":
            return node

        node.name = "should_be_rejected_by_hard_rules_instrumented"
        node = self.generic_visit(node)

        node.body.insert(
            0,
            ast.Assign(
                targets=[ast.Name(id="__hit_rules", ctx=ast.Store())],
                value=ast.List(elts=[], ctx=ast.Load()),
            ),
        )
        return node

    def visit_If(self, node: ast.If) -> ast.AST:
        has_direct_true_return = any(
            isinstance(x, ast.Return)
            and isinstance(x.value, ast.Constant)
            and x.value.value is True
            for x in node.body
        )

        if has_direct_true_return:
            idx = self.rule_index
            self.rule_index += 1
            self.rule_map.append(
                {
                    "reject_rule_index": idx,
                    "lineno": node.lineno,
                    "condition": ast.get_source_segment(self.source, node.test) or "",
                }
            )
            node.body.insert(
                0,
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="__hit_rules", ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[ast.Constant(idx)],
                        keywords=[],
                    )
                ),
            )

        node = self.generic_visit(node)
        return node

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool):
            node.value = ast.Tuple(
                elts=[
                    ast.Constant(node.value.value),
                    ast.Name(id="__hit_rules", ctx=ast.Load()),
                ],
                ctx=ast.Load(),
            )
        return node


def instrument_current_reject_rules(hard_rules_path: Path):
    source = hard_rules_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    inst = RejectRuleInstrumenter(source)
    new_tree = inst.visit(copy.deepcopy(tree))
    ast.fix_missing_locations(new_tree)

    ns: Dict[str, Any] = {}
    exec(compile(new_tree, str(hard_rules_path), "exec"), ns)
    fn = ns.get("should_be_rejected_by_hard_rules_instrumented")
    if fn is None:
        raise RuntimeError("Could not instrument should_be_rejected_by_hard_rules")

    return fn, pd.DataFrame(inst.rule_map)


def analyze_existing_reject_rules(
    hard_rules_path: Path,
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    outdir: Path,
) -> Dict[str, Any]:
    module = load_hard_rules(hard_rules_path)

    if not hasattr(module, "should_be_rejected_by_hard_rules"):
        raise AttributeError("hard_rules.py does not contain should_be_rejected_by_hard_rules")

    reject_fn = module.should_be_rejected_by_hard_rules

    pos_rejected = []
    for _, row in tqdm(pos_df.iterrows(), total=len(pos_df), desc="Current reject eval: positives"):
        pos_rejected.append(safe_reject(reject_fn, row.to_dict()))
    fp_rejected = []
    for _, row in tqdm(fp_df.iterrows(), total=len(fp_df), desc="Current reject eval: FPs"):
        fp_rejected.append(safe_reject(reject_fn, row.to_dict()))

    pos_rejected = np.array(pos_rejected, dtype=bool)
    fp_rejected = np.array(fp_rejected, dtype=bool)

    # First-hit rule stats.
    inst_fn, rule_map = instrument_current_reject_rules(hard_rules_path)

    fp_first_hits = []
    for _, row in tqdm(fp_df.iterrows(), total=len(fp_df), desc="Instrumented first-hit: FPs"):
        result, hits = inst_fn(row.to_dict())
        fp_first_hits.append(hits[0] if hits else None)

    pos_first_hits = []
    for _, row in tqdm(pos_df.iterrows(), total=len(pos_df), desc="Instrumented first-hit: positives"):
        result, hits = inst_fn(row.to_dict())
        pos_first_hits.append(hits[0] if hits else None)

    fp_first_counts = pd.Series(fp_first_hits, dtype="object").value_counts(dropna=False).to_dict()
    pos_first_counts = pd.Series(pos_first_hits, dtype="object").value_counts(dropna=False).to_dict()

    stats_rows = []
    for _, r in rule_map.iterrows():
        idx = int(r["reject_rule_index"])
        stats_rows.append(
            {
                "reject_rule_index": idx,
                "lineno": int(r["lineno"]),
                "fp_first_hit_count": int(fp_first_counts.get(idx, 0)),
                "positive_first_hit_count": int(pos_first_counts.get(idx, 0)),
                "condition": r["condition"],
                "candidate_unnecessary_by_order": int(fp_first_counts.get(idx, 0)) == 0
                and int(pos_first_counts.get(idx, 0)) == 0,
            }
        )

    stats_df = pd.DataFrame(stats_rows)
    stats_df.to_csv(outdir / "existing_reject_rule_first_hit_stats.csv", index=False)

    if len(stats_df):
        stats_df[stats_df["candidate_unnecessary_by_order"]].to_csv(
            outdir / "existing_reject_rules_unreachable_by_order.csv",
            index=False,
        )

    summary = {
        "current_reject_positive_count": int(pos_rejected.sum()),
        "current_reject_fp_count": int(fp_rejected.sum()),
        "current_unrejected_fp_count": int((~fp_rejected).sum()),
        "existing_reject_rule_count": int(len(rule_map)),
        "existing_reject_rules_with_zero_first_hits": int(
            stats_df["candidate_unnecessary_by_order"].sum() if len(stats_df) else 0
        ),
    }

    return summary


# ======================================================================================
# Atom/rule evaluation
# ======================================================================================

def make_atom_masks(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    fp_target_mask: np.ndarray,
    quantiles: Sequence[float],
    min_fp_atom: int,
    max_positive_atom_rate: float,
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
                pm = mask_for_atom_values(pv, atom)
                fm = mask_for_atom_values(fv, atom)

                if int((fm & fp_target_mask).sum()) < min_fp_atom:
                    continue
                if pm.mean() > max_positive_atom_rate:
                    continue

                atoms.append(atom)
                pos_masks.append(pm)
                fp_masks.append(fm)

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
    fp_target_mask: np.ndarray,
    source: str,
) -> Rule:
    fp_count = int((fp_mask & fp_target_mask).sum())
    pos_count = int(pos_mask.sum())
    score = fp_count * 100.0 - pos_count * 100000.0 - len(atoms) * 0.25
    return Rule(
        name=name,
        atoms=atoms,
        fp_count=fp_count,
        pos_count=pos_count,
        score=score,
        source=source,
    )


def compress_atoms(atoms: List[Atom]) -> List[Atom]:
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


def rules_to_frame(rules: Sequence[Rule]) -> pd.DataFrame:
    rows = []
    for r in rules:
        rows.append(
            {
                "name": r.name,
                "source": r.source,
                "fp_count": r.fp_count,
                "positive_damage_count": r.pos_count,
                "new_fp_gain": r.new_fp_gain,
                "n_conditions": len(r.atoms),
                "score": r.score,
                "condition": r.condition_str(),
                "python_if": r.python_if_block(),
            }
        )
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(
            ["positive_damage_count", "fp_count", "new_fp_gain", "n_conditions", "score"],
            ascending=[True, False, False, True, False],
        )
    return df


def checkpoint_rules(rules: Sequence[Rule], path: Path) -> None:
    rules_to_frame(rules).to_csv(path, index=False)


# ======================================================================================
# Pass 1: reject beam search
# ======================================================================================

def mine_reject_beam(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    fp_target_mask: np.ndarray,
    quantiles: Sequence[float],
    min_fp: int,
    max_conditions: int,
    beam_width: int,
    max_atoms: int,
    time_deadline: Optional[float],
) -> List[Rule]:
    atoms, pos_masks, fp_masks = make_atom_masks(
        pos_df,
        fp_df,
        feature_cols,
        fp_target_mask,
        quantiles,
        min_fp_atom=max(1, min_fp // 2),
        max_positive_atom_rate=0.95,
    )

    # Rank atoms by target FP coverage and low positive overlap.
    ranked = []
    for i, (a, pm, fm) in enumerate(zip(atoms, pos_masks, fp_masks)):
        fp_count = int((fm & fp_target_mask).sum())
        pos_count = int(pm.sum())
        score = fp_count * 100.0 - pos_count * 3.0
        ranked.append((score, i))

    ranked.sort(reverse=True)
    keep = [i for _, i in ranked[:max_atoms]]
    atoms = [atoms[i] for i in keep]
    pos_masks = [pos_masks[i] for i in keep]
    fp_masks = [fp_masks[i] for i in keep]

    rules: List[Rule] = []
    frontier = [
        (
            tuple(),
            np.ones(len(pos_df), dtype=bool),
            np.ones(len(fp_df), dtype=bool),
        )
    ]

    for depth in range(1, max_conditions + 1):
        if time_deadline is not None and time.time() > time_deadline:
            print(f"[beam] Hit time deadline at depth {depth}")
            break

        new_frontier = []

        for idxs, pm, fm in tqdm(frontier, desc=f"Reject beam depth {depth}", leave=False):
            start = idxs[-1] + 1 if idxs else 0

            for j in range(start, len(atoms)):
                npm = pm & pos_masks[j]
                nfm = fm & fp_masks[j]
                fp_count = int((nfm & fp_target_mask).sum())
                if fp_count < min_fp:
                    continue

                pos_count = int(npm.sum())
                nidxs = idxs + (j,)

                if pos_count == 0:
                    ratoms = [atoms[k] for k in nidxs]
                    rules.append(
                        rule_from_masks(
                            name=f"reject_beam_{len(rules)+1}",
                            atoms=ratoms,
                            pos_mask=npm,
                            fp_mask=nfm,
                            fp_target_mask=fp_target_mask,
                            source="reject_beam",
                        )
                    )
                else:
                    # Keep promising partials.
                    pos_per_fp = pos_count / max(1, fp_count)
                    if pos_per_fp <= 2.0:
                        new_frontier.append((nidxs, npm, nfm))

        new_frontier.sort(
            key=lambda x: (
                int(x[1].sum()),                         # fewer positives first
                -int((x[2] & fp_target_mask).sum()),      # more FPs next
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

    return sorted(unique.values(), key=lambda r: (-r.fp_count, len(r.atoms), -r.score))


# ======================================================================================
# Pass 2: deep forest/path mining
# ======================================================================================

def extract_tree_rules(
    estimator,
    feature_cols: Sequence[str],
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    fp_target_mask: np.ndarray,
    source: str,
    min_fp: int,
) -> List[Rule]:
    tree = estimator.tree_
    rules: List[Rule] = []

    def recurse(node: int, atoms: List[Atom]):
        if tree.feature[node] != _tree.TREE_UNDEFINED:
            feat_idx = int(tree.feature[node])
            feat = feature_cols[feat_idx]
            thr = float(tree.threshold[node])

            recurse(tree.children_left[node], atoms + [Atom(feat, "<=", thr)])
            recurse(tree.children_right[node], atoms + [Atom(feat, ">", thr)])
            return

        if not atoms:
            return

        compressed = compress_atoms(atoms)
        pm = np.ones(len(pos_df), dtype=bool)
        fm = np.ones(len(fp_df), dtype=bool)

        for a in compressed:
            pm &= mask_for_atom_df(pos_df, a)
            fm &= mask_for_atom_df(fp_df, a)

        pos_count = int(pm.sum())
        fp_count = int((fm & fp_target_mask).sum())

        if pos_count == 0 and fp_count >= min_fp:
            rules.append(
                rule_from_masks(
                    name=f"reject_tree_{len(rules)+1}",
                    atoms=compressed,
                    pos_mask=pm,
                    fp_mask=fm,
                    fp_target_mask=fp_target_mask,
                    source=source,
                )
            )

    recurse(0, [])
    return rules


def mine_reject_tree_paths(
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    fp_target_mask: np.ndarray,
    max_depth: int,
    min_fp: int,
    n_estimators: int,
    n_jobs: int,
    random_state: int,
) -> Tuple[List[Rule], pd.DataFrame]:
    X = pd.concat([pos_df[feature_cols], fp_df[feature_cols]], axis=0).to_numpy(float)
    y = np.r_[np.zeros(len(pos_df), dtype=int), np.ones(len(fp_df), dtype=int)]

    # Heavily weight target FPs, but keep positives important as negatives.
    sample_weight = np.ones(len(y), dtype=float)
    fp_weight_slice = sample_weight[len(pos_df):]
    fp_weight_slice[fp_target_mask] = 5.0
    fp_weight_slice[~fp_target_mask] = 0.25

    models = [
        (
            "reject_random_forest",
            RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_leaf=max(1, min_fp // 4),
                class_weight={0: 2.0, 1: 1.0},
                max_features="sqrt",
                bootstrap=True,
                n_jobs=n_jobs,
                random_state=random_state,
            ),
        ),
        (
            "reject_extra_trees",
            ExtraTreesClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_leaf=max(1, min_fp // 4),
                class_weight={0: 2.0, 1: 1.0},
                max_features="sqrt",
                bootstrap=False,
                n_jobs=n_jobs,
                random_state=random_state + 997,
            ),
        ),
    ]

    all_rules: List[Rule] = []
    importances = []

    for name, model in models:
        print(f"Fitting {name}...")
        model.fit(X, y, sample_weight=sample_weight)

        importances.append(
            pd.DataFrame(
                {
                    "feature": list(feature_cols),
                    "importance": model.feature_importances_,
                    "model": name,
                }
            )
        )

        extracted = Parallel(n_jobs=n_jobs)(
            delayed(extract_tree_rules)(
                est,
                feature_cols,
                pos_df,
                fp_df,
                fp_target_mask,
                f"{name}_path",
                min_fp,
            )
            for est in tqdm(model.estimators_, desc=f"trees:{name}")
        )

        for batch in extracted:
            all_rules.extend(batch)

    unique = {}
    for r in all_rules:
        key = tuple(a.key() for a in r.atoms)
        if key not in unique or r.score > unique[key].score:
            unique[key] = r

    fi = pd.concat(importances, ignore_index=True)
    fi = (
        fi.groupby("feature", as_index=False)["importance"]
        .mean()
        .sort_values("importance", ascending=False)
    )

    return sorted(unique.values(), key=lambda r: (-r.fp_count, len(r.atoms), -r.score)), fi


# ======================================================================================
# Pass 3: local expansion
# ======================================================================================

def local_expand_rules(
    seed_rules: Sequence[Rule],
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    feature_cols: Sequence[str],
    fp_target_mask: np.ndarray,
    quantiles: Sequence[float],
    max_conditions: int,
    min_fp: int,
    trials_per_seed: int,
    rng: random.Random,
) -> List[Rule]:
    atoms, pos_masks, fp_masks = make_atom_masks(
        pos_df,
        fp_df,
        feature_cols,
        fp_target_mask,
        quantiles,
        min_fp_atom=max(1, min_fp // 2),
        max_positive_atom_rate=0.95,
    )

    atom_by_key = {a.key(): i for i, a in enumerate(atoms)}
    all_idx = list(range(len(atoms)))
    rules: List[Rule] = []

    for seed in tqdm(seed_rules, desc="Local expanding reject seeds"):
        seed_idxs = [atom_by_key[a.key()] for a in seed.atoms if a.key() in atom_by_key]
        same_feature_idxs = [
            i for i, a in enumerate(atoms) if a.feature in {sa.feature for sa in seed.atoms}
        ]
        candidates = same_feature_idxs or all_idx

        for _ in range(trials_per_seed):
            chosen = set(seed_idxs)

            # Randomly drop some constraints to try broader variants.
            for idx in list(chosen):
                if rng.random() < 0.20:
                    chosen.remove(idx)

            add_count = rng.randint(0, max(0, max_conditions - len(chosen)))
            if candidates:
                for idx in rng.sample(candidates, min(add_count, len(candidates))):
                    chosen.add(idx)

            if not chosen or len(chosen) > max_conditions:
                continue

            pm = np.ones(len(pos_df), dtype=bool)
            fm = np.ones(len(fp_df), dtype=bool)

            for idx in chosen:
                pm &= pos_masks[idx]
                fm &= fp_masks[idx]

            if int(pm.sum()) != 0:
                continue

            fp_count = int((fm & fp_target_mask).sum())
            if fp_count < min_fp:
                continue

            ratoms = [atoms[i] for i in sorted(chosen)]
            rules.append(
                rule_from_masks(
                    name=f"reject_expanded_{len(rules)+1}",
                    atoms=ratoms,
                    pos_mask=pm,
                    fp_mask=fm,
                    fp_target_mask=fp_target_mask,
                    source="local_expansion",
                )
            )

    unique = {}
    for r in rules:
        key = tuple(a.key() for a in r.atoms)
        if key not in unique or r.score > unique[key].score:
            unique[key] = r

    return sorted(unique.values(), key=lambda r: (-r.fp_count, len(r.atoms), -r.score))


# ======================================================================================
# Greedy selection/output
# ======================================================================================

def evaluate_rule_masks(rule: Rule, pos_df: pd.DataFrame, fp_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    pm = np.ones(len(pos_df), dtype=bool)
    fm = np.ones(len(fp_df), dtype=bool)
    for a in rule.atoms:
        pm &= mask_for_atom_df(pos_df, a)
        fm &= mask_for_atom_df(fp_df, a)
    return pm, fm


def greedy_select_reject_rules(
    rules: Sequence[Rule],
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    fp_target_mask: np.ndarray,
    max_rules: int,
    min_new_fp: int,
) -> List[Rule]:
    evaluated = []
    for r in rules:
        pm, fm = evaluate_rule_masks(r, pos_df, fp_df)
        pos_count = int(pm.sum())
        fp_count = int((fm & fp_target_mask).sum())
        if pos_count == 0 and fp_count > 0:
            r.pos_count = pos_count
            r.fp_count = fp_count
            evaluated.append((r, pm, fm))

    selected: List[Rule] = []
    covered_fp = np.zeros(len(fp_df), dtype=bool)

    for step in range(max_rules):
        best = None
        best_key = None

        for r, pm, fm in evaluated:
            if r in selected:
                continue
            new_fp = int((fm & fp_target_mask & ~covered_fp).sum())
            if new_fp < min_new_fp:
                continue

            key = (
                new_fp,
                r.fp_count,
                -len(r.atoms),
                r.score,
            )
            if best_key is None or key > best_key:
                best_key = key
                best = (r, pm, fm, new_fp)

        if best is None:
            break

        r, pm, fm, new_fp = best
        r.new_fp_gain = int(new_fp)
        selected.append(r)
        covered_fp |= (fm & fp_target_mask)

        print(
            f"[select {step+1:02d}] +{new_fp} new FPs | "
            f"covered={int(covered_fp.sum())} | "
            f"rule={r.name} fp={r.fp_count} cond={len(r.atoms)}"
        )

    return selected


def write_python_blocks(rules: Sequence[Rule], outpath: Path, prefix: str) -> None:
    chunks = []
    for i, r in enumerate(rules, start=1):
        reason_name = f"{prefix}_{i:02d}"
        chunks.append("# " + "=" * 96)
        chunks.append(f"# {reason_name}")
        chunks.append(f"# Selected gain: +{r.new_fp_gain} newly rejected target FPs")
        chunks.append(
            f"# Rejects: {r.fp_count} FPs / {r.pos_count} positives / "
            f"{len(r.atoms)} conditions / source={r.source}"
        )
        chunks.append(r.python_if_block(reason_name=reason_name))
        chunks.append("")
    outpath.write_text("\n".join(chunks), encoding="utf-8")


def write_variable_declarations(feature_cols: Sequence[str], outpath: Path) -> None:
    lines = []
    for feat in sorted(feature_cols):
        lines.append(f'{feature_to_var(feat)} = features_data["{feat}"]')
    outpath.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ======================================================================================
# Main
# ======================================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Feature-only reject-rule miner")
    p.add_argument("--outdir", required=True, type=Path)

    p.add_argument("--time-budget-minutes", type=float, default=240.0)
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--n-jobs", type=int, default=4)

    p.add_argument("--target-mode", choices=["all_fps", "currently_unrejected_fps"], default="all_fps")
    p.add_argument(
        "--target-overall-legit-trade-fps",
        action="store_true",
        help=(
            "Mine broad zero-positive-damage reject rules specifically for false-positive rows "
            "where feature_overall_legit_trade is True/nonzero. This overrides --target-mode "
            "for the mining target mask, but does not add feature_overall_legit_trade to the "
            "candidate feature set."
        ),
    )

    p.add_argument("--min-fp", type=int, default=10)
    p.add_argument("--max-depth", type=int, default=22)
    p.add_argument("--n-estimators", type=int, default=1200)

    p.add_argument("--beam-width", type=int, default=4000)
    p.add_argument("--beam-max-atoms", type=int, default=1000)
    p.add_argument("--beam-max-conditions", type=int, default=22)

    p.add_argument("--local-expansion", action="store_true")
    p.add_argument("--local-expansion-trials", type=int, default=3000)

    p.add_argument("--max-selected-rules", type=int, default=60)
    p.add_argument("--min-new-fp", type=int, default=3)

    p.add_argument(
        "--include-score-features",
        action="store_true",
        help="Include feature_*score columns. Default excludes them to avoid meta/leakage features.",
    )
    p.add_argument(
        "--exclude-regex",
        action="append",
        default=[],
        help="Additional feature-column exclusion regex. Can be passed multiple times.",
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    deadline = started + args.time_budget_minutes * 60.0 if args.time_budget_minutes > 0 else None

    print("Loading data...")
    pos_df = normalize_feature_frame(pd.read_csv("model/training/positive_results.csv"))
    fp_df = normalize_feature_frame(pd.read_csv("model/training/false_positive_results.csv"))

    exclude_regexes = list(args.exclude_regex or [])
    if not args.include_score_features:
        exclude_regexes = DEFAULT_EXCLUDE_FEATURE_REGEXES + exclude_regexes
    else:
        exclude_regexes = [r"^feature_overall_legit_trade$"] + exclude_regexes

    feature_cols = discover_feature_cols(pos_df, fp_df, exclude_regexes)
    print(f"Feature-only columns used: {len(feature_cols)}")
    (args.outdir / "feature_columns_used.json").write_text(json.dumps(feature_cols, indent=2), encoding="utf-8")
    write_variable_declarations(feature_cols, args.outdir / "variable_declarations.py")

    print("\n=== Current hard-rule reject analysis ===")

    hard_rules_path = Path("model/training/hard_rules.py")
    current_summary = analyze_existing_reject_rules(hard_rules_path, pos_df, fp_df, args.outdir)
    print("Current reject summary:", current_summary)

    module = load_hard_rules(hard_rules_path)
    reject_fn = module.should_be_rejected_by_hard_rules

    current_fp_rejected = []
    for _, row in fp_df.iterrows():
        current_fp_rejected.append(safe_reject(reject_fn, row.to_dict()))
    current_fp_rejected = np.array(current_fp_rejected, dtype=bool)

    if args.target_overall_legit_trade_fps:
        overall_col = "feature_overall_legit_trade"
        if overall_col not in fp_df.columns:
            raise ValueError(
                "--target-overall-legit-trade-fps was passed, but "
                "feature_overall_legit_trade is missing from the false-positive CSV."
            )
        fp_target_mask = fp_df[overall_col].fillna(0).astype(float).to_numpy() != 0
        target_description = "overall_legit_trade_true_fps"
    elif args.target_mode == "currently_unrejected_fps":
        fp_target_mask = ~current_fp_rejected
        target_description = "currently_unrejected_fps"
    else:
        fp_target_mask = np.ones(len(fp_df), dtype=bool)
        target_description = "all_fps"

    print(
        f"Target FPs for mining: {int(fp_target_mask.sum())} / {len(fp_df)} "
        f"({target_description})"
    )

    if fp_target_mask.sum() == 0:
        print("No target FPs to mine. Current reject rules already reject all target FPs.")
        # Still write summary and exit.
        summary = {
            **current_summary,
            "target_mode": args.target_mode,
            "target_overall_legit_trade_fps": bool(args.target_overall_legit_trade_fps),
            "target_description": target_description,
            "target_fp_count": int(fp_target_mask.sum()),
            "feature_count": int(len(feature_cols)),
            "all_zero_positive_damage_candidates": 0,
            "selected_reject_rules": 0,
            "selected_unique_fp_covered": 0,
            "elapsed_minutes": round((time.time() - started) / 60.0, 2),
        }
        (args.outdir / "final_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("Final summary:", summary)
        return

    quantiles = np.unique(
        np.r_[
            np.linspace(0.005, 0.995, 199),
            [0.001, 0.0025, 0.9975, 0.999],
        ]
    )

    all_rules: List[Rule] = []

    print("\n=== Pass 1: reject beam search ===")
    beam_rules = mine_reject_beam(
        pos_df=pos_df,
        fp_df=fp_df,
        feature_cols=feature_cols,
        fp_target_mask=fp_target_mask,
        quantiles=quantiles,
        min_fp=args.min_fp,
        max_conditions=args.beam_max_conditions,
        beam_width=args.beam_width,
        max_atoms=args.beam_max_atoms,
        time_deadline=deadline,
    )
    checkpoint_rules(beam_rules, args.outdir / "pass1_reject_beam_candidates.csv")
    all_rules.extend(beam_rules)
    print(f"Pass 1 reject rules: {len(beam_rules)}")

    print("\n=== Pass 2: reject deep tree/path mining ===")
    tree_rules, feature_importance = mine_reject_tree_paths(
        pos_df=pos_df,
        fp_df=fp_df,
        feature_cols=feature_cols,
        fp_target_mask=fp_target_mask,
        max_depth=args.max_depth,
        min_fp=args.min_fp,
        n_estimators=args.n_estimators,
        n_jobs=args.n_jobs,
        random_state=args.random_state,
    )
    checkpoint_rules(tree_rules, args.outdir / "pass2_reject_tree_candidates.csv")
    feature_importance.to_csv(args.outdir / "pass2_reject_feature_importance.csv", index=False)
    all_rules.extend(tree_rules)
    print(f"Pass 2 reject rules: {len(tree_rules)}")

    if args.local_expansion:
        print("\n=== Pass 3: local expansion ===")
        seeds = sorted(all_rules, key=lambda r: (-r.fp_count, len(r.atoms), -r.score))[:100]
        expanded = local_expand_rules(
            seed_rules=seeds,
            pos_df=pos_df,
            fp_df=fp_df,
            feature_cols=feature_cols,
            fp_target_mask=fp_target_mask,
            quantiles=quantiles,
            max_conditions=args.beam_max_conditions,
            min_fp=args.min_fp,
            trials_per_seed=args.local_expansion_trials,
            rng=random.Random(args.random_state),
        )
        checkpoint_rules(expanded, args.outdir / "pass3_reject_local_expansion_candidates.csv")
        all_rules.extend(expanded)
        print(f"Pass 3 reject rules: {len(expanded)}")

    print("\n=== Final aggregation/selection ===")
    unique = {}
    for r in all_rules:
        if r.pos_count != 0 or r.fp_count < args.min_fp:
            continue
        key = tuple(a.key() for a in r.atoms)
        if key not in unique or r.score > unique[key].score:
            unique[key] = r

    final_rules = sorted(unique.values(), key=lambda r: (-r.fp_count, len(r.atoms), -r.score))
    checkpoint_rules(final_rules, args.outdir / "all_zero_positive_damage_reject_candidates.csv")

    selected = greedy_select_reject_rules(
        rules=final_rules,
        pos_df=pos_df,
        fp_df=fp_df,
        fp_target_mask=fp_target_mask,
        max_rules=args.max_selected_rules,
        min_new_fp=args.min_new_fp,
    )

    checkpoint_rules(selected, args.outdir / "selected_reject_rules.csv")
    write_python_blocks(selected, args.outdir / "selected_reject_rules_python_blocks.py", "mined_reject_rule")

    covered_fp = np.zeros(len(fp_df), dtype=bool)
    for r in selected:
        _, fm = evaluate_rule_masks(r, pos_df, fp_df)
        covered_fp |= (fm & fp_target_mask)

    summary = {
        **current_summary,
        "target_mode": args.target_mode,
        "target_overall_legit_trade_fps": bool(args.target_overall_legit_trade_fps),
        "target_description": target_description,
        "target_fp_count": int(fp_target_mask.sum()),
        "feature_count": int(len(feature_cols)),
        "all_zero_positive_damage_candidates": int(len(final_rules)),
        "selected_reject_rules": int(len(selected)),
        "selected_unique_fp_covered": int(covered_fp.sum()),
        "selected_unique_fp_coverage_pct": float(covered_fp.sum() / max(1, fp_target_mask.sum())),
        "elapsed_minutes": round((time.time() - started) / 60.0, 2),
    }

    print("Final summary:", summary)
    (args.outdir / "final_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\nDone. Main outputs:")
    print(f"  {args.outdir / 'existing_reject_rule_first_hit_stats.csv'}")
    print(f"  {args.outdir / 'existing_reject_rules_unreachable_by_order.csv'}")
    print(f"  {args.outdir / 'all_zero_positive_damage_reject_candidates.csv'}")
    print(f"  {args.outdir / 'selected_reject_rules.csv'}")
    print(f"  {args.outdir / 'selected_reject_rules_python_blocks.py'}")
    print(f"  {args.outdir / 'final_summary.json'}")


if __name__ == "__main__":
    main()
