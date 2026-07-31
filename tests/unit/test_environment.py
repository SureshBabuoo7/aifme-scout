"""Placeholder tests verifying the development environment is correctly configured."""

import importlib
import sys


def test_python_version() -> None:
    assert sys.version_info >= (3, 11), "Python 3.11+ is required"


def test_package_importable() -> None:
    module = importlib.import_module("aifme_scout")
    assert hasattr(module, "__version__")


def test_pytest_available() -> None:
    importlib.import_module("pytest")
