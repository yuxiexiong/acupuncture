#!/bin/bash
cd /workspace/acupuncture/experiments/early-state-localization-stage2-v2-2026-10-30
while [ "$(python3 -c "import json;print(json.load(open(\"runs/g_development-r01/controller.json\"))[\"status\"])")" = running ]; do sleep 20; done
s=$(python3 -c "import json;print(json.load(open(\"runs/g_development-r01/controller.json\"))[\"status\"])")
echo "dev $s $(date -u)"
[ "$s" = completed ] && [ -f runs/g_development-r01/verification.json ] || exit 1
exec /workspace/acupuncture/.venv-bench/bin/python stage2.py launch --stage g_history --authorization readiness/authorization-g_history-r01.json --output runs/g_history-r01
