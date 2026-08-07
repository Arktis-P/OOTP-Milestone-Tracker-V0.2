"""
PyInstaller Build & Packaging Script for OOTP Milestone Tracker V0.2 (Phase 16.2)
Bundles application code, assets, and data files into a standalone executable.
"""

import os
import sys
import subprocess


def build():
    print("==================================================")
    print("Building OOTP Milestone Tracker V0.2 Executable...")
    print("==================================================")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(root_dir, "main.py")
    data_dir = os.path.join(root_dir, "data")

    # PyInstaller command flags
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "OOTP_Milestone_Tracker_V0.2",
        "--add-data", f"{data_dir}{os.path.pathsep}data",
        main_py
    ]

    print("Running command:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, cwd=root_dir)
        print("\n✅ Build completed successfully! Output located at dist/OOTP_Milestone_Tracker_V0.2/")
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        print("Ensure PyInstaller is installed (`pip install pyinstaller`).")


if __name__ == "__main__":
    build()
