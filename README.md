# SymbolicArena

SymbolicArena provides a unified interface for symbolic regression, isolated
algorithm environments, a standardized evaluation pipeline, the Core-50
benchmark datasets, and the archived experimental evidence used in the paper.
This snapshot includes the current 15-algorithm implementation and the revised
Core-50 six-axis evaluation code for clean, 1% noise, and 5% noise conditions.

The artifact supports `gplearn`, `pysr`, `fepysr`, `jaxsr`, `symbolfit`,
`pyoperon`, `ragsr`, `llmsr`, `dso`, `udsr`, `tpsr`, `e2esr`, `QLattice`,
`iMCTS`, and `drsr`.

Git and Conda are required. Unless stated otherwise, run all commands below on
Linux from the repository root.

## Table of Contents

- [Repository Structure](#repository-structure)
- [1. Access the Anonymous Repository](#1-access-the-anonymous-repository)
- [2. Installation](#2-installation)
  - [Step 1: Install the Controller Environment](#step-1-install-the-controller-environment)
  - [Step 2: Install an Algorithm Environment](#step-2-install-an-algorithm-environment)
- [3. Run a Dataset or the Full Benchmark](#3-run-a-dataset-or-the-full-benchmark)
  - [3.1 Run One Core-50 Dataset](#31-run-one-core-50-dataset)
  - [3.2 Run the Full Core-50 Benchmark](#32-run-the-full-core-50-benchmark)
- [4. Basic Usage](#4-basic-usage)
  - [4.1 Python API](#41-python-api)
  - [4.2 CSV and NumPy Inputs](#42-csv-and-numpy-inputs)
  - [4.3 Smoke Checks](#43-smoke-checks)
- [5. Integrate a New Symbolic Regression Algorithm](#5-integrate-a-new-symbolic-regression-algorithm)
  - [5.1 Create a Wrapper](#51-create-a-wrapper)
  - [5.2 Register the Algorithm](#52-register-the-algorithm)
  - [5.3 Register the Runtime Environment](#53-register-the-runtime-environment)
  - [5.4 Add a Smoke Check](#54-add-a-smoke-check)
  - [5.5 Validate the Integration](#55-validate-the-integration)

## Repository Structure

```text
SymbolicArenaCode/
|-- core-50/                         # Standardized Core-50 datasets
|-- results/                         # Archived experimental artifacts
|   |-- stage1_664dats_2probes_1seed_1h/
|   |-- stage2_200dats_12algs_1seed_1h/
|   |-- stage3_664dats_4probes_3seeds_1h/
|   |-- stage4_core50_12algs_5seeds_4noise_1h/
|   |-- stage4_core50_15algs_3seeds_3conditions_3h/
|   `-- gpt56_opus_simplification_audit_20260915/
|-- evaluation/
|   `-- core50_final_20260914/code/ # Frozen metric and publication pipeline
|-- scientific_intelligent_modelling/
|   |-- algorithms/                  # Symbolic regression wrappers
|   |   |-- base_wrapper.py          # Shared wrapper interface
|   |   |-- drsr_wrapper/
|   |   |-- dso_wrapper/
|   |   |-- e2esr_wrapper/
|   |   |-- fepysr_wrapper/
|   |   |-- gplearn_wrapper/
|   |   |-- iMCTS_wrapper/
|   |   |-- jaxsr_wrapper/
|   |   |-- llmsr_wrapper/
|   |   |-- pyoperon_wrapper/
|   |   |-- pysr_wrapper/
|   |   |-- QLattice_wrapper/
|   |   |-- ragsr_wrapper/
|   |   |-- symbolfit_wrapper/
|   |   |-- tpsr_wrapper/
|   |   `-- udsr_wrapper/
|   |-- benchmarks/                  # Benchmark execution utilities
|   |-- config/                      # Algorithm and runtime configuration
|   |-- pipelines/                   # Evaluation pipelines
|   `-- srkit/                       # Shared interfaces and CLI support
|-- check/                           # Integration and smoke checks
|-- core-50_datasets.csv             # Core-50 dataset manifest
|-- environment.yml                  # Controller Conda environment
|-- pyproject.toml                   # Python package definition
|-- LICENSE
`-- THIRD_PARTY_NOTICES.md
```

For a minimal reviewer-oriented reproduction, follow Section 2, Section 3.1,
and Section 4.3 in that order. Section 3.2 launches the complete Core-50
benchmark. The archived paper experiments are available under `results/`.

### Current Core-50 Release

The current evaluation uses 15 algorithms, 50 tasks, seeds 520--522, and three
conditions (`clean`, `noise001`, and `noise005`). Compact final run tables,
six-axis scores, task-level stability evidence, and 180-minute aggregate curves
are available under:

```text
results/stage4_core50_15algs_3seeds_3conditions_3h/
```

The corresponding frozen implementation is under
`evaluation/core50_final_20260914/code/`. Raw API responses, credentials,
machine-specific launch logs, model weights, and large per-minute trajectory
archives are intentionally excluded from this code repository.

The supplementary GPT-5.6-Sol audit of all 6,800 Opus5 simplification records
is summarized under `results/gpt56_opus_simplification_audit_20260915/`.

## 1. Access the Anonymous Repository

Reviewers can browse the anonymized artifact at:

<https://anonymous.4open.science/r/SymbolicArenaCode-A3C0/>

The anonymous mirror is a read-only browser and ZIP distribution endpoint, not
a Git remote, so it cannot be used with `git clone`. Download and extract the
complete repository instead:

```bash
curl -L \
  https://anonymous.4open.science/api/repo/SymbolicArenaCode-A3C0/zip \
  -o SymbolicArenaCode.zip
unzip SymbolicArenaCode.zip -d SymbolicArenaCode
cd SymbolicArenaCode
```

The `core-50/` directory contains the 50 standardized datasets.
`core-50_datasets.csv` records their paths, source families, target columns,
feature counts, and split sizes.

## 2. Installation

Installation has two explicit steps. First install the lightweight controller
environment, then install only the isolated environment required by the
algorithm to be evaluated.

### Step 1: Install the Controller Environment

```bash
conda env create -f environment.yml
conda activate sim
python -m pip install -e .
sim-cli --help
```

Step 1 is complete when `sim-cli --help` prints the command-line help. The
controller environment intentionally does not include every algorithm
dependency or model weight.

### Step 2: Install an Algorithm Environment

Keep the current working directory at the repository root while creating an
environment because the environment recipe installs this package in editable
mode.

For example, `gplearn`, `pysr`, and `pyoperon` share `sim_base`:

```bash
conda activate sim
python - <<'PY'
from scientific_intelligent_modelling.srkit.conda_env_manager import env_manager

if not env_manager.create_environment("sim_base"):
    raise SystemExit("Failed to create sim_base")
PY
```

The algorithm-to-environment mapping is:

| Algorithm | Conda environment |
| --- | --- |
| `gplearn`, `pysr`, `pyoperon` | `sim_base` |
| `fepysr` | `sim_fepysr` |
| `jaxsr` | `sim_jaxsr` |
| `symbolfit` | `sim_symbolfit` |
| `dso`, `udsr` | `sim_dso` |
| `llmsr`, `drsr` | `sim_llm` |
| `ragsr` | `sim_ragsr` |
| `tpsr` | `sim_tpsr` |
| `e2esr` | `sim_e2esr` |
| `QLattice` | `sim_qLattice` |
| `iMCTS` | `sim_iMCTS` |

Some algorithms download model weights or external assets when their dedicated
environment is prepared or when they are first used. API-backed algorithms
also require provider credentials supplied through environment variables.
Credentials and machine-specific model paths must not be committed.

## 3. Run a Dataset or the Full Benchmark

### 3.1 Run One Core-50 Dataset

Each Core-50 directory contains `metadata.yaml`, `formula.py`, and the
standardized train, validation, ID-test, and OOD-test splits.

```bash
conda activate sim
sim-cli \
  --algorithm gplearn \
  --train-path core-50/keijzer/Keijzer-11 \
  --seed 42 \
  --output-root benchmark_outputs/core50_single
```

When `--train-path` points to a standardized dataset directory, `sim-cli`
automatically uses the benchmark runner and writes a structured `result.json`.
Replace `gplearn` with another registered algorithm after installing its
environment.

### 3.2 Run the Full Core-50 Benchmark

The generic launcher reads the 50-row dataset manifest and runs a fixed local
worker pool. Create a JSON file containing the algorithm parameters first:

```bash
mkdir -p benchmark_outputs
printf '%s\n' '{}' > benchmark_outputs/gplearn_params.json

python check/launch_e1_benchmark.py run \
  --tool gplearn \
  --slice-csv core-50_datasets.csv \
  --params-json benchmark_outputs/gplearn_params.json \
  --output-root benchmark_outputs/core50_gplearn_seed42 \
  --seed 42 \
  --workers 4
```

Adjust `--workers` to the available CPU and memory capacity. To evaluate
another algorithm, install its environment, change `--tool`, and provide its
parameter JSON. Launcher state and per-task logs are stored under
`<output-root>/__launcher__/`.

## 4. Basic Usage

### 4.1 Python API

```python
import numpy as np

from scientific_intelligent_modelling.srkit.regressor import SymbolicRegressor

rng = np.random.RandomState(0)
X = rng.rand(100, 2)
y = X[:, 0] ** 2 + X[:, 1]

regressor = SymbolicRegressor(
    "gplearn",
    problem_name="api_example",
    seed=42,
    population_size=500,
    generations=10,
)
regressor.fit(X, y)

print(regressor.get_optimal_equation())
print(regressor.get_total_equations()[:3])
print(regressor.predict(X[:5]))
```

Algorithm-specific parameters are passed as keyword arguments to
`SymbolicRegressor` and forwarded to the selected wrapper.

### 4.2 CSV and NumPy Inputs

For a CSV file, the CLI treats the last column as the target by default:

```bash
sim-cli \
  --algorithm gplearn \
  --train-path /path/to/train.csv \
  --dataset-name csv_example \
  --seed 42
```

The same entry point supports `.npy`, `.npz` containing `arr_0`, delimited text
files, and standardized dataset directories. Unknown `--key value` options are
normalized to underscore-separated wrapper parameters.

### 4.3 Smoke Checks

Run the check for the selected algorithm before starting a benchmark:

```bash
python check/check_gplearn.py
python check/check_pysr.py
python check/check_dso.py
```

Checks for the remaining algorithms follow the same naming convention.
Model-based or API-backed checks require their corresponding environment,
weights, or credentials.

## 5. Integrate a New Symbolic Regression Algorithm

An integration consists of a wrapper, a toolbox registration, a runtime
environment registration, and a focused smoke check.

### 5.1 Create a Wrapper

Create:

```text
scientific_intelligent_modelling/algorithms/mytool_wrapper/
|-- __init__.py
`-- wrapper.py
```

The wrapper should inherit `BaseWrapper`, validate the explicit dataset
contract, and implement the unified methods:

```python
from scientific_intelligent_modelling.algorithms.base_wrapper import BaseWrapper


class MyToolRegressor(BaseWrapper):
    def __init__(self, **kwargs):
        self.params = kwargs
        self.model = None

    def fit(self, X, y):
        self._validate_explicit_dataset_contract(
            X,
            n_features=self.params.pop("n_features", None),
            feature_names=self.params.pop("feature_names", None),
            target_name=self.params.pop("target_name", None),
            context=self.__class__.__name__,
        )
        return self

    def predict(self, X):
        raise NotImplementedError

    def get_optimal_equation(self):
        raise NotImplementedError

    def get_total_equations(self):
        raise NotImplementedError
```

Import heavy upstream dependencies inside the methods that use them. This
keeps wrapper discovery functional in the controller environment.

### 5.2 Register the Algorithm

Add the tool mapping to
`scientific_intelligent_modelling/config/toolbox_config.json`:

```json
{
  "mytool": {
    "env": "sim_mytool",
    "regressor": "MyToolRegressor"
  }
}
```

The tool name, wrapper module name, and class name must agree exactly.

### 5.3 Register the Runtime Environment

Add `sim_mytool` to
`scientific_intelligent_modelling/config/envs_config.json`. Declare the Python
version, package dependencies, and any repository-local installation command.
Create a dedicated environment when the upstream dependency set conflicts with
an existing environment.

Model weights and API credentials are runtime assets. Do not place them in the
repository; document how the dedicated environment downloads or locates them.

### 5.4 Add a Smoke Check

Create `check/check_mytool.py` with a small deterministic dataset. At minimum,
exercise:

```text
fit
get_optimal_equation
get_total_equations
predict, when supported
```

The smoke check should fail clearly when a required runtime asset is missing.

### 5.5 Validate the Integration

From the repository root:

```bash
python -c \
  "from scientific_intelligent_modelling.algorithms.mytool_wrapper.wrapper import MyToolRegressor"
python check/check_mytool.py
```

Then run one Core-50 dataset through `sim-cli` and confirm that the output
contains a valid equation, structured metrics, and `result.json`.
