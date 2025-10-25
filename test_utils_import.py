#!/usr/bin/env python3
"""Quick test to see if utils shim loads correctly."""
import sys
import os

# Add edx-platform to path if needed
sys.path.insert(0, os.path.dirname(__file__))

try:
    from cms.djangoapps.contentstore.utils import reverse_usage_url
    print("✓ SUCCESS: reverse_usage_url imported successfully")
    print(f"  Type: {type(reverse_usage_url)}")
    print(f"  Callable: {callable(reverse_usage_url)}")
except Exception as e:
    print("✗ FAILED to import reverse_usage_url")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error message: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
