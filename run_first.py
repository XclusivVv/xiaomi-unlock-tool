#!/usr/bin/env python3
"""
Setup script for Xiaomi Unlock Tool
Creates virtual environment, installs dependencies, and runs the application
"""

import subprocess
import sys
import os
import platform
import venv

def run_command(command, shell=False, check=True):
    """Execute a command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("=" * 60)
    print("Xiaomi Unlock Tool - Setup")
    print("=" * 60)
    print()
    
    # Detect OS
    system = platform.system()
    print(f"Detected OS: {system}")
    print()
    
    # Step 1: Create virtual environment
    venv_name = "venv"
    print(f"[1/4] Creating virtual environment '{venv_name}'...")
    
    try:
        venv.create(venv_name, with_pip=True)
        print("✓ Virtual environment created successfully")
    except Exception as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return False
    
    print()
    
    # Determine activation command and pip path based on OS
    if system == "Windows":
        activate_script = os.path.join(venv_name, "Scripts", "activate.bat")
        pip_executable = os.path.join(venv_name, "Scripts", "pip.exe")
        python_executable = os.path.join(venv_name, "Scripts", "python.exe")
    else:  # Linux, macOS, etc.
        activate_script = os.path.join(venv_name, "bin", "activate")
        pip_executable = os.path.join(venv_name, "bin", "pip")
        python_executable = os.path.join(venv_name, "bin", "python")
    
    # Step 2: Upgrade pip
    print("[2/4] Upgrading pip...")
    if system == "Windows":
        success = run_command([pip_executable, "install", "--upgrade", "pip"], check=False)
    else:
        success = run_command([pip_executable, "install", "--upgrade", "pip"], check=False)
    
    if success:
        print("✓ Pip upgraded successfully")
    else:
        print("⚠ Pip upgrade had issues, continuing anyway...")
    
    print()
    
    # Step 3: Install requirements
    print("[3/4] Installing dependencies...")
    
    requirements = [
        "customtkinter",
        "ntplib",
        "pytz",
        "urllib3",
        "icmplib",
        "requests",
    ]
    
    all_installed = True
    for requirement in requirements:
        print(f"  Installing {requirement}...", end=" ", flush=True)
        if run_command([pip_executable, "install", requirement], check=False):
            print("✓")
        else:
            print("✗")
            all_installed = False
    
    if all_installed:
        print("✓ All dependencies installed successfully")
    else:
        print("⚠ Some dependencies failed to install. This may cause issues.")
    
    print()
    
    # Step 4: Run the application
    print("[4/4] Launching Xiaomi Unlock Tool...")
    print()
    print("-" * 60)
    print()
    
    if system == "Windows":
        # On Windows, use the python executable from venv
        run_command([python_executable, "app.py"])
    else:
        # On Unix-like systems
        run_command([python_executable, "app.py"])
    
    print()
    print("-" * 60)
    print()
    print("Application closed. Thank you for using Xiaomi Unlock Tool!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)