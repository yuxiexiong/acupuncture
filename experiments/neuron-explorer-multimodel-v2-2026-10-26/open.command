#!/usr/bin/env bash
set -euo pipefail
socket=/tmp/acupuncture-neuron-explorer-multi.sock
if ! ssh -S "$socket" -O check gqa-h20 >/dev/null 2>&1; then
    if ssh -S /tmp/acupuncture-neuron-explorer-8791.sock -O check gqa-h20 >/dev/null 2>&1; then
        socket=/tmp/acupuncture-neuron-explorer-8791.sock
    else
        ssh -fNT -M -S "$socket" -o ServerAliveInterval=30 -o ServerAliveCountMax=3 gqa-h20
    fi
fi
ssh -S "$socket" -O forward -L 127.0.0.1:8792:127.0.0.1:8792 \
    -L 127.0.0.1:8794:127.0.0.1:8794 -L 127.0.0.1:8799:127.0.0.1:8799 gqa-h20
open 'http://127.0.0.1:8794/'
