# yapper-snip

- Tests: `uv run pytest`. Lint: `uv run ruff check`. The pre-commit hook in `.githooks/` runs both; enable it with `git config core.hooksPath .githooks`.
- Vocabulary: `GLOSSARY.md` (Portuguese first, English below). Docs for users put Portuguese above English.
- Review standards: `CODING_STANDARDS.md`.
- `work/`, `models/` and `settings.json` are gitignored runtime state.
- A running app keeps serving the code it started with. Before trying a change in the browser, run `uv run python -m app stop`, then start it again.
