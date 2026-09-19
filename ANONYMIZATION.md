# Anonymization Notes

This artifact is a curated, reviewer-facing snapshot.

- Author names, personal email addresses, private repository URLs, local user
  names, internal host names, private IP addresses, and absolute experiment
  paths have been removed or replaced with documentation-only placeholders.
- API credentials, model weights, caches, locks, raw provider responses, and
  machine-specific orchestration logs are not part of this repository.
- Third-party source snapshots are retained where they are required to run an
  integrated algorithm. Their public citations and licenses remain applicable.
- `core-50/` contains the frozen benchmark data used by the included examples.
- `check/core50_selection/input/` contains the frozen Probe4 postprocess snapshot
  required to reproduce the recovered Core50 and nested Core60/Core70/Core80
  membership; it contains no credentials or machine-specific paths.
- Large raw trajectories are distributed separately from this code snapshot.

The anonymous reviewer URL is the only project repository URL intended for the
submission-facing documentation.
