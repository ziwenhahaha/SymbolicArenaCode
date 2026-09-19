#!/usr/bin/env python3
"""Build nested Core50/Core60/Core70/Core80 subsets for SymbolicArena.

Core50 is reproduced by the recovered compatibility selector.  Each larger
subset is solved sequentially with the preceding subset fixed, so the output
guarantees Core50 ⊂ Core60 ⊂ Core70 ⊂ Core80.  The family quotas and selected
coverage caps scale with the requested size; semantic-duplicate and basename
caps remain one at every size.

Example
-------
python core50_60_70_80_selector.py \
  --input postprocess_final_20260501-105508_664+4+3result.zip \
  --outdir nested_core_sets
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

import core50_selector_recovered as base


TARGET_SIZES = (50, 60, 70, 80)


def family_quotas(
    data: pd.DataFrame, size: int
) -> dict[str, tuple[int, int, float]]:
    counts = data["family"].astype(str).value_counts()
    n_family = len(counts)
    quotas: dict[str, tuple[int, int, float]] = {}
    for family, count in counts.items():
        target = size * (0.6 * float(count) / len(data) + 0.4 / n_family)
        quotas[str(family)] = (
            max(1, math.floor(target - 1.0)),
            math.ceil(target + 2.0),
            target,
        )
    return quotas


def scaled_cap(base_cap: int, size: int) -> int:
    return max(base_cap, math.ceil(base_cap * size / 50.0))


def add_group_cap(
    rows: list[np.ndarray],
    lower: list[float],
    upper: list[float],
    data: pd.DataFrame,
    column: str,
    cap: int,
) -> None:
    values = data[column].fillna("__NA__").astype(str)
    for _, indices in values.groupby(values).groups.items():
        if len(indices) <= cap:
            continue
        row = np.zeros(len(data), dtype=float)
        row[list(indices)] = 1.0
        rows.append(row)
        lower.append(-np.inf)
        upper.append(float(cap))


def eligible_mask(data: pd.DataFrame) -> pd.Series:
    return (
        (pd.to_numeric(data["dataset_valid_rate"], errors="coerce").fillna(0) >= 0.5)
        & (pd.to_numeric(data["wrong_dataset_runs"], errors="coerce").fillna(1) == 0)
        & (pd.to_numeric(data["completion_rate"], errors="coerce").fillna(0) >= 1.0)
    )


def solve_extension(
    data: pd.DataFrame,
    scores: np.ndarray,
    size: int,
    required_ids: set[str],
) -> tuple[pd.DataFrame, dict[str, object]]:
    n = len(data)
    dataset_ids = data["dataset_id"].astype(str)
    rows: list[np.ndarray] = [np.ones(n, dtype=float)]
    lower: list[float] = [float(size)]
    upper: list[float] = [float(size)]

    quotas = family_quotas(data, size)
    for family, (qmin, qmax, _) in quotas.items():
        rows.append((data["family"].astype(str) == family).to_numpy(dtype=float))
        lower.append(float(qmin))
        upper.append(float(qmax))

    add_group_cap(rows, lower, upper, data, "semantic_duplicate_group", 1)
    add_group_cap(rows, lower, upper, data, "basename", 1)
    add_group_cap(rows, lower, upper, data, "subgroup", scaled_cap(8, size))

    for column, value, cap in [
        ("eligible_class", "limited_quota", scaled_cap(8, size)),
        ("difficulty_bin", "extreme", scaled_cap(6, size)),
        ("failure_mode", "one_sided", scaled_cap(5, size)),
    ]:
        rows.append((data[column].astype(str) == value).to_numpy(dtype=float))
        lower.append(-np.inf)
        upper.append(float(cap))

    allowed = eligible_mask(data)
    for index in np.flatnonzero(~allowed.to_numpy()):
        row = np.zeros(n, dtype=float)
        row[index] = 1.0
        rows.append(row)
        lower.append(0.0)
        upper.append(0.0)

    required_indices = np.flatnonzero(dataset_ids.isin(required_ids).to_numpy())
    if len(required_indices) != len(required_ids):
        missing = sorted(required_ids - set(dataset_ids))
        raise ValueError(f"Required datasets are absent from the reservoir: {missing}")
    for index in required_indices:
        row = np.zeros(n, dtype=float)
        row[index] = 1.0
        rows.append(row)
        lower.append(1.0)
        upper.append(1.0)

    constraints = LinearConstraint(
        np.vstack(rows), np.asarray(lower), np.asarray(upper)
    )
    result = milp(
        c=-scores,
        integrality=np.ones(n),
        bounds=Bounds(0, 1),
        constraints=constraints,
        options={"time_limit": 60, "mip_rel_gap": 0.0},
    )
    if not result.success:
        raise RuntimeError(f"Core{size} MILP failed: {result.message}")

    selected = data.loc[np.asarray(result.x) > 0.5].copy()
    if len(selected) != size:
        raise RuntimeError(f"Solver returned {len(selected)} tasks for Core{size}")
    selected_ids = set(selected["dataset_id"].astype(str))
    if not required_ids <= selected_ids:
        raise RuntimeError(f"Core{size} lost required members")

    info: dict[str, object] = {
        "success": bool(result.success),
        "message": str(result.message),
        "objective_sum": float(scores[np.asarray(result.x) > 0.5].sum()),
        "required_previous_size": len(required_ids),
        "added_count": size - len(required_ids),
        "scaled_caps": {
            "subgroup": scaled_cap(8, size),
            "limited_quota": scaled_cap(8, size),
            "extreme": scaled_cap(6, size),
            "one_sided": scaled_cap(5, size),
        },
        "family_quotas": {
            family: {"min": qmin, "max": qmax, "target": target}
            for family, (qmin, qmax, target) in quotas.items()
        },
    }
    return selected, info


def audit_subset(
    selected: pd.DataFrame,
    reservoir: pd.DataFrame,
    size: int,
) -> dict[str, object]:
    quotas = family_quotas(reservoir, size)
    family_counts = selected["family"].astype(str).value_counts().to_dict()
    duplicate_max = int(selected["semantic_duplicate_group"].value_counts().max())
    basename_max = int(selected["basename"].value_counts().max())
    subgroup_max = int(selected["subgroup"].value_counts().max())
    limited_count = int((selected["eligible_class"] == "limited_quota").sum())
    extreme_count = int((selected["difficulty_bin"] == "extreme").sum())
    one_sided_count = int((selected["failure_mode"] == "one_sided").sum())
    checks = {
        "size_ok": len(selected) == size,
        "family_quota_ok": all(
            qmin <= int(family_counts.get(family, 0)) <= qmax
            for family, (qmin, qmax, _) in quotas.items()
        ),
        "semantic_duplicate_ok": duplicate_max <= 1,
        "basename_ok": basename_max <= 1,
        "subgroup_cap_ok": subgroup_max <= scaled_cap(8, size),
        "limited_quota_ok": limited_count <= scaled_cap(8, size),
        "extreme_ok": extreme_count <= scaled_cap(6, size),
        "one_sided_ok": one_sided_count <= scaled_cap(5, size),
    }
    return {
        "size": int(len(selected)),
        "family_counts": family_counts,
        "difficulty_counts": selected["difficulty_bin"].value_counts().to_dict(),
        "failure_mode_counts": selected["failure_mode"].value_counts().to_dict(),
        "subgroup_max": subgroup_max,
        "semantic_duplicate_max": duplicate_max,
        "basename_max": basename_max,
        "limited_quota_count": limited_count,
        "extreme_count": extreme_count,
        "one_sided_count": one_sided_count,
        **checks,
        "all_constraints_ok": bool(all(checks.values())),
    }


def write_subset_csv(
    data: pd.DataFrame,
    selected_ids: set[str],
    previous_ids: set[str],
    size: int,
    outdir: Path,
) -> None:
    selected = data[data["dataset_id"].astype(str).isin(selected_ids)].copy()
    selected["in_previous_core"] = selected["dataset_id"].astype(str).isin(previous_ids)
    selected["new_at_size"] = ~selected["in_previous_core"]
    selected = selected.sort_values(
        ["new_at_size", "family", "subgroup", "compatibility_score", "dataset_id"],
        ascending=[True, True, True, False, True],
    ).reset_index(drop=True)
    selected[f"core{size}_rank"] = np.arange(1, len(selected) + 1)
    columns = [
        f"core{size}_rank",
        "dataset_id",
        "dataset_name",
        "dataset_rel",
        "family",
        "subgroup",
        "metadata_class",
        "basename",
        "semantic_duplicate_group",
        "formula_hash",
        "feature_count",
        "total_samples",
        "operator_group",
        "difficulty_bin",
        "failure_mode",
        "winner_probe",
        "eligible_class",
        "compatibility_score",
        "selection_score_simple",
        "info_score",
        "discrimination_score",
        "stability_score",
        "in_previous_core",
        "new_at_size",
    ]
    selected[[column for column in columns if column in selected.columns]].to_csv(
        outdir / f"core{size}.csv", index=False
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("nested_core_sets"))
    parser.add_argument("--allow-input-mismatch", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    outdir = args.outdir.expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nested_core_selector_") as temp:
        level_path, algorithm_path = base.unpack_input(input_path, Path(temp))
        hashes = base.validate_snapshot(
            level_path, algorithm_path, args.allow_input_mismatch
        )
        data = pd.read_csv(level_path)

    compatibility_scores, labels = base.build_compatibility_scores(data)
    data["compatibility_score"] = compatibility_scores
    data["selection_info_score"] = base.minmax(data["info_score"])
    data["selection_disc_score"] = base.minmax(data["discrimination_score"])
    data["selection_stability_score"] = base.minmax(data["stability_score"])
    data["selection_score_simple"] = (
        0.45 * data["selection_info_score"]
        + 0.20 * data["selection_disc_score"]
        + 0.35 * data["selection_stability_score"]
    )

    core50, core50_solver = base.solve_selection(data, compatibility_scores)
    selections: dict[int, pd.DataFrame] = {50: core50}
    solver_info: dict[str, object] = {"core50": core50_solver}

    previous_ids = set(core50["dataset_id"].astype(str))
    for size in TARGET_SIZES[1:]:
        selected, info = solve_extension(
            data, compatibility_scores, size, previous_ids
        )
        selections[size] = selected
        solver_info[f"core{size}"] = info
        previous_ids = set(selected["dataset_id"].astype(str))

    audits: dict[str, object] = {}
    previous_ids = set()
    for size in TARGET_SIZES:
        selected_ids = set(selections[size]["dataset_id"].astype(str))
        write_subset_csv(data, selected_ids, previous_ids, size, outdir)
        audit = audit_subset(selections[size], data, size)
        audit["contains_previous"] = previous_ids <= selected_ids
        audit["added_dataset_ids"] = sorted(selected_ids - previous_ids)
        audits[f"core{size}"] = audit
        data[f"selected_core{size}"] = data["dataset_id"].astype(str).isin(
            selected_ids
        )
        previous_ids = selected_ids

    embedded_ids = set(data.loc[labels == 1, "dataset_id"].astype(str))
    core50_ids = set(selections[50]["dataset_id"].astype(str))
    audit_document = {
        "target_sizes": list(TARGET_SIZES),
        "nested_chain_ok": all(
            set(selections[left]["dataset_id"].astype(str))
            <= set(selections[right]["dataset_id"].astype(str))
            for left, right in zip(TARGET_SIZES, TARGET_SIZES[1:])
        ),
        "core50_historical_overlap": len(core50_ids & embedded_ids),
        "core50_historical_only": sorted(embedded_ids - core50_ids),
        "core50_recovered_only": sorted(core50_ids - embedded_ids),
        "all_constraints_ok": all(
            bool(audits[f"core{size}"]["all_constraints_ok"])
            for size in TARGET_SIZES
        ),
        "input": hashes,
        "model": {
            "type": "ExtraTreesClassifier",
            "n_estimators": 12,
            "max_depth": 9,
            "random_state": 1,
            "id_features_used": False,
        },
        "solver": solver_info,
        "subsets": audits,
    }
    with (outdir / "nested_selection_audit.json").open("w", encoding="utf-8") as handle:
        json.dump(audit_document, handle, ensure_ascii=False, indent=2)

    entry_size = np.full(len(data), np.nan)
    for size in reversed(TARGET_SIZES):
        entry_size[data[f"selected_core{size}"].to_numpy()] = size
    data["first_core_size"] = pd.array(entry_size, dtype="Int64")
    data.sort_values("global_index").to_csv(
        outdir / "selection_scores_664_nested.csv", index=False
    )

    report_lines = [
        "# Nested Core50 / Core60 / Core70 / Core80 audit",
        "",
        f"- nested chain: `{audit_document['nested_chain_ok']}`",
        f"- Core50 historical overlap: `{audit_document['core50_historical_overlap']}/50`",
        f"- all implemented constraints pass: `{audit_document['all_constraints_ok']}`",
        "",
        "| subset | size | new items | contains previous | constraints |",
        "|---|---:|---:|---:|---:|",
    ]
    for size in TARGET_SIZES:
        audit = audits[f"core{size}"]
        report_lines.append(
            f"| Core{size} | {audit['size']} | {len(audit['added_dataset_ids'])} | "
            f"{audit['contains_previous']} | {audit['all_constraints_ok']} |"
        )
    report_lines.extend(
        [
            "",
            "Each extension maximizes the recovered Core50 compatibility score while fixing every member of the preceding subset. Family quotas and coverage caps scale with subset size; semantic-duplicate and basename caps remain one.",
        ]
    )
    (outdir / "NESTED_SELECTION_REPORT.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    print("Nested Core subsets complete")
    print(f"output: {outdir}")
    print(f"nested chain: {audit_document['nested_chain_ok']}")
    print(f"Core50 overlap: {audit_document['core50_historical_overlap']}/50")
    print(f"constraints: {audit_document['all_constraints_ok']}")


if __name__ == "__main__":
    main()
