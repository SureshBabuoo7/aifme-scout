# Contributing

Thank you for your interest in contributing to AIFME Scout OSS.

## Setup

1. Fork and clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
5. Create a branch for your change:
   ```bash
   git checkout -b feature/your-feature
   ```

## Verify Setup

Run the test suite to verify your environment:

```bash
pytest
```

## Code Quality

This project uses:
- **Ruff** for linting and import sorting
- **Black** for code formatting
- **Mypy** for static type checking
- **pytest** for testing

Run checks manually:
```bash
ruff check src/ tests/
black --check src/ tests/
mypy src/
```

## Branch Naming

Use the following convention:
- `feature/<short-description>` for new features
- `fix/<short-description>` for bug fixes
- `docs/<short-description>` for documentation changes
- `refactor/<short-description>` for refactoring

## Pull Requests

- Link to a related issue in the PR description.
- Describe what changed and why.
- Confirm that the test suite passes.
- Keep PRs scoped to a single concern.

## Coding Standards

- Follow the project's linting and formatting rules.
- Write tests for new behavior.
- Update documentation when changing public interfaces.

## DCO

By contributing, you agree that your contributions will be licensed under the
project's [Apache-2.0 License](./LICENSE).

## Issue Reporting

- Search existing issues before opening a new one.
- Use the issue templates when available.
- Provide a clear description, steps to reproduce, and expected behavior.
