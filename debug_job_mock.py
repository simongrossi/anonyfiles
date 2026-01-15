import sys
from unittest.mock import MagicMock

# Mock aiofiles
sys.modules["aiofiles"] = MagicMock()
sys.modules["aiofiles.os"] = MagicMock()

# Mock fastapi
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.concurrency"] = MagicMock()

# Add project root
sys.path.insert(0, r"n:\Programmation\GitHub\anonyfiles")

try:
    from anonyfiles_api.job_utils import Job

    print("Job class imported.")
    j = Job("test-id")
    print(f"Job methods: {dir(j)}")
    print(f"Has set_initial_status_async: {hasattr(j, 'set_initial_status_async')}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
