import sys
from unittest.mock import MagicMock
# Mock aiofiles
sys.modules["aiofiles"] = MagicMock()
sys.modules["aiofiles.os"] = MagicMock()
# Mock fastapi
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.concurrency"] = MagicMock()

sys.path.insert(0, r"n:\Programmation\GitHub\anonyfiles")

print("--- Validation Script ---")
try:
    from anonyfiles_api.core_config import set_job_id
    set_job_id("test")
    set_job_id(None)
    print("OK: set_job_id works")
except Exception as e:
    print(f"FAIL: set_job_id error: {e}")

try:
    from anonyfiles_api.job_utils import Job
    j = Job("test-id")
    if hasattr(j, 'set_initial_status_async'):
        print("OK: Job.set_initial_status_async exists")
    else:
        print("FAIL: Job.set_initial_status_async MISSING")
        
    if hasattr(j, 'set_status_as_error_async'):
        print("OK: Job.set_status_as_error_async exists")
    else:
        print("FAIL: Job.set_status_as_error_async MISSING")
except Exception as e:
    print(f"FAIL: Job class error: {e}")
