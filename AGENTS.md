# Agent instructions — OptiLab

Canonical instructions for any coding agent (Claude Code, Codex CLI, Gemini CLI, etc.) working in this repo. `CLAUDE.md` and `GEMINI.md` point here.

## What this is

A desktop app: pywebview shell + Vue 3/Tailwind frontend, Python backend doing numeric work (NumPy/SciPy) exposed to JS via a `js_api` object. See `README.md` for architecture detail.

## Toolchain — use `just`, not raw commands

This repo is orchestrated through a `justfile`. Always prefer the recipe over reinventing the raw command, so behavior stays consistent with CI and with other contributors:

- `just install` — create `.venv` (with `--system-site-packages`, required for GTK/WebKit bindings) + install Python/frontend deps
- `just dev` — Vite dev server + pywebview app together
- `just build` — build frontend to `frontend/dist`
- `just run` — run app against the built frontend
- `just test` — `pytest`
- `just lint` — `ruff check src tests`
- `just format` — `ruff format src tests`
- `just check` — lint + test (what CI expects to pass, modulo commitlint)
- `just clean` — wipe venv/caches/build output

Run `just --list` if unsure what's available — don't assume a recipe exists without checking.

## Before finishing any change

1. If you touched `src/` or `tests/`: run `just format` then `just check`.
2. If you touched `frontend/`: there is no lint/test script configured yet (see `frontend/package.json`) — don't invent one unless asked. If the app has a visible/runtime effect, use the `run` skill or manually drive `just dev` to confirm it works rather than relying on types alone.
3. Don't touch `frontend/dist/`, `.venv/`, `__pycache__/`, `*.egg-info/` — all gitignored, all generated.

## Commit messages

This repo enforces [Conventional Commits](https://www.conventionalcommits.org/) via `commitlint` in CI (`.github/workflows/lint.yml`). Every commit you author must match `<type>(<scope>): <subject>` (e.g. `fix(app): handle empty array in describe()`). A PR with a non-conforming commit message will fail CI.

## CI reality check

`.github/workflows/lint.yml` currently only runs:
- `commitlint` on the PR's commits
- `ruff check` on changed `*.py` files

It does **not** run `pytest` or any frontend checks in CI yet. That means passing CI is not sufficient — run `just check` yourself before calling a Python change done, since CI won't catch a broken test for you.

## Code style

- **Python**: ruff-formatted/linted (config in `pyproject.toml`). Keep the `Api` class in `app.py` as the single bridge surface between frontend and Python compute logic — don't scatter pywebview-exposed methods elsewhere without a reason.
- **Frontend**: Vue 3 `<script setup>`, Tailwind v4 utility classes applied inline (no CSS modules / scoped `<style>` blocks in the current code — match `App.vue`'s approach unless there's a good reason to diverge).
- Keep changes minimal and consistent with the existing small-app scope — don't add build tooling, abstractions, or dependencies the task doesn't need.

## Review

PRs require approval per `.github/CODEOWNERS` (`@michaelarias25 @josephhdiazg`). Don't merge or push to `main` on their behalf.
