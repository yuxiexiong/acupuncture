#!/bin/bash
# Pre-freeze limited checks (D18, D19, D20) for several models on one GPU, sequentially.
# Usage: launch_checks.sh <cuda:N> <model_key>...
set -u
DEV=$1; shift
LOG=runs/f1-checks
mkdir -p "$LOG"
run() {
  local tag=$1; shift
  echo "[$(date -u +%FT%TZ)] START $tag"
  python "$@" > "$LOG/$tag.log" 2>&1
  local rc=$?
  echo "[$(date -u +%FT%TZ)] EXIT $tag $rc"
}
for m in "$@"; do
  S=runs/f1-scales/$m/scales.json
  run "$m.d18" calibrate.py "$m" "$S" "runs/f1-d18/$m" "$DEV" 3/8
  run "$m.d19_38" path_check2.py "$m" "$S" 3/8 "runs/f1-d19/dose-3_8/$m" "$DEV"
  run "$m.d19_34" path_check2.py "$m" "$S" 3/4 "runs/f1-d19/dose-3_4/$m" "$DEV"
  run "$m.d20b" calib_b.py "$m" "$S" 3/4 "runs/f1-calib-b-r2/$m" "$DEV"
done
echo "[$(date -u +%FT%TZ)] ALL_DONE $DEV"
