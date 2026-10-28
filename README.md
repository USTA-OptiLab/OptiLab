# OptiLab

A desktop app: a [pywebview](https://pywebview.flowrl.com/) shell around a Vue 3 + Tailwind frontend, backed by a Python API that does numeric work with NumPy/SciPy.

## Architecture

- **Backend** (`src/optilab/`) — `app.py` creates the pywebview window and exposes an `Api` class to the frontend as `window.pywebview.api`. Computation (stats, etc.) lives here, not in JS.
- **Frontend** (`frontend/`) — Vue 3 (`<script setup>` SFCs) + Tailwind CSS v4, built with Vite. Talks to the backend only through the pywebview JS bridge.
- **Dev vs. prod loading** — `app.py` points the webview at the Vite dev server (`http://localhost:5173`) when `OPTILAB_DEV=1` or no production build exists at `frontend/dist`; otherwise it loads the built `index.html` directly.

## Prerequisites

- Python >= 3.11
- Node.js (for the `frontend/` npm project)
- [`just`](https://github.com/casey/just) as the task runner
- Linux: system packages for the GTK webview backend — `python-gobject` and `webkit2gtk-4.1` (these are **not** pip-installable, which is why the venv is created with `--system-site-packages`)

## Quickstart

```sh
just install   # create venv (system-site-packages) + install Python/frontend deps
just dev       # run Vite dev server + pywebview app together (hot reload)
```

## Common commands

| Command | Does |
| --- | --- |
| `just install` | Create `.venv` and install Python (`.[dev]`) + frontend (`npm install`) deps |
| `just dev` | Run Vite dev server and the pywebview app together, pointed at `localhost:5173` |
| `just build` | Build the production frontend bundle into `frontend/dist` |
| `just run` | Run the app against the built frontend (run `just build` first) |
| `just test` | Run the pytest suite |
| `just lint` | `ruff check` over `src` and `tests` |
| `just format` | `ruff format` over `src` and `tests` |
| `just check` | `lint` + `test`, mirrors CI |
| `just clean` | Remove venv, caches, and build artifacts |

Run `just` with no args to list all recipes.

## Repository layout

```
src/optilab/       Python package (pywebview app + Api exposed to JS)
tests/              pytest suite
frontend/           Vue 3 + Tailwind + Vite app
justfile            task runner — source of truth for dev commands
pyproject.toml      Python package/deps config (ruff + pytest config lives here too)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions, the PR process, and code style expectations. Agent-specific instructions (Claude Code, Codex, Gemini CLI) live in [AGENTS.md](AGENTS.md).
