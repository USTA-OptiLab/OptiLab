# GEMINI.md

@AGENTS.md

Gemini CLI specific notes:

- Full instructions are in `AGENTS.md` (shared across agents) — read it before making changes.
- Quick reference: use `just install` / `just dev` / `just check` rather than calling `pip`, `npm`, `ruff`, or `pytest` directly.
- Commits must be Conventional Commits (`<type>(<scope>): <subject>`) — enforced by `commitlint` in CI.
