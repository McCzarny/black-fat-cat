#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
pushd "$SCRIPT_DIR" || exit 1
conda activate numpy-dev;
python3 ./main.py
popd || exit 1
