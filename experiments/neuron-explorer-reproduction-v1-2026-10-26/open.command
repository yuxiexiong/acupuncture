#!/usr/bin/env bash
set -euo pipefail
socket=/tmp/acupuncture-neuron-explorer-8791.sock
if ! ssh -S "$socket" -O check gqa-h20 >/dev/null 2>&1; then
    ssh -fNT -M -S "$socket" -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 -L 127.0.0.1:8791:127.0.0.1:8791 gqa-h20
fi
open 'http://127.0.0.1:8791/#L14/N8949'
