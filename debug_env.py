import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, r"n:\Programmation\GitHub\anonyfiles")

print("--- Debugging Environment ---")
try:
    from anonyfiles_api.core_config import set_job_id
    print(f"SUCCESS: set_job_id found in core_config: {set_job_id}")
except ImportError as e:
    print(f"ERROR: ImportError core_config: {e}")
except AttributeError as e:
    print(f"ERROR: AttributeError core_config: {e}")

try:
    from anonyfiles_api.job_utils import Job
    print(f"SUCCESS: Job class imported from job_utils.")
    
    j = Job("debug-uuid")
    print(f"Job instance: {j}")
    
    methods = dir(j)
    print(f"set_initial_status_async in methods: {'set_initial_status_async' in methods}")
    print(f"check_exists_async in methods: {'check_exists_async' in methods}")
    
except ImportError as e:
    print(f"ERROR: ImportError job_utils: {e}")
except Exception as e:
    print(f"ERROR: Exception with Job class: {e}")

