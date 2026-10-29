#!/bin/bash
# Mechanical continuation (user pre-approved 2026-10-30): every step requires the previous verification to pass.
set -e
cd /workspace/acupuncture/experiments/early-state-localization-stage2-v2-2026-10-30
P=/workspace/acupuncture/.venv-bench/bin/python; A=/workspace/stage2-ops/make_auth.py
status() { python3 -c "import json;print(json.load(open(\"runs/$1/controller.json\"))[\"status\"])"; }
wait_run() { while [ "$(status $1)" = running ]; do sleep 20; done; if [ "$(status $1)" != completed ] || [ ! -f runs/$1/verification.json ]; then echo "STOP: $1 $(status $1) $(date -u)"; exit 1; fi; echo "$1 completed $(date -u)"; }
launch() { $P stage2.py launch --stage $1 --authorization readiness/authorization-$1-r01.json --output runs/$1-r01 > /workspace/stage2-ops/$1-r01.launch.log 2>&1; wait_run $1-r01; }
BASE="items_lock_path=readiness/items-lock-r01.json g_lock_path=readiness/g-lock-r01.json g_development_verification_path=runs/g_development-r01/verification.json"
until [ -f runs/g_history-r01/controller.json ]; do sleep 10; done
wait_run g_history-r01
$P analyze_stage2.py g runs/g_history-r01 analysis/g_history-r01.json
$P $A . a_preflight $BASE g_development_run=runs/g_development-r01
launch a_preflight
$P $A . a_scan $BASE g_development_run=runs/g_development-r01 a_preflight_verification_path=runs/a_preflight-r01/verification.json
launch a_scan
$P analyze_stage2.py a runs/g_development-r01 runs/a_scan-r01 readiness/g-lock-r01.json analysis/a_scan-r01.json
$P analyze_stage2.py lock-a analysis/a_scan-r01.json readiness/g-lock-r01.json readiness/a-lock-r01.json
$P $A . b_preflight $BASE a_lock_path=readiness/a-lock-r01.json
launch b_preflight
$P $A . b_validate $BASE a_lock_path=readiness/a-lock-r01.json b_preflight_verification_path=runs/b_preflight-r01/verification.json
launch b_validate
$P analyze_stage2.py b runs/b_validate-r01 readiness/a-lock-r01.json analysis/b_validate-r01.json
echo "ALL DONE $(date -u)"
