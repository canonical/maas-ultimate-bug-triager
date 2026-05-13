# MAAS Ultimate Bug Triager

A tool to triage MAAS bugs, reproduce them, and ultimately suggest fixes.

## Project Structure

- **`backend/`** — Python backend using [uv](https://docs.astral.sh/uv/) for dependency management. See `backend/pyproject.toml` for dependencies and configuration.
- **`frontend/`** — Frontend (planned, npm/TypeScript).

## Getting Started

### Backend

```shell
cd backend
uv sync
uv run maas-triager
```

### Running Tests & Linting

```shell
cd backend
uv run pytest
uv run ruff check src tests
```
