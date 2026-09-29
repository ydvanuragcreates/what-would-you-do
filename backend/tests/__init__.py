"""Test environment.

Python imports this file before conftest.py, so these variables are in place before
the app reads its settings. That makes the suite independent of your personal `.env`:
it always uses a fixed test secret and never trips its own rate limiter.
"""

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-only-secret-never-use-outside-tests-0123456789")
os.environ["RATE_LIMIT_ENABLED"] = "false"  # forced; the rate-limit tests switch it on themselves
