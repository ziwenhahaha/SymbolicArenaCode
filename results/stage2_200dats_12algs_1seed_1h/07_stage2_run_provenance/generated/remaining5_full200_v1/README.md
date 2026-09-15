# E1 remaining5 full Candidate-200 assets

- source: `exp-planning/02.E1选择验证/generated/candidate200_unified.csv`
- seed: `1314`
- workers per host: `50`
- scope: remaining integrated algorithms without prior full Candidate-200 E1 run

## Allocation

| tool | host | env | tasks |
|---|---:|---|---:|
| `e2esr` | `anon-node-03` | `sim_e2esr` | `200` |
| `iMCTS` | `anon-node-04` | `sim_iMCTS` | `200` |
| `QLattice` | `anon-node-05` | `sim_qLattice` | `200` |
| `ragsr` | `anon-node-06` | `sim_ragsr` | `200` |
| `udsr` | `anon-node-07` | `sim_dso` | `200` |
