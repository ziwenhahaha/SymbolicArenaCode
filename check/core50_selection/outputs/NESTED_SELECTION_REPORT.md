# Nested Core50 / Core60 / Core70 / Core80 audit

- nested chain: `True`
- Core50 historical overlap: `50/50`
- all implemented constraints pass: `True`

| subset | size | new items | contains previous | constraints |
|---|---:|---:|---:|---:|
| Core50 | 50 | 50 | True | True |
| Core60 | 60 | 10 | True | True |
| Core70 | 70 | 10 | True | True |
| Core80 | 80 | 10 | True | True |

Each extension maximizes the recovered Core50 compatibility score while fixing every member of the preceding subset. Family quotas and coverage caps scale with subset size; semantic-duplicate and basename caps remain one.
