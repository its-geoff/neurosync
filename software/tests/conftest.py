"""conftest.py

Shared fixtures and import stubs for the NeuroSync test suite.
Installs a pylsl stub before any test file imports main.py.
"""

import sys
import types
import unittest.mock as mock


def pytest_configure(config):
    if "pylsl" not in sys.modules:
        pylsl = types.ModuleType("pylsl")
        pylsl.resolve_byprop = lambda *a, **k: [mock.MagicMock()]
        pylsl.StreamInlet = mock.MagicMock
        sys.modules["pylsl"] = pylsl
