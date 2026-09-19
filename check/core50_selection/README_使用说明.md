# SymbolicArena Core50 / Core60 / Core70 / Core80 完整复现包

这个压缩包已经包含运行所需的脚本、输入数据、Python 依赖清单、四个结果 CSV 和审计结果。

## 文件结构

```text
SymbolicArena_Core50_60_70_80_complete/
├── core50_selector_recovered.py          # 只生成历史兼容 Core50
├── core50_60_70_80_selector.py           # 生成严格嵌套的 50/60/70/80
├── requirements.txt                      # Python 依赖
├── run_linux_mac.sh                      # Linux/macOS 一键运行
├── run_windows.bat                       # Windows 一键运行
├── input/
│   └── postprocess_final_20260501-105508_664+4+3result.zip
└── outputs/
    ├── core50.csv
    ├── core60.csv
    ├── core70.csv
    ├── core80.csv
    ├── selection_scores_664_nested.csv
    ├── nested_selection_audit.json
    └── NESTED_SELECTION_REPORT.md
```

## 环境要求

- Python 3.10 或更高版本
- 依赖：NumPy、pandas、SciPy、scikit-learn

安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 生成 Core50 / Core60 / Core70 / Core80

在解压后的根目录运行：

```bash
python core50_60_70_80_selector.py \
  --input input/postprocess_final_20260501-105508_664+4+3result.zip \
  --outdir outputs_reproduced
```

运行完成后，`outputs_reproduced/` 中会生成：

- `core50.csv`
- `core60.csv`
- `core70.csv`
- `core80.csv`
- `selection_scores_664_nested.csv`
- `nested_selection_audit.json`
- `NESTED_SELECTION_REPORT.md`

嵌套关系固定为：

```text
Core50 ⊂ Core60 ⊂ Core70 ⊂ Core80
```

每一级保留前一级全部成员，并新增 10 个任务。

## 只生成 Core50

```bash
python core50_selector_recovered.py \
  --input input/postprocess_final_20260501-105508_664+4+3result.zip \
  --outdir core50_reproduced
```

这会输出 `core50.csv`、664 项评分表、审计 JSON 和恢复报告。

## 一键运行

Linux 或 macOS：

```bash
chmod +x run_linux_mac.sh
./run_linux_mac.sh
```

Windows：双击 `run_windows.bat`，或在命令提示符中运行：

```bat
run_windows.bat
```

## CSV 字段

- `in_previous_core=true`：已经属于上一层集合。
- `new_at_size=true`：本层新增任务。
- `compatibility_score`：恢复模型给出的 Core50 兼容分。
- `selection_score_simple`：信息量、区分度和稳定性的组合分。

`selection_scores_664_nested.csv` 包含全部 664 个任务，并提供 `selected_core50`、`selected_core60`、`selected_core70`、`selected_core80` 和 `first_core_size`。

## 已完成验证

- Core50 与恢复的历史成员完全一致：50/50。
- 四个集合严格嵌套。
- family 配额、重复限制、有效性限制和规模化覆盖上限全部通过。
- 独立运行两次，输出文件逐项一致。
- 对最终压缩包进行了解压复跑，结果与随包 CSV 一致。
