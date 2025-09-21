# check_path.py
import sys
import os

print("--- Python's Search Paths (sys.path) ---")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

print("\n--- Verification ---")
expected_path = os.getcwd()
if expected_path in sys.path:
    print(f" The current directory is in the path: {expected_path}")
else:
    print(f"CRITICAL ERROR: The current directory is NOT in the path: {expected_path}")