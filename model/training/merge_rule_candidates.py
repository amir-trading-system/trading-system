#!/usr/bin/env python3
"""
Merge multiple deep_rule_miner seed outputs and run a final greedy selection.

It loads all_zero_fp_candidates.csv from multiple seed folders, deduplicates rules,
re-evaluates them on the original positive/FP CSVs, keeps true 0-FP rules, then
selects the best non-redundant set for maximum currently-untagged positive coverage.

COMMAND:
python merge_rule_candidates.py \
  --seed-dirs \
    mining_out_88_seed_42 \
    mining_out_88_seed_101 \
    mining_out_88_seed_202 \
    mining_out_88_seed_303 \
    mining_out_88_seed_404 \
  --outdir mining_out_88_MERGED \
  --max-selected-rules 60 \
  --min-new-untagged 2

"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm


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
    source: str
    base_reason: str
    atoms: List[Atom]
    condition_original: str
    seed_dir: str
    pos_count: int = 0
    fp_count: int = 0
    untagged_pos_count: int = 0
    tagged_pos_count: int = 0
    n_conditions: int = 0
    score: float = 0.0
    new_untagged_gain: int = 0

    def condition_str(self) -> str:
        return " and ".join(a.expr() for a in self.atoms)

    def python_if_block(self, reason_name: Optional[str] = None, indent: str = "    ") -> str:
        reason_name = reason_name or self.name
        lines = []
        lines.append(f"{indent}# Covers: {self.pos_count} positives / {self.fp_count} FP")
        lines.append(
            f"{indent}# Includes: {self.untagged_pos_count} untagged / "
            f"{self.tagged_pos_count} already-tagged / {len(self.atoms)} conditions"
        )
        lines.append(f"{indent}if (")
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


def feature_to_var(feature: str) -> str:
    return feature[len("feature_"):] if feature.startswith("feature_") else feature


def var_to_feature(var: str, columns: Sequence[str]) -> str:
    if var in columns:
        return var
    f = f"feature_{var}"
    if f in columns:
        return f
    return f


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


def load_hard_rules(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("loaded_hard_rules_for_merge", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import hard_rules from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["loaded_hard_rules_for_merge"] = module
    spec.loader.exec_module(module)
    return module


def safe_success_patterns(fn: Callable, features: Dict[str, Any]) -> Tuple[int, List[str]]:
    try:
        out = fn(features)
        if isinstance(out, tuple) and len(out) >= 2:
            score, reasons = out[0], out[1]
            return int(score), list(reasons or [])
        if isinstance(out, list):
            return len(out), list(out)
        if isinstance(out, bool):
            return int(out), []
        return int(out), []
    except Exception:
        return 0, []


def compute_current_tags(hard_rules_path: Path, pos_df: pd.DataFrame, fp_df: pd.DataFrame):
    module = load_hard_rules(hard_rules_path)
    if not hasattr(module, "success_patterns"):
        raise AttributeError("hard_rules.py does not contain success_patterns(features_data)")
    fn = module.success_patterns

    pos_scores = []
    pos_reasons = []
    for _, row in tqdm(pos_df.iterrows(), total=len(pos_df), desc="Evaluating positives"):
        s, r = safe_success_patterns(fn, row.to_dict())
        pos_scores.append(s)
        pos_reasons.append(r)

    fp_scores = []
    fp_reasons = []
    for _, row in tqdm(fp_df.iterrows(), total=len(fp_df), desc="Evaluating FPs"):
        s, r = safe_success_patterns(fn, row.to_dict())
        fp_scores.append(s)
        fp_reasons.append(r)

    return (
        np.array(pos_scores) > 0,
        np.array(fp_scores) > 0,
        pos_reasons,
        fp_reasons,
    )


def parse_condition(condition: str, columns: Sequence[str]) -> List[Atom]:
    """Parse simple threshold conjunctions joined by 'and'."""
    if not isinstance(condition, str) or not condition.strip():
        return []

    text = re.sub(r"\s+", " ", condition.strip().replace("\n", " "))
    parts = re.split(r"\s+and\s+", text)
    atoms: List[Atom] = []

    for part in parts:
        part = part.strip().strip("() ")
        if not part:
            continue
        if " in reasons" in part:
            continue

        m = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>|>=|<)\s*(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$",
            part,
        )
        if not m:
            raise ValueError(f"Cannot parse condition atom: {part!r} from {condition!r}")

        var, op, threshold_s = m.groups()
        threshold = float(threshold_s)

        if op == "<":
            op = "<="
        elif op == ">=":
            op = ">"

        feat = var_to_feature(var, columns)
        if feat not in columns:
            raise ValueError(f"Parsed feature {feat!r} not found in data columns for atom {part!r}")

        atoms.append(Atom(feat, op, threshold))

    return compress_atoms(atoms)


def compress_atoms(atoms: List[Atom]) -> List[Atom]:
    lower: Dict[str, float] = {}
    upper: Dict[str, float] = {}

    for a in atoms:
        if a.op == ">":
            lower[a.feature] = max(lower.get(a.feature, -np.inf), a.threshold)
        elif a.op == "<=":
            upper[a.feature] = min(upper.get(a.feature, np.inf), a.threshold)
        else:
            raise ValueError(a.op)

    out: List[Atom] = []
    for feat in sorted(set(lower) | set(upper)):
        if feat in lower and np.isfinite(lower[feat]):
            out.append(Atom(feat, ">", float(lower[feat])))
        if feat in upper and np.isfinite(upper[feat]):
            out.append(Atom(feat, "<=", float(upper[feat])))
    return out


def mask_for_atom(df: pd.DataFrame, atom: Atom) -> np.ndarray:
    v = df[atom.feature].to_numpy(float)
    if atom.op == "<=":
        return v <= atom.threshold
    if atom.op == ">":
        return v > atom.threshold
    raise ValueError(atom.op)


def evaluate_rule(
    rule: Rule,
    pos_df: pd.DataFrame,
    fp_df: pd.DataFrame,
    untagged_pos_mask: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, Rule]:
    pm = np.ones(len(pos_df), dtype=bool)
    fm = np.ones(len(fp_df), dtype=bool)

    for atom in rule.atoms:
        pm &= mask_for_atom(pos_df, atom)
        fm &= mask_for_atom(fp_df, atom)

    pos_count = int(pm.sum())
    fp_count = int(fm.sum())
    untagged = int((pm & untagged_pos_mask).sum())
    tagged = pos_count - untagged

    rule.pos_count = pos_count
    rule.fp_count = fp_count
    rule.untagged_pos_count = untagged
    rule.tagged_pos_count = tagged
    rule.n_conditions = len(rule.atoms)
    rule.score = (
        untagged * 100.0
        + pos_count * 3.0
        - tagged * 2.0
        - fp_count * 100000.0
        - len(rule.atoms) * 0.25
    )

    return pm, fm, rule


def load_candidate_csvs(seed_dirs: Sequence[Path], columns: Sequence[str]) -> List[Rule]:
    rules: List[Rule] = []

    for seed_dir in seed_dirs:
        path = seed_dir / "all_zero_fp_candidates.csv"
        if not path.exists():
            print(f"[WARN] Missing {path}, skipping")
            continue

        df = pd.read_csv(path)
        if "condition" not in df.columns:
            print(f"[WARN] {path} has no 'condition' column, skipping")
            continue

        for i, row in df.iterrows():
            condition = row.get("condition", "")
            try:
                atoms = parse_condition(str(condition), columns)
            except Exception as e:
                print(f"[WARN] Could not parse condition in {path} row {i}: {e}")
                continue

            if not atoms:
                continue

            base_reason = str(row.get("base_reason", "") or "").strip()
            source = str(row.get("source", "") or "merged_source").strip()
            name = str(row.get("name", "") or f"{seed_dir.name}_rule_{i}").strip()

            rules.append(
                Rule(
                    name=name,
                    source=source,
                    base_reason=base_reason,
                    atoms=atoms,
                    condition_original=str(condition),
                    seed_dir=str(seed_dir),
                )
            )

    return rules


def deduplicate_rules(rules: Sequence[Rule]) -> List[Rule]:
    unique: Dict[Tuple[str, Tuple[Tuple[str, str, float], ...]], Rule] = {}

    for r in rules:
        key = (r.base_reason, tuple(a.key() for a in r.atoms))
        if key not in unique:
            unique[key] = r
        else:
            existing = unique[key]
            if r.source not in existing.source.split("|"):
                existing.source = existing.source + "|" + r.source
            if r.seed_dir not in existing.seed_dir.split("|"):
                existing.seed_dir = existing.seed_dir + "|" + r.seed_dir

    return list(unique.values())


def greedy_select(
    evaluated: List[Tuple[Rule, np.ndarray, np.ndarray]],
    untagged_pos_mask: np.ndarray,
    max_selected_rules: int,
    min_new_untagged: int,
    prefer_simple: bool,
) -> List[Rule]:
    selected: List[Rule] = []
    covered_untagged = np.zeros(len(untagged_pos_mask), dtype=bool)
    remaining = [(r, pm, fm) for r, pm, fm in evaluated if r.fp_count == 0]

    for step in range(max_selected_rules):
        best = None
        best_key = None

        for r, pm, fm in remaining:
            if r in selected:
                continue

            new_untagged = int((pm & untagged_pos_mask & ~covered_untagged).sum())
            if new_untagged < min_new_untagged:
                continue

            if prefer_simple:
                key = (new_untagged, r.untagged_pos_count, r.pos_count, -r.n_conditions, r.score)
            else:
                key = (new_untagged, r.untagged_pos_count, r.pos_count, r.score, -r.n_conditions)

            if best_key is None or key > best_key:
                best = (r, pm, fm, new_untagged)
                best_key = key

        if best is None:
            break

        r, pm, fm, new_untagged = best
        r.new_untagged_gain = int(new_untagged)
        selected.append(r)
        covered_untagged |= (pm & untagged_pos_mask)

        print(
            f"[select {step+1:02d}] +{new_untagged} new untagged | "
            f"covered={int(covered_untagged.sum())} | "
            f"rule={r.name} | pos={r.pos_count} unt={r.untagged_pos_count} "
            f"tagged={r.tagged_pos_count} cond={r.n_conditions}"
        )

    return selected


def rules_to_frame(rules: Sequence[Rule]) -> pd.DataFrame:
    rows = []
    for r in rules:
        rows.append({
            "name": r.name,
            "source": r.source,
            "base_reason": r.base_reason,
            "seed_dir": r.seed_dir,
            "pos_count": r.pos_count,
            "fp_count": r.fp_count,
            "untagged_pos_count": r.untagged_pos_count,
            "tagged_pos_count": r.tagged_pos_count,
            "new_untagged_gain": r.new_untagged_gain,
            "n_conditions": r.n_conditions,
            "score": r.score,
            "condition": r.condition_str(),
            "condition_original": r.condition_original,
            "python_if": r.python_if_block(),
        })
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(
            ["fp_count", "untagged_pos_count", "pos_count", "new_untagged_gain", "n_conditions", "score"],
            ascending=[True, False, False, False, True, False],
        )
    return df


def write_python_blocks(rules: Sequence[Rule], outpath: Path, reason_prefix: str) -> None:
    chunks = []
    for i, r in enumerate(rules, start=1):
        reason = f"{reason_prefix}_{i:02d}"
        chunks.append("# " + "=" * 96)
        chunks.append(f"# {reason}")
        chunks.append(f"# Selected gain: +{r.new_untagged_gain} new untagged positives")
        chunks.append(
            f"# Covers: {r.pos_count} positives / {r.fp_count} FP / "
            f"{r.untagged_pos_count} untagged / {r.tagged_pos_count} already-tagged / "
            f"{r.n_conditions} conditions"
        )
        chunks.append(f"# Source: {r.source}")
        chunks.append(f"# Seed dir: {r.seed_dir}")
        chunks.append(r.python_if_block(reason_name=reason))
        chunks.append("")
    outpath.write_text("\n".join(chunks), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge seed candidate files and run greedy selection")
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--seed-dirs", nargs="+", required=True, type=Path)
    p.add_argument("--positive-tags-file", type=Path, default=None)

    p.add_argument("--max-selected-rules", type=int, default=60)
    p.add_argument("--min-new-untagged", type=int, default=2)
    p.add_argument("--min-total-positives", type=int, default=1)
    p.add_argument("--min-total-untagged", type=int, default=1)
    p.add_argument("--max-fp", type=int, default=0)
    p.add_argument("--prefer-simple", action="store_true")
    p.add_argument("--reason-prefix", default="merged_untagged_rule")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    print("Loading original data...")
    pos_df = normalize_feature_frame(pd.read_csv("model/training/positive_results.csv"))
    fp_df = normalize_feature_frame(pd.read_csv("model/training/false_positive_results.csv"))
    all_columns = list(pos_df.columns)

    tagged_pos_mask, tagged_fp_mask, _, _ = compute_current_tags("model/training/hard_rules.py", pos_df, fp_df)

    untagged_pos_mask = ~tagged_pos_mask

    baseline = {
        "positives": int(len(pos_df)),
        "false_positives": int(len(fp_df)),
        "tagged_positives": int(tagged_pos_mask.sum()),
        "untagged_positives": int(untagged_pos_mask.sum()),
        "currently_tagged_fps": int(tagged_fp_mask.sum()),
    }
    print("Baseline:", baseline)
    (args.outdir / "baseline.json").write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    print("Loading seed candidates...")
    loaded_rules = load_candidate_csvs(args.seed_dirs, all_columns)
    print(f"Loaded raw rules: {len(loaded_rules)}")

    deduped_rules = deduplicate_rules(loaded_rules)
    print(f"Deduplicated rules: {len(deduped_rules)}")

    evaluated: List[Tuple[Rule, np.ndarray, np.ndarray]] = []
    for r in tqdm(deduped_rules, desc="Re-evaluating merged rules"):
        try:
            pm, fm, rr = evaluate_rule(r, pos_df, fp_df, untagged_pos_mask)
        except Exception as e:
            print(f"[WARN] Failed evaluating {r.name}: {e}")
            continue

        if (
            rr.fp_count <= args.max_fp
            and rr.pos_count >= args.min_total_positives
            and rr.untagged_pos_count >= args.min_total_untagged
        ):
            evaluated.append((rr, pm, fm))

    print(f"Rules after filters: {len(evaluated)}")

    all_valid_rules = [r for r, _, _ in evaluated]
    all_valid_df = rules_to_frame(all_valid_rules)
    all_valid_df.to_csv(args.outdir / "merged_all_valid_candidates.csv", index=False)

    print("Running greedy selection...")
    selected = greedy_select(
        evaluated=evaluated,
        untagged_pos_mask=untagged_pos_mask,
        max_selected_rules=args.max_selected_rules,
        min_new_untagged=args.min_new_untagged,
        prefer_simple=args.prefer_simple,
    )

    selected_df = rules_to_frame(selected)
    selected_df.to_csv(args.outdir / "merged_selected_rules.csv", index=False)
    write_python_blocks(selected, args.outdir / "merged_selected_rules_python_blocks.py", args.reason_prefix)

    covered_untagged = np.zeros(len(pos_df), dtype=bool)
    covered_pos = np.zeros(len(pos_df), dtype=bool)
    covered_fp = np.zeros(len(fp_df), dtype=bool)

    selected_ids = {id(r) for r in selected}
    for r, pm, fm in evaluated:
        if id(r) not in selected_ids:
            continue
        covered_pos |= pm
        covered_untagged |= (pm & untagged_pos_mask)
        covered_fp |= fm

    summary = {
        **baseline,
        "seed_dirs": [str(p) for p in args.seed_dirs],
        "raw_rules_loaded": int(len(loaded_rules)),
        "deduplicated_rules": int(len(deduped_rules)),
        "valid_rules_after_reeval": int(len(evaluated)),
        "selected_rules": int(len(selected)),
        "selected_unique_positives_covered": int(covered_pos.sum()),
        "selected_unique_untagged_covered": int(covered_untagged.sum()),
        "selected_unique_untagged_coverage_pct": float(covered_untagged.sum() / max(1, untagged_pos_mask.sum())),
        "selected_unique_fp_covered": int(covered_fp.sum()),
    }
    print("Final summary:", summary)
    (args.outdir / "merged_final_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\nDone. Main outputs:")
    print(f"  {args.outdir / 'merged_all_valid_candidates.csv'}")
    print(f"  {args.outdir / 'merged_selected_rules.csv'}")
    print(f"  {args.outdir / 'merged_selected_rules_python_blocks.py'}")
    print(f"  {args.outdir / 'merged_final_summary.json'}")


if __name__ == "__main__":
    main()
