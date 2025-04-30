#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def setup_virtual_environment(install_path):
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", os.path.join(install_path, "venv")], check=True)
    
    # Get the pip path in the new virtual environment
    if sys.platform == "win32":
        pip_path = os.path.join(install_path, "venv", "Scripts", "pip")
    else:
        pip_path = os.path.join(install_path, "venv", "bin", "pip")
    
    print("Installing dependencies...")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    subprocess.run([pip_path, "install", "-e", "."], check=True)

def create_desktop_shortcut(install_path):
    home = str(Path.home())
    if sys.platform == "win32":
        desktop = os.path.join(home, "Desktop")
        shortcut_path = os.path.join(desktop, "DVT.bat")
        with open(shortcut_path, "w") as f:
            f.write(f'@echo off\ncall "{os.path.join(install_path, "venv", "Scripts", "activate.bat")}"\ndvt\n')
    else:
        desktop = os.path.join(home, "Desktop")
        shortcut_path = os.path.join(desktop, "DVT.desktop")
        with open(shortcut_path, "w") as f:
            f.write(f"""[Desktop Entry]
Name=DVT
Exec={os.path.join(install_path, "venv", "bin", "dvt")}
Type=Application
Terminal=false
""")
        os.chmod(shortcut_path, 0o755)

def main():
    check_python_version()
    
    # Default installation path
    if sys.platform == "win32":
        default_install_path = "C:\\Program Files\\DVT"
    else:
        default_install_path = "/opt/dvt"
    
    # Get installation path from user
    install_path = input(f"Enter installation path [{default_install_path}]: ").strip()
    if not install_path:
        install_path = default_install_path
    
    # Create installation directory
    os.makedirs(install_path, exist_ok=True)
    
    try:
        setup_virtual_environment(install_path)
        create_desktop_shortcut(install_path)
        print(f"\nInstallation completed successfully!")
        print(f"Application installed to: {install_path}")
        print("A desktop shortcut has been created.")
    except Exception as e:
        print(f"Error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()