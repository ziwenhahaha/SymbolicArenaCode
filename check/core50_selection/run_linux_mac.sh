#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
python3 core50_60_70_80_selector.py \
  --input input/postprocess_final_20260501-105508_664+4+3result.zip \
  --outdir outputs_reproduced

echo "完成：结果位于 outputs_reproduced/"
