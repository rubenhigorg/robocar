#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="${SCRIPT_DIR}/rplidar_sdk"
BUILD_DIR="${SDK_DIR}/output/Linux/Release"
PORT="${1:-/dev/ttyUSB0}"

if [[ ! -d "${SDK_DIR}" ]]; then
    echo "No se ha encontrado el SDK en: ${SDK_DIR}"
    echo "Ejecuta primero ./build_sdk.sh después de clonar el SDK."
    exit 1
fi

if [[ ! -e "${PORT}" ]]; then
    echo "El puerto ${PORT} no existe."
    echo "Puertos serie detectados:"
    ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
    exit 1
fi

BAUDRATE="${2:-460800}"

if [[ -x "${BUILD_DIR}/ultra_simple" ]]; then
    BIN="${BUILD_DIR}/ultra_simple"
elif [[ -x "${BUILD_DIR}/simple_grabber" ]]; then
    BIN="${BUILD_DIR}/simple_grabber"
else
    echo "No se han encontrado binarios compilados en ${BUILD_DIR}"
    echo "Ejecuta primero ./build_sdk.sh"
    exit 1
fi

echo "Usando binario: ${BIN}"
echo "Usando puerto: ${PORT}"
echo "Usando baudrate: ${BAUDRATE}"
echo

"${BIN}" --channel --serial "${PORT}" "${BAUDRATE}"
