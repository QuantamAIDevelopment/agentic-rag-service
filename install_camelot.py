#!/usr/bin/env python3
"""Install camelot-py for advanced table extraction."""

import subprocess
import sys

def install_camelot():
    """Install camelot-py with required dependencies."""
    try:
        print("Installing camelot-py for advanced table extraction...")
        
        # Install camelot with CV dependencies
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "camelot-py[cv]", "--upgrade"
        ])
        
        print("✓ camelot-py installed successfully!")
        print("Advanced table extraction is now available.")
        
        # Test import
        try:
            import camelot
            print("✓ camelot-py import test successful")
        except ImportError as e:
            print(f"✗ Import test failed: {e}")
            print("You may need to install additional system dependencies:")
            print("- Windows: Install Visual C++ Build Tools")
            print("- Linux: sudo apt-get install python3-tk ghostscript")
            print("- macOS: brew install ghostscript")
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Installation failed: {e}")
        print("Try manual installation: pip install camelot-py[cv]")

if __name__ == "__main__":
    install_camelot()