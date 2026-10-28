# CLAUDE.md

@AGENTS.md

Claude Code specific notes:

- Use the `run` skill (or `just dev`) to actually exercise UI/behavior changes before reporting them done — type-checking/tests don't verify the pywebview bridge or the rendered UI.
- Prefer the `justfile` recipes over ad hoc `pip`/`npm`/`ruff`/`pytest` invocations so behavior matches what's documented in `AGENTS.md` and `README.md`.
