import sys
from pathlib import Path

import pytest

# Ensure project root is in sys.path for test imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def disable_api_key_by_default(monkeypatch):
    """Keep the optional API auth disabled unless a test enables it explicitly."""
    monkeypatch.delenv("ANONYFILES_API_KEY", raising=False)
