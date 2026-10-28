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

## Adding a new optimization method

New methods (simplex variants, transportation-problem algorithms, etc.) should follow this shape so they integrate the same way regardless of who adds them. `feat/doubolfeis-metod` is the reference example to copy:

1. **Backend package** — put the algorithm in its own subpackage, `src/optilab/<method_name>/` (snake_case), not a flat module and not a root-level script. Expose one clear entry point (e.g. `solve(problem)`) from `__init__.py`; keep internals private to the package.
2. **Wire it into `Api`** — add a method to the single `Api` class in `src/optilab/app.py` that imports your package and delegates to it. Catch the exceptions your algorithm can raise (`ValueError`, `ZeroDivisionError`, domain-specific ones) and return `{"status": "error", "message": str(exc)}` instead of letting them propagate across the `js_api` bridge — an unhandled exception there fails silently in the GTK window with no visible traceback (see "Known gotchas" below).
3. **Frontend folder** — put the method's Vue components under `frontend/src/<method-name>/` (kebab-case), and wire an entry point into `App.vue` so it's actually reachable in the UI. A method isn't done when the files exist — it's done when you can click to it in `just dev`. Only promote a component into the shared `frontend/src/components/` folder once two or more methods actually reuse it.
4. **Tests** — add `tests/test_<method_name>.py` covering the algorithm directly, not just through `Api`.
5. **New dependencies** — if the method needs a package not already in `pyproject.toml` (e.g. `pandas`, `sympy`), add it to `dependencies` there in the same PR.
6. **A CLI-only prototype isn't "added to OptiLab."** A script that reads from `input()` or otherwise never gets called from `Api` doesn't integrate with the architecture described in `README.md`. Land the pywebview/Vue wiring in the same PR, or say explicitly in the PR description that it's prototype-only and not yet integrated, so reviewers don't expect it to show up in the app.

> `feat/modi-method` predates this convention and uses a flatter layout (modules directly in `src/optilab/`, a shared `frontend/src/components/` folder for everything). It's not wrong, but don't copy it for new work — treat `doubolfeis-metod`'s per-feature layout above as canonical going forward.

## Known gotchas

- **`structuredClone()` breaks the pywebview bridge.** Don't pass a Vue `ref`/`reactive` value through `structuredClone()` before sending it to `window.pywebview.api.*` — on WebKitGTK's JavaScriptCore engine this throws `DataCloneError`, even though the object is otherwise JSON-safe. Use `JSON.parse(JSON.stringify(x))` to clone instead. The failure mode is silent: no visible console in the GTK window, just a click handler that appears to do nothing.
- **Debugging a GTK window that "does nothing"** — there's no visible devtools console in this environment. To catch bridge-level JS errors, drive the window with `webview.evaluate_js()` to install a `window.onerror` / `unhandledrejection` listener and dispatch synthetic events, rather than assuming the UI itself is broken.

## Review

PRs require approval per `.github/CODEOWNERS` (`@michaelarias25 @josephhdiazg`). Don't merge or push to `main` on their behalf.
