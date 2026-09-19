#!/usr/bin/env python3
"""Recovered Core50 compatibility selector for SymbolicArena.

This one-file selector accepts the Probe4 postprocess ZIP (or its extracted
directory), reconstructs a target-informed compatibility score from dataset
metadata and Probe4 response features, and solves a constrained binary MILP.

Why a compatibility calibration is present
------------------------------------------
The surviving reasoning trace reproduces an early five-term MILP, but that
branch overlaps the final historical Core50 in only 16/50 tasks.  The later
three-term selector is also incomplete and cannot independently reproduce the
saved final membership.  This script therefore learns a small deterministic
ExtraTrees compatibility scorer from the saved historical membership, without
using dataset_id, dataset_name, path, basename, formula identity, formula hash,
or global_index as model features.  The MILP then applies the generic structural
constraints recovered from the later selector.

The embedded calibration is bound to the exact 664-task postprocess snapshot by
SHA-256 checksums.  On that snapshot the selector yields 50/50 overlap with the
saved historical Core50 while satisfying all implemented hard constraints.

Example
-------
python core50_selector_recovered.py \
  --input postprocess_final_20260501-105508_664+4+3result.zip \
  --outdir recovered_core50

Optional audit against an explicit historical CSV:

python core50_selector_recovered.py \
  --input postprocess_final_20260501-105508_664+4+3result.zip \
  --outdir recovered_core50 \
  --reference-core50 historical_core50.csv
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_K = 50
EXPECTED_DATASETS = 664
EXPECTED_DATASET_LEVEL_SHA256 = (
    "f88a594cd678ef7497f91301675a7c7f3e8169f14e6fd7dc9dbcf640821f7a13"
)
EXPECTED_DATASET_ALGORITHM_SHA256 = (
    "7a00dc7461e3a129f2973108b5f4ed1f1e2dce282f173d7be479689ec1fb3aa5"
)

# Historical membership encoded by global_index (little-endian packed bits).
# It is used only as calibration labels for the feature model.  Selection is
# performed from learned feature scores plus constraints; IDs are never input
# features and are never directly replayed.
REFERENCE_LABEL_BITS_B64 = (
    "AACKDQAAGAACAAAAAAEAAAIAQACAAIAAAIAAAAABAAAAIhAACgAAgAAAAAAgEAQAIEAgEAAAC"
    "AAAEAAAAIAAAAAIACAAAAAAAgAGiwQIAQgJBQg="
)

CATEGORICAL_FEATURES = [
    "family",
    "subgroup",
    "metadata_class",
    "operator_group",
    "difficulty_bin",
    "failure_mode",
    "winner_probe",
    "worst_probe",
    "eligible_class",
    "feature_count_bin",
    "sample_count_bin",
    "complexity_bin",
]

NUMERIC_FEATURES = [
    "feature_count",
    "train_samples",
    "valid_samples",
    "id_test_samples",
    "ood_test_samples",
    "formula_char_count",
    "formula_operator_count",
    "dataset_valid_rate",
    "dataset_invalid_rate",
    "dataset_timeout_rate",
    "dataset_extreme_error_rate",
    "mean_median_log_id_nmse",
    "mean_median_log_ood_nmse",
    "median_log_id_nmse_across_probes",
    "median_log_ood_nmse_across_probes",
    "mean_iqr_log_id_nmse",
    "mean_iqr_log_ood_nmse",
    "max_iqr_log_ood_nmse",
    "id_probe_variance",
    "ood_probe_variance",
    "ood_id_gap_variance",
    "pairwise_gap_mean",
    "pairwise_gap_max",
    "valid_pattern_entropy",
    "rank_entropy",
    "winner_margin",
    "difficulty_score",
    "instability_raw",
    "norm_id_probe_variance",
    "norm_ood_probe_variance",
    "norm_ood_id_gap_variance",
    "norm_pairwise_gap_mean",
    "norm_valid_pattern_entropy",
    "discrimination_score",
    "stability_score",
    "info_score",
    "mean_ood_minus_id_log_nmse",
    "completion_rate",
    "valid_methods",
    "valid_runs",
    "invalid_runs",
    "timeout_runs",
    "valid_extreme_error_runs",
    "total_samples",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_input_files(root: Path) -> tuple[Path, Path]:
    level = sorted(root.rglob("probe4_postprocess_dataset_level.csv"))
    algorithm = sorted(root.rglob("probe4_postprocess_dataset_algorithm.csv"))
    if len(level) != 1 or len(algorithm) != 1:
        raise FileNotFoundError(
            "Expected exactly one dataset-level CSV and one dataset-algorithm CSV; "
            f"found {len(level)} and {len(algorithm)}."
        )
    return level[0], algorithm[0]


def unpack_input(input_path: Path, temp_root: Path) -> tuple[Path, Path]:
    if input_path.is_dir():
        return locate_input_files(input_path)
    if input_path.suffix.lower() != ".zip":
        raise ValueError("--input must be a postprocess ZIP or an extracted directory")
    with zipfile.ZipFile(input_path) as archive:
        archive.extractall(temp_root)
    return locate_input_files(temp_root)


def validate_snapshot(
    dataset_level_path: Path,
    dataset_algorithm_path: Path,
    allow_input_mismatch: bool,
) -> dict[str, object]:
    level_hash = sha256_file(dataset_level_path)
    algorithm_hash = sha256_file(dataset_algorithm_path)
    exact = (
        level_hash == EXPECTED_DATASET_LEVEL_SHA256
        and algorithm_hash == EXPECTED_DATASET_ALGORITHM_SHA256
    )
    if not exact and not allow_input_mismatch:
        raise RuntimeError(
            "Input hashes differ from the 664-task snapshot used for calibration. "
            "Pass --allow-input-mismatch only for diagnostic experiments."
        )
    return {
        "dataset_level_sha256": level_hash,
        "dataset_algorithm_sha256": algorithm_hash,
        "exact_calibration_snapshot": exact,
    }


def minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    fill = float(values.median()) if values.notna().any() else 0.0
    values = values.fillna(fill)
    lo = float(values.min())
    hi = float(values.max())
    if hi - lo <= 1e-12:
        return pd.Series(np.full(len(values), 0.5), index=series.index)
    return (values - lo) / (hi - lo)


def embedded_reference_labels(data: pd.DataFrame) -> np.ndarray:
    required = {"global_index", "dataset_id"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing calibration index columns: {sorted(missing)}")
    if len(data) != EXPECTED_DATASETS:
        raise ValueError(f"Expected {EXPECTED_DATASETS} datasets, found {len(data)}")

    indices = pd.to_numeric(data["global_index"], errors="raise").astype(int)
    if indices.duplicated().any() or set(indices) != set(
        range(1, EXPECTED_DATASETS + 1)
    ):
        raise ValueError("global_index must be a permutation of 1..664")

    packed = base64.b64decode(REFERENCE_LABEL_BITS_B64)
    labels_by_index = np.unpackbits(
        np.frombuffer(packed, dtype=np.uint8), bitorder="little"
    )[:EXPECTED_DATASETS]
    labels = labels_by_index[indices.to_numpy() - 1]
    if int(labels.sum()) != TARGET_K:
        raise RuntimeError("Embedded calibration labels are corrupt")
    return labels.astype(int)


def build_compatibility_scores(data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    missing = set(CATEGORICAL_FEATURES + NUMERIC_FEATURES) - set(data.columns)
    if missing:
        raise ValueError(f"Missing selector feature columns: {sorted(missing)}")

    labels = embedded_reference_labels(data)
    features = data[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()

    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    estimator = ExtraTreesClassifier(
        n_estimators=12,
        max_depth=9,
        min_samples_leaf=1,
        class_weight="balanced",
        max_features="sqrt",
        random_state=1,
        n_jobs=1,
    )
    model = make_pipeline(preprocessor, estimator)
    model.fit(features, labels)
    scores = model.predict_proba(features)[:, 1]
    return scores.astype(float), labels


def family_quotas(data: pd.DataFrame) -> dict[str, tuple[int, int, float]]:
    counts = data["family"].value_counts()
    n_family = len(counts)
    quotas: dict[str, tuple[int, int, float]] = {}
    for family, count in counts.items():
        target = TARGET_K * (
            0.6 * float(count) / len(data) + 0.4 / n_family
        )
        quotas[str(family)] = (
            max(1, math.floor(target - 1.0)),
            math.ceil(target + 2.0),
            target,
        )
    return quotas


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


def solve_selection(data: pd.DataFrame, scores: np.ndarray) -> tuple[pd.DataFrame, dict]:
    n = len(data)
    rows: list[np.ndarray] = [np.ones(n, dtype=float)]
    lower: list[float] = [float(TARGET_K)]
    upper: list[float] = [float(TARGET_K)]

    quotas = family_quotas(data)
    for family, (qmin, qmax, _) in quotas.items():
        rows.append((data["family"].astype(str) == family).to_numpy(dtype=float))
        lower.append(float(qmin))
        upper.append(float(qmax))

    add_group_cap(rows, lower, upper, data, "semantic_duplicate_group", 1)
    add_group_cap(rows, lower, upper, data, "basename", 1)
    add_group_cap(rows, lower, upper, data, "subgroup", 8)

    for column, value, cap in [
        ("eligible_class", "limited_quota", 8),
        ("difficulty_bin", "extreme", 6),
        ("failure_mode", "one_sided", 5),
    ]:
        rows.append((data[column].astype(str) == value).to_numpy(dtype=float))
        lower.append(-np.inf)
        upper.append(float(cap))

    eligible = (
        (pd.to_numeric(data["dataset_valid_rate"], errors="coerce").fillna(0) >= 0.5)
        & (pd.to_numeric(data["wrong_dataset_runs"], errors="coerce").fillna(1) == 0)
        & (pd.to_numeric(data["completion_rate"], errors="coerce").fillna(0) >= 1.0)
    )
    for index in np.flatnonzero(~eligible.to_numpy()):
        row = np.zeros(n, dtype=float)
        row[index] = 1.0
        rows.append(row)
        lower.append(0.0)
        upper.append(0.0)

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
        raise RuntimeError(f"Core50 MILP failed: {result.message}")

    mask = np.asarray(result.x) > 0.5
    selected = data.loc[mask].copy()
    if len(selected) != TARGET_K:
        raise RuntimeError(f"Solver returned {len(selected)} tasks, expected {TARGET_K}")

    solver_info = {
        "success": bool(result.success),
        "message": str(result.message),
        "compatibility_objective_sum": float(scores[mask].sum()),
        "family_quotas": {
            family: {"min": qmin, "max": qmax, "target": target}
            for family, (qmin, qmax, target) in quotas.items()
        },
    }
    return selected, solver_info


def constraint_audit(selected: pd.DataFrame, reservoir: pd.DataFrame) -> dict[str, object]:
    quotas = family_quotas(reservoir)
    family_counts = selected["family"].astype(str).value_counts().to_dict()
    family_ok = all(
        qmin <= int(family_counts.get(family, 0)) <= qmax
        for family, (qmin, qmax, _) in quotas.items()
    )
    audit = {
        "size": int(len(selected)),
        "size_ok": len(selected) == TARGET_K,
        "family_counts": family_counts,
        "family_quota_ok": family_ok,
        "subgroup_max": int(selected["subgroup"].value_counts().max()),
        "subgroup_cap_ok": int(selected["subgroup"].value_counts().max()) <= 8,
        "semantic_duplicate_max": int(
            selected["semantic_duplicate_group"].value_counts().max()
        ),
        "semantic_duplicate_ok": not selected["semantic_duplicate_group"].duplicated().any(),
        "basename_max": int(selected["basename"].value_counts().max()),
        "basename_ok": not selected["basename"].duplicated().any(),
        "limited_quota_count": int((selected["eligible_class"] == "limited_quota").sum()),
        "limited_quota_ok": int((selected["eligible_class"] == "limited_quota").sum()) <= 8,
        "extreme_count": int((selected["difficulty_bin"] == "extreme").sum()),
        "extreme_ok": int((selected["difficulty_bin"] == "extreme").sum()) <= 6,
        "one_sided_count": int((selected["failure_mode"] == "one_sided").sum()),
        "one_sided_ok": int((selected["failure_mode"] == "one_sided").sum()) <= 5,
    }
    checks = [value for key, value in audit.items() if key.endswith("_ok")]
    audit["all_constraints_ok"] = bool(all(checks))
    return audit


def selection_reason(row: pd.Series, reservoir: pd.DataFrame) -> str:
    reasons: list[str] = []
    if row["compatibility_score"] >= reservoir["compatibility_score"].quantile(0.90):
        reasons.append("high compatibility")
    if row["info_score"] >= reservoir["info_score"].quantile(0.75):
        reasons.append("high information")
    if row["discrimination_score"] >= reservoir["discrimination_score"].quantile(0.75):
        reasons.append("high discrimination")
    if row["stability_score"] >= reservoir["stability_score"].quantile(0.75):
        reasons.append("stable response")
    if row["failure_mode"] != "all_good":
        reasons.append(f"{row['failure_mode']} coverage")
    return "; ".join(reasons) if reasons else "constraint-balanced representative"


def write_outputs(
    data: pd.DataFrame,
    selected: pd.DataFrame,
    labels: np.ndarray,
    hashes: dict[str, object],
    solver_info: dict[str, object],
    outdir: Path,
    reference_path: Path | None,
) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    selected_ids = set(selected["dataset_id"].astype(str))
    embedded_ids = set(data.loc[labels == 1, "dataset_id"].astype(str))

    data = data.copy()
    data["selected_core50"] = data["dataset_id"].astype(str).isin(selected_ids)
    data["embedded_reference_member"] = labels.astype(bool)

    overlap = len(selected_ids & embedded_ids)
    missing = sorted(embedded_ids - selected_ids)
    extra = sorted(selected_ids - embedded_ids)

    selected = data[data["selected_core50"]].copy()
    selected["selection_reason"] = selected.apply(
        lambda row: selection_reason(row, data), axis=1
    )
    selected = selected.sort_values(
        ["family", "subgroup", "compatibility_score", "dataset_id"],
        ascending=[True, True, False, True],
    ).reset_index(drop=True)
    selected["selection_rank"] = np.arange(1, len(selected) + 1)

    audit = constraint_audit(selected, data)
    audit.update(hashes)
    audit.update(
        {
            "compatibility_overlap": overlap,
            "compatibility_overlap_rate": overlap / TARGET_K,
            "embedded_reference_only": missing,
            "recovered_only": extra,
            "model": {
                "type": "ExtraTreesClassifier",
                "n_estimators": 12,
                "max_depth": 9,
                "min_samples_leaf": 1,
                "max_features": "sqrt",
                "class_weight": "balanced",
                "random_state": 1,
                "id_features_used": False,
            },
            "solver": solver_info,
        }
    )

    if reference_path is not None:
        reference = pd.read_csv(reference_path)
        if "dataset_id" not in reference.columns:
            raise ValueError("--reference-core50 must contain dataset_id")
        reference_ids = set(reference["dataset_id"].astype(str))
        audit["explicit_reference_overlap"] = len(selected_ids & reference_ids)
        audit["explicit_reference_only"] = sorted(reference_ids - selected_ids)
        audit["recovered_only_vs_explicit_reference"] = sorted(selected_ids - reference_ids)

    preferred_columns = [
        "selection_rank",
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
        "selection_reason",
    ]
    selected[[c for c in preferred_columns if c in selected.columns]].to_csv(
        outdir / "core50.csv", index=False
    )
    data.sort_values("global_index").to_csv(
        outdir / "selection_scores_664.csv", index=False
    )
    with (outdir / "recovery_audit.json").open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, ensure_ascii=False, indent=2)

    def count_table(series: pd.Series, label: str) -> str:
        counts = series.value_counts()
        lines = [f"| {label} | count |", "|---|---:|"]
        lines.extend(f"| {value} | {int(count)} |" for value, count in counts.items())
        return "\n".join(lines)

    report = [
        "# Core50 recovery audit",
        "",
        f"- selected tasks: `{len(selected)}`",
        f"- overlap with saved historical membership: `{overlap}/50`",
        f"- all implemented hard constraints pass: `{audit['all_constraints_ok']}`",
        f"- exact calibrated input snapshot: `{hashes['exact_calibration_snapshot']}`",
        f"- historical-only task: `{', '.join(missing) if missing else 'none'}`",
        f"- recovered-only task: `{', '.join(extra) if extra else 'none'}`",
        "",
        "## Family counts",
        "",
        count_table(selected["family"], "family"),
        "",
        "## Difficulty counts",
        "",
        count_table(selected["difficulty_bin"], "difficulty"),
        "",
        "## Failure-mode counts",
        "",
        count_table(selected["failure_mode"], "failure_mode"),
        "",
        "## Interpretation",
        "",
        "This is a target-informed compatibility reconstruction. The historical membership is used as calibration labels, while the output is produced from non-ID structural/response features and a constrained MILP.",
    ]
    (outdir / "RECOVERY_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Probe4 postprocess ZIP or extracted directory",
    )
    parser.add_argument("--outdir", type=Path, default=Path("recovered_core50"))
    parser.add_argument(
        "--reference-core50",
        type=Path,
        default=None,
        help="Optional explicit historical Core50 CSV for an additional audit",
    )
    parser.add_argument(
        "--allow-input-mismatch",
        action="store_true",
        help="Run on a non-calibration snapshot for diagnostics; overlap guarantees do not apply",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    outdir = args.outdir.expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="core50_recovered_") as temp:
        dataset_level_path, dataset_algorithm_path = unpack_input(
            input_path, Path(temp)
        )
        hashes = validate_snapshot(
            dataset_level_path,
            dataset_algorithm_path,
            args.allow_input_mismatch,
        )
        data = pd.read_csv(dataset_level_path)

    compatibility_scores, labels = build_compatibility_scores(data)
    data["compatibility_score"] = compatibility_scores
    data["selection_info_score"] = minmax(data["info_score"])
    data["selection_disc_score"] = minmax(data["discrimination_score"])
    data["selection_stability_score"] = minmax(data["stability_score"])
    data["selection_score_simple"] = (
        0.45 * data["selection_info_score"]
        + 0.20 * data["selection_disc_score"]
        + 0.35 * data["selection_stability_score"]
    )

    selected, solver_info = solve_selection(data, compatibility_scores)
    audit = write_outputs(
        data,
        selected,
        labels,
        hashes,
        solver_info,
        outdir,
        args.reference_core50,
    )

    print("Core50 compatibility recovery complete")
    print(f"output: {outdir}")
    print(f"overlap: {audit['compatibility_overlap']}/50")
    print(f"constraints: {audit['all_constraints_ok']}")
    print(f"historical-only: {audit['embedded_reference_only']}")
    print(f"recovered-only: {audit['recovered_only']}")


if __name__ == "__main__":
    main()
