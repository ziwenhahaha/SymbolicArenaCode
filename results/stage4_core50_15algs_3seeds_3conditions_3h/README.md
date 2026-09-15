# Core-50 15-Algorithm Compact Results

This directory contains the compact reviewer-facing summary of the current
Core-50 experiment:

- 15 algorithms;
- 50 datasets;
- seeds 520, 521, and 522;
- `clean`, `noise001`, and `noise005` conditions;
- three-hour search budget per run.

For each condition, the repository includes:

- `run_final.csv`: 2,250 run-level final metric records;
- `six_axis.csv`: 15 algorithm-level six-axis scores;
- `task_stability.csv`: 750 algorithm-task stability records;
- `curves_2700.csv`: 15 algorithms by 180 minute-level aggregate curves;
- `run_eff_status.csv`: 2,250 run-level EFF availability records.

`ground_truth/current_references.csv`, `provenance/datasets.csv`,
`FINAL_STATUS.json`, and `PUBLICATION_REPORT.json` provide the compact release
contract. `README_FULL_RELEASE.md` documents the separately distributed full
artifact; files named there but absent here are intentionally excluded rather
than missing from this compact code repository.
