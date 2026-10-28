# Contributing to OptiLab

## Setup

```sh
just install
just dev
```

See [README.md](README.md) for prerequisites and the full command reference.

## Before opening a PR

Run the same checks CI runs:

```sh
just check   # ruff check + pytest
```

If you touched `src/` or `tests/`, also run `just format` (`ruff format`) so formatting matches CI's `ruff check`.

There is no frontend lint/test command configured yet. If you add one (ESLint, Vitest, etc.), wire it into the `justfile` and the `lint.yml` workflow in the same PR.

## Commit messages

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/) — this is enforced by `commitlint` in CI (`.github/workflows/lint.yml`), using the shared `@commitlint/config-conventional` rules (see `commitlint.config.js`).

Format:

```
<type>(<optional scope>): <subject>
```

Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `build`, `perf`.

Examples:

```
feat(frontend): add histogram view for describe() output
fix(app): handle empty input array in Api.describe
chore: bump vite to 8.3.5
```

Keep the subject imperative and lowercase after the type; avoid a trailing period.

## Pull requests

- Keep PRs focused — one logical change per PR.
- CI runs on every PR (`.github/workflows/lint.yml`):
  - `commitlint` — validates every commit message in the PR.
  - `python-lint` — runs `ruff check` against changed `*.py` files only.
- All changes require review/approval per `.github/CODEOWNERS`.
- Don't commit generated artifacts: `frontend/dist/`, `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/` are gitignored — keep it that way.

## Code style

- **Python**: formatted and linted with `ruff` (`just format`, `just lint`). Config lives in `pyproject.toml`. Add tests under `tests/` for new behavior — `pytest` config (`testpaths = ["tests"]`) is also in `pyproject.toml`.
- **Frontend**: Vue 3 `<script setup>` SFCs, Tailwind utility classes (v4, via `@tailwindcss/vite` — no `tailwind.config.js` needed for basic usage). Match the existing style in `frontend/src/App.vue`.
- Avoid introducing new tooling or abstractions beyond what a change needs — this is a small app; prefer the simplest change that works.
