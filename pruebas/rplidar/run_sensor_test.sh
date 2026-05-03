#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-/dev/ttyUSB0}"
BAUDRATE="${2:-460800}"

make -C "${SCRIPT_DIR}" rplidar_check

"${SCRIPT_DIR}/rplidar_check" \
    --serial "${PORT}" \
    --baudrate "${BAUDRATE}" \
    --frames 20 \
    --warmup-frames 3 \
    --min-points 100 \
    --min-coverage 270 \
    --max-distance 12000
