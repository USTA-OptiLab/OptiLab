venv := ".venv"
python := venv + "/bin/python"
pip := venv + "/bin/pip"
ruff := venv + "/bin/ruff"

default:
    @just --list

# Create the venv (if needed) and install Python + frontend dependencies
install: install-python install-frontend

# --system-site-packages lets pywebview see the system GTK/WebKit bindings
# (python-gobject + webkit2gtk-4.1), which aren't practical to pip-install
install-python:
    [ -d {{venv}} ] || python3 -m venv --system-site-packages {{venv}}
    {{pip}} install -e ".[dev]"

install-frontend:
    cd frontend && npm install

# Run the Vite dev server and the pywebview app together
dev:
    #!/usr/bin/env bash
    set -euo pipefail -m
    # `exec` replaces the subshell with npm itself, and `-m` gives that
    # background job its own process group, so `kill -- -$vite_pid` below
    # reaps npm's node/esbuild children too — otherwise they survive as
    # orphans holding the terminal's stdout open and the shell never returns.
    (cd frontend && exec npm run dev) &
    vite_pid=$!
    trap 'kill -TERM -- -$vite_pid 2>/dev/null' EXIT
    sleep 1
    OPTILAB_DEV=1 {{python}} -m optilab.app

# Build the frontend for production
build:
    cd frontend && npm run build

# Run the app against the built frontend (run `just build` first)
run:
    {{python}} -m optilab.app

test:
    {{python}} -m pytest

lint:
    {{ruff}} check src tests

format:
    {{ruff}} format src tests

# Lint + test, mirroring CI
check: lint test

clean:
    rm -rf {{venv}} .pytest_cache .ruff_cache frontend/dist frontend/node_modules
    find . -type d -name __pycache__ -not -path "./frontend/*" -exec rm -rf {} +
