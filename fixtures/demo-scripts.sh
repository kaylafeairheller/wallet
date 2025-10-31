#!/bin/bash

# Get the fixtures directory (where this script lives)
# Handle both bash and zsh
if [ -n "${BASH_SOURCE[0]}" ]; then
    script_path="${BASH_SOURCE[0]}"
elif [ -n "${(%):-%x}" ]; then
    script_path="${(%):-%x}"
else
    script_path="$0"
fi

fixtures_dir=$( cd -- "$( dirname -- "$script_path" )" &> /dev/null && pwd )

# Get the wallet directory (parent of fixtures)
if [[ "$(basename "$fixtures_dir")" == "fixtures" ]]; then
    # Script is in fixtures subdirectory, wallet is parent
    wallet_dir="$(dirname "$fixtures_dir")"
else
    # Script might be in wallet directory already
    wallet_dir="$fixtures_dir"
fi

export KERI_DEMO_SCRIPT_DIR="${fixtures_dir}"
export KERI_SCRIPT_DIR="${wallet_dir}"
export KERI_TEMP_DIR="scripts_tmp"