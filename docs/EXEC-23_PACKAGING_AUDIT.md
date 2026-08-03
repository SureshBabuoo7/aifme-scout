# EXEC-23 — Packaging Audit

**Date:** 2026-08-03  
**Repository:** https://github.com/SureshBabuoo7/aifme-scout  
**Task:** PyPI release preparation — version and wheel consistency audit  
**Status:** PASS

---

## Root Cause

The `dist/` directory contained stale build artifacts from earlier version bumps:
- `aifme_scout-0.0.0-py3-none-any.whl`
- `aifme_scout-1.0.0rc1-py3-none-any.whl`

The source version in `pyproject.toml`, `VERSION`, and `__init__.py` was `1.0.0-rc2` (with hyphen). While hatchling normalizes this to `1.0.0rc2` in wheel metadata, the non-PEP-440 hyphenated form was inconsistent across:
1. Package `__version__` string
2. CLI hardcoded version argument
3. PyPI package metadata URLs pointing to the old `aifme/aifme-scout` org

**Result:** No RC2 wheel existed in `dist/` because the directory had not been cleaned and rebuilt after the version bump.

---

## Files Changed

| File | Change |
|------|--------|
| `pyproject.toml` | `version = "1.0.0rc2"` (was `1.0.0-rc2`) |
| `pyproject.toml` | Fixed `Homepage` and `Repository` URLs from `aifme/aifme-scout` to `SureshBabuoo7/aifme-scout` |
| `VERSION` | `1.0.0rc2` (was `1.0.0-rc2`) |
| `src/aifme_scout/__init__.py` | `__version__ = "1.0.0rc2"` (was `1.0.0-rc2`) |
| `src/aifme_scout/cli/__init__.py` | `version="%(prog)s 1.0.0rc2"` (was `1.0.0-rc2`) |

---

## Version History

| Location | Before | After |
|----------|--------|-------|
| `pyproject.toml` | `1.0.0-rc2` | `1.0.0rc2` |
| `VERSION` | `1.0.0-rc2` | `1.0.0rc2` |
| `src/aifme_scout/__init__.py` | `1.0.0-rc2` | `1.0.0rc2` |
| `src/aifme_scout/cli/__init__.py` | `1.0.0-rc2` | `1.0.0rc2` |

---

## Wheel Names

| Artifact | Before | After |
|----------|--------|-------|
| Wheel | `aifme_scout-1.0.0rc1-py3-none-any.whl` | `aifme_scout-1.0.0rc2-py3-none-any.whl` |
| SDist | `aifme_scout-1.0.0rc1.tar.gz` | `aifme_scout-1.0.0rc2.tar.gz` |
| Stale artifacts | `aifme_scout-0.0.0-*` present | Removed |

---

## Build Verification

| Step | Command | Result |
|------|---------|--------|
| Clean build | `python -m build` | ✅ `aifme_scout-1.0.0rc2-py3-none-any.whl` |
| Twine check | `python -m twine check dist/*` | ✅ PASSED |
| pip install | `python -m pip install --force-reinstall dist/aifme_scout-1.0.0rc2-py3-none-any.whl` | ✅ Successfully installed |
| CLI help | `aifme-scout --help` | ✅ Renders usage |
| CLI help | `python -m aifme_scout --help` | ✅ Renders usage |
| Version | `aifme-scout --version` | ✅ `aifme-scout 1.0.0rc2` |
| Version | `python -m aifme_scout --version` | ✅ `aifme-scout 1.0.0rc2` |

---

## Wheel Metadata Verification

| Field | Value |
|-------|-------|
| Name | `aifme-scout` |
| Version | `1.0.0rc2` |
| Homepage | `https://github.com/SureshBabuoo7/aifme-scout` |
| Repository | `https://github.com/SureshBabuoo7/aifme-scout` |
| License | `Apache-2.0` |
| Requires-Python | `>=3.11` |
| Twine check | PASSED |

---

## Commit

```
9152f31 fix(packaging): normalize version to PEP 440 for PyPI release (EXEC-23)
```

---

## Recommendation

**READY FOR PYPI**

The package builds cleanly, passes twine validation, installs correctly, and reports the correct version. All version strings are now PEP 440 compliant and consistent. The only remaining step is to upload to PyPI:

```bash
python -m twine upload dist/*
```

---

*Report generated as part of EXEC-23 — Packaging Audit.*
