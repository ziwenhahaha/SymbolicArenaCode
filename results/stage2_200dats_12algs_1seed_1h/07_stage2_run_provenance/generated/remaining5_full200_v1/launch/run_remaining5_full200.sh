#!/usr/bin/env bash
set -euo pipefail

BATCH_NAME="${1:-e1_remaining5_full200_v1_$(date +%Y%m%d-%H%M%S)}"
WORKERS="${2:-50}"
REMOTE_ROOT="/home/anonymous/projects/scientific-intelligent-modelling"

echo "BATCH_NAME=${BATCH_NAME}"
echo "WORKERS=${WORKERS}"

echo "[start] e2esr on anon-node-03 workers=${WORKERS}"
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 -J hub anonymous@192.0.2.1 'tmux new-session -d -s e1_remaining5_e2esr_24 /bin/bash /home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/bootstrap_env_and_run.sh "'"'sim_e2esr"'"' "'"'/home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/e2esr_anon-node-03.sh"'"' "'"'${BATCH_NAME}'"'"' "'"'${WORKERS}'"'"' retry'

echo "[start] iMCTS on anon-node-04 workers=${WORKERS}"
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 -J hub anonymous@192.0.2.1 'tmux new-session -d -s e1_remaining5_imcts_25 /bin/bash /home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/bootstrap_env_and_run.sh "'"'sim_iMCTS"'"' "'"'/home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/imcts_anon-node-04.sh"'"' "'"'${BATCH_NAME}'"'"' "'"'${WORKERS}'"'"' retry'

echo "[start] QLattice on anon-node-05 workers=${WORKERS}"
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 -J hub anonymous@192.0.2.1 'tmux new-session -d -s e1_remaining5_qlattice_26 /bin/bash /home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/bootstrap_env_and_run.sh "'"'sim_qLattice"'"' "'"'/home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/qlattice_anon-node-05.sh"'"' "'"'${BATCH_NAME}'"'"' "'"'${WORKERS}'"'"' retry'

echo "[start] ragsr on anon-node-06 workers=${WORKERS}"
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 -J hub anonymous@192.0.2.1 'tmux new-session -d -s e1_remaining5_ragsr_27 /bin/bash /home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/bootstrap_env_and_run.sh "'"'sim_ragsr"'"' "'"'/home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/ragsr_anon-node-06.sh"'"' "'"'${BATCH_NAME}'"'"' "'"'${WORKERS}'"'"' retry'

echo "[start] udsr on anon-node-07 workers=${WORKERS}"
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 -J hub anonymous@192.0.2.1 'tmux new-session -d -s e1_remaining5_udsr_28 /bin/bash /home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/bootstrap_env_and_run.sh "'"'sim_dso"'"' "'"'/home/anonymous/projects/scientific-intelligent-modelling/exp-planning/02.E1选择验证/generated/remaining5_full200_v1/remote_jobs/udsr_anon-node-07.sh"'"' "'"'${BATCH_NAME}'"'"' "'"'${WORKERS}'"'"' retry'

