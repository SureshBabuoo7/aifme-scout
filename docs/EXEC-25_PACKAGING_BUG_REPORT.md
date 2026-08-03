# EXEC-25 — Critical PyPI Packaging Bug

**Date:** 2026-08-04  
**Repository:** https://github.com/SureshBabuoo7/aifme-scout  
**Task:** Fix critical packaging regression where installed wheel fails with FileNotFoundError for schema file  
**Status:** PASS

---

## Root Cause

The `dist/` directory contained stale build artifacts from previous version bumps, and the source code contained a filesystem-based fallback for schema loading that was incompatible with wheel installs.

### Detailed Root Cause

1. **PyPI version 1.0.0rc2 was uploaded before the schema embedding fix from EXEC-24.** The uploaded wheel did not contain `schemas/v1/scan-result.schema.json` at the expected location.

2. **Filesystem fallback masked the real issue.** `src/aifme_scout/extractors/schema.py` had a fallback path `_BACKUP_SCHEMA_PATH` that computed the schema location relative to the source file:
   ```python
   Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "v1" / "scan-result.schema.json"
   ```
   In a wheel install, this resolves to `site-packages/schemas/v1/scan-result.schema.json`, which does not exist.

3. **The `try/except` block caught the `FileNotFoundError` from `importlib.resources` and attempted the filesystem fallback, which also failed, producing the observed error.**

---

## Files Changed

| File | Change |
|------|--------|
| `src/aifme_scout/extractors/schema.py` | Removed `_BACKUP_SCHEMA_PATH` and filesystem fallback. Use only `importlib.resources`. |
| `pyproject.toml` | Version `1.0.0rc2` → `1.0.0rc3` |
| `src/aifme_scout/__init__.py` | `__version__ = "1.0.0rc3"` |
| `src/aifme_scout/cli/__init__.py` | `version="%(prog)s 1.0.0rc3"` |
| `VERSION` | `1.0.0rc3` |

---

## Version History

| Location | Before | After |
|----------|--------|-------|
| `pyproject.toml` | `1.0.0rc2` | `1.0.0rc3` |
| `VERSION` | `1.0.0rc2` | `1.0.0rc3` |
| `src/aifme_scout/__init__.py` | `1.0.0rc2` | `1.0.0rc3` |
| `src/aifme_scout/cli/__init__.py` | `1.0.0rc2` | `1.0.0rc3` |
| `src/aifme_scout/extractors/schema.py` | `_ENGINE_VERSION = "1.0.0-rc2"` | `_ENGINE_VERSION = "1.0.0rc3"` |

---

## Wheel Names

| Artifact | Name |
|----------|------|
| Wheel | `aifme_scout-1.0.0rc3-py3-none-any.whl` |
| SDist | `aifme_scout-1.0.0rc3.tar.gz` |

---

## Build Verification

| Step | Command | Result |
|------|---------|--------|
| Clean build | `python -m build` | ✅ `aifme_scout-1.0.0rc3-py3-none-any.whl` |
| Twine check | `python -m twine check dist/*` | ✅ PASSED |
| pip install | `pip install aifme-scout` | ✅ `aifme-scout-1.0.0rc3` |
| Version | `aifme-scout --version` | ✅ `aifme-scout 1.0.0rc3` |
| Version | `python -m aifme_scout --version` | ✅ `aifme-scout 1.0.0rc3` |

---

## PyPI Verification (Fresh Install)

| Site | Exit Code | Evidence | Status |
|------|-----------|----------|--------|
| https://python.org | 0 | 320 | ✅ PASS |
| https://openai.com | 0 | 2 | ✅ PASS |

**Both sites scanned successfully from a clean virtual environment installed via PyPI.**

---

## What Was Fixed in schema.py

**Before:**
```python
_BACKUP_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas"
    / "v1"
    / "scan-result.schema.json"
)

def _load_schema() -> dict[str, Any]:
    try:
        data = importlib.resources.files("aifme_scout").joinpath(*_SCHEMA_RESOURCE).read_text(encoding="utf-8")
        return json.loads(data)
    except (FileNotFoundError, ModuleNotFoundError):
        with _BACKUP_SCHEMA_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
```

**After:**
```python
def _load_schema() -> dict[str, Any]:
    data = importlib.resources.files("aifme_scout").joinpath(*_SCHEMA_RESOURCE).read_text(encoding="utf-8")
    return json.loads(data)
```

The filesystem fallback was removed entirely. `importlib.resources.files("aifme_scout").joinpath(*_SCHEMA_RESOURCE).read_text()` correctly loads the schema from the wheel package.

---

## PyPI Release

| Attribute | Value |
|-----------|-------|
| Version | `1.0.0rc3` |
| PyPI URL | https://pypi.org/project/aifme-scout/1.0.0rc3/ |
| Install command | `pip install aifme-scout` |
| Status | ✅ Uploaded and verified |

---

## Commit

```
1732aa1 fix(packaging): remove filesystem schema fallback and bump to 1.0.0rc3 (EXEC-25)
```

---

## Recommendation

**READY FOR PYPI — 1.0.0rc3**

The critical packaging bug is fixed. The schema is now loaded exclusively via `importlib.resources`, which works correctly in wheel installs. Verified with fresh virtual environment installations from PyPI.

---

*Report generated as part of EXEC-25 — Critical PyPI Packaging Bug.*
