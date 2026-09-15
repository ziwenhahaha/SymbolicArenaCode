#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/anonymous/workplace/scientific-intelligent-modelling"
REMOTE_ROOT="/home/anonymous/workplace/scientific-intelligent-modelling"
STAMP="${STAMP:-$(date +%Y%m%d-%H%M%S)}"
BATCH_NAME="${BATCH_NAME:-e1_candidate200_seed1314_w4_$STAMP}"
echo "BATCH_NAME=${BATCH_NAME}"

start_job() {
  local host="$1"
  local session="$2"
  local remote_job="$3"
  local rel_slice="$4"
  local rel_params="$5"
  local workers="$6"
  timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "mkdir -p \"$REMOTE_ROOT/check\" \"$REMOTE_ROOT/$(dirname "$rel_slice")\" \"$REMOTE_ROOT/$(dirname "$rel_params")\" \"$REMOTE_ROOT/$(dirname "$remote_job")\""
  timeout 40 scp -o BatchMode=yes -o ConnectTimeout=10 "$REPO_ROOT/check/launch_e1_benchmark.py" "$host:$REMOTE_ROOT/check/launch_e1_benchmark.py"
  timeout 40 scp -o BatchMode=yes -o ConnectTimeout=10 "$REPO_ROOT/$rel_slice" "$host:$REMOTE_ROOT/$rel_slice"
  timeout 40 scp -o BatchMode=yes -o ConnectTimeout=10 "$REPO_ROOT/$rel_params" "$host:$REMOTE_ROOT/$rel_params"
  timeout 40 scp -o BatchMode=yes -o ConnectTimeout=10 "$REPO_ROOT/$remote_job" "$host:$REMOTE_ROOT/$remote_job"
  timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "chmod +x \"$REMOTE_ROOT/$remote_job\" && tmux kill-session -t \"$session\" >/dev/null 2>&1 || true; tmux new-session -d -s \"$session\" /bin/bash \"$REMOTE_ROOT/$remote_job\" \"$BATCH_NAME\" \"$workers\""
  echo "STARTED ${host} ${session}"
}

start_job "anon-node-01" "e1_w4_dso_22" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-01.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-01.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"
start_job "anon-node-02" "e1_w4_dso_23" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-02.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-02.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"
start_job "anon-node-03" "e1_w4_dso_24" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-03.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-03.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"
start_job "anon-node-04" "e1_w4_dso_25" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-04.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-04.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"
start_job "anon-node-05" "e1_w4_dso_26" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-05.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-05.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"
start_job "anon-node-06" "e1_w4_dso_27" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-06.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-06.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"
start_job "anon-node-07" "e1_w4_dso_28" "exp-planning/02.E1选择验证/generated/remote_jobs/W4/dso_anon-node-07.sh" "exp-planning/02.E1选择验证/generated/slices/W4/dso/anon-node-07.csv" "exp-planning/02.E1选择验证/generated/params/dso.json" "15"

echo "WAVE_DONE W4"
