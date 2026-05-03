#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="${SCRIPT_DIR}/rplidar_sdk"

if [[ ! -d "${SDK_DIR}" ]]; then
    echo "No se ha encontrado el SDK en: ${SDK_DIR}"
    echo "Clónalo aquí antes de compilar:"
    echo "  git clone https://github.com/Slamtec/rplidar_sdk.git ${SDK_DIR}"
    exit 1
fi

echo "Compilando SDK en ${SDK_DIR}"
make -C "${SDK_DIR}"

echo
echo "Build completada. Binarios esperados:"
echo "  ${SDK_DIR}/output/Linux/Release/simple_grabber"
echo "  ${SDK_DIR}/output/Linux/Release/ultra_simple"
