# Contributing to wxdiagram

## Development setup

wxdiagram uses [uv](https://docs.astral.sh/uv/) for environment management:

```bash
git clone https://github.com/abulka/wxdiagram.git
cd wxdiagram
uv sync
```

This creates `.venv/` with wxPython and the dev dependencies (pytest, coverage,
ruff).

## Running the demos and tests

```bash
uv run python -m wxdiagram.demo
uv run python -m wxdiagram.shapesdemo
uv run python -m wxdiagram.layoutdemo
uv run python -m pytest tests/ -q
uv run ruff check .
uv run ruff format --check .
uv run mkdocs build
uv build
```

On a headless Linux machine, run the tests under `xvfb-run -a`.

## Making changes

- Keep changes small and reviewable.
- `uv run ruff check .` and `uv run ruff format --check .` must pass.
- Run the test suite before pushing.
- If you change the public API (`wxdiagram/__init__.py`), update
  `tests/test_api_contract.py`.
- Do not add drawing-time globals that require `initialize()`; it is optional
  and resources are created lazily.
- Use `CamelCase` for public API methods; keep internal helpers snake_case.
- If you change a demo's layout or controls, regenerate its screenshot with
  `uv run python bin/make-demo-screenshots` and commit the PNG.

## Release process

1. Update the version in `pyproject.toml` and `CHANGELOG.md`.
2. `uv build`.
3. Publish with `uv publish` (or the GitHub Actions trusted-publishing
   workflow).
