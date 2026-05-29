#!/usr/bin/env python3
"""
Debug script to capture startup errors from main.py
"""
import sys
import traceback

try:
    print("=== Starting main.py ===")
    sys.stdout.flush()
    
    import main
    print("✓ main.py imported successfully")
    sys.stdout.flush()
    
except Exception as e:
    print(f"\n❌ ERROR during import/startup:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\n=== Full Traceback ===")
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)

print("✓ Application started successfully")
