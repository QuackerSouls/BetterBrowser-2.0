#!/usr/bin/env python3
"""
PyBrowser Launcher Script
Simple script to launch the advanced browser with proper error handling
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['PyQt6', 'PyQt6.QtWebEngineWidgets']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install PyQt6 PyQt6-WebEngine")
        return False

    return True

def main():
    """Main launcher function"""
    print("PyBrowser Advanced - Starting...")

    # Check requirements
    if not check_python_version():
        input("Press Enter to exit...")
        return

    if not check_dependencies():
        input("Press Enter to exit...")
        return

    # Launch browser
    try:
        browser_path = Path(__file__).parent / "advanced_browser.py"
        if not browser_path.exists():
            print(f"Error: Browser file not found at {browser_path}")
            input("Press Enter to exit...")
            return

        # Import and run the browser
        sys.path.insert(0, str(browser_path.parent))
        import advanced_browser
        advanced_browser.main()

    except Exception as e:
        print(f"Error starting browser: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
