#!/usr/bin/env bash

set -euo pipefail

if [[ ! -f /usr/bin/pipx ]]; then
    sudo apt-get update
    sudo apt-get install --yes pipx
fi

if [[ ! -d "$HOME/.local/pipx/venvs/pyinfra" ]]; then
    pipx install pyinfra
fi

"$HOME/.local/bin/pyinfra" @local deploy.py
