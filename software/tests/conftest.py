"""conftest.py

Shared fixtures and import stubs for the NeuroSync test suite.
Installs a pylsl stub before any test file imports main.py.
Sets matplotlib to the non-interactive Agg backend to suppress
display windows during testing.
"""

import sys
import types
import unittest.mock as mock


def pytest_configure(config):
    import matplotlib

    matplotlib.use("Agg")

    # suppresses matplotlib output
    import matplotlib.pyplot as plt

    plt.show = lambda *a, **k: None
    plt.pause = lambda *a, **k: None

    if "pylsl" not in sys.modules:
        pylsl = types.ModuleType("pylsl")
        pylsl.resolve_byprop = lambda *a, **k: [mock.MagicMock()]
        pylsl.StreamInlet = mock.MagicMock
        sys.modules["pylsl"] = pylsl
