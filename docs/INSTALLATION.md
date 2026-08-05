# Installation

This guide covers installing AIFME Scout OSS on all supported platforms.

## Prerequisites

- **Python 3.11 or higher** — Scout OSS uses modern Python typing features and requires >=3.11
- **pip** — Usually included with Python installations
- **Virtual environment** — Recommended for isolation

## Verify Python Version

```bash
python --version
# Should output: Python 3.11.x or higher
```

## Install from PyPI (Recommended)

```bash
pip install aifme-scout
```

Verify installation:

```bash
aifme-scout --version
# Should output: aifme-scout, version 1.0.0
```

## Upgrade

```bash
pip install --upgrade aifme-scout
```

## Platform-Specific Instructions

### Ubuntu / Debian

```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Scout OSS
pip install aifme-scout
```

### macOS

```bash
# Install Python 3.11 via Homebrew
brew install python@3.11

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Scout OSS
pip install aifme-scout
```

### Windows

```powershell
# Install Python 3.11 from python.org or Microsoft Store

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install Scout OSS
pip install aifme-scout
```

If you encounter PowerShell execution policy errors:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Editable Install (Development)

For contributors and developers who want to modify the source:

```bash
git clone https://github.com/SureshBabuoo7/aifme-scout.git
cd aifme-scout
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Verify Installation

```bash
# Check version
aifme-scout --version

# Run help
aifme-scout --help

# Quick smoke test
aifme-scout scan https://www.python.org --quiet
```

## Dependencies

Scout OSS has minimal runtime dependencies:

| Package | Purpose | Version |
|---------|---------|---------|
| beautifulsoup4 | HTML parsing | >=4.12.0 |
| fastapi | REST API | >=0.100.0 |
| httpx | HTTP client | >=0.27.0 |
| jsonschema | JSON Schema validation | >=4.21.0 |
| pyyaml | Configuration loading | >=6.0 |
| uvicorn | ASGI server | >=0.27.0 |

Development dependencies (installed with `.[dev]`):

| Package | Purpose |
|---------|---------|
| ruff | Linting and import sorting |
| black | Code formatting |
| mypy | Static type checking |
| pytest | Test runner |
| pytest-cov | Coverage reporting |
| pre-commit | Git hook management |
| build | Package building |
| types-PyYAML | Type stubs |
| types-beautifulsoup4 | Type stubs |

## Troubleshooting

### pip install fails with "externally-managed-environment"

On newer Linux distributions, use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install aifme-scout
```

### Import errors after installation

Ensure you're using the correct Python interpreter:

```bash
python -c "import aifme_scout; print(aifme_scout.__version__)"
```

### Slow first run

The first scan may be slower as httpx/BeautifulSoup caches are warmed. Subsequent scans are faster.

## Uninstall

```bash
pip uninstall aifme-scout
```
