#!/usr/bin/env python3
"""
TTC PROJECT FINAL CLEANUP - Comprehensive reorganization and cleanup
"""

import os
import shutil
from pathlib import Path

def safe_remove_dir(path):
    """Safely remove a directory."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return True
    except Exception as e:
        print(f"   Warning: Could not remove {path}: {e}")
    return False

def safe_remove_file(path):
    """Safely remove a file."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception as e:
        print(f"   Warning: Could not remove {path}: {e}")
    return False

def safe_move_file(src, dst):
    """Safely move a file."""
    try:
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return True
    except Exception as e:
        print(f"   Warning: Could not move {src} to {dst}: {e}")
    return False

def main():
    os.chdir("C:\\Users\\niroo\\Downloads\\TTC")
    
    print("\n" + "="*60)
    print("  TTC PROJECT CLEANUP - COMPREHENSIVE REORGANIZATION")
    print("="*60 + "\n")
    
    # PHASE 1: Delete Python cache
    print("[PHASE 1] Deleting Python cache directories...")
    cache_dirs = [
        "./.pytest_cache",
        "./src/__pycache__",
        "./tests/__pycache__",
        "./validation/__pycache__",
        "./config/__pycache__",
        "./firmware/config/__pycache__",
        "./ml/__pycache__",
        "./ml/inference/__pycache__",
    ]
    
    for dir_path in cache_dirs:
        if safe_remove_dir(dir_path):
            print(f"  [OK] Removed: {dir_path}")
    print("  Done\n")
    
    # PHASE 2: Delete build artifacts
    print("[PHASE 2] Deleting Arduino build artifacts...")
    if safe_remove_dir("./build"):
        print(f"  [OK] Removed: ./build")
    print("  Done\n")
    
    # PHASE 3: Delete runtime logs
    print("[PHASE 3] Deleting runtime logs...")
    log_files = [
        "./LOGS/live_data.txt",
        "./LOGS/ttc_system.log",
    ]
    
    for log_file in log_files:
        if safe_remove_file(log_file):
            print(f"  [OK] Removed: {log_file}")
    print("  Done\n")
    
    # PHASE 4: Delete test artifacts
    print("[PHASE 4] Cleaning validation test artifacts...")
    test_artifacts = [
        "./validation/outputs/classification_report.txt",
        "./validation/outputs/confusion_matrix.png",
        "./validation/outputs/scenario_summary.png",
        "./validation/outputs/summary.json",
        "./validation/outputs/synthetic_predictions.csv",
        "./validation/outputs/timeline_summary.png",
    ]
    
    for artifact in test_artifacts:
        if safe_remove_file(artifact):
            print(f"  [OK] Removed: {artifact}")
    
    # Remove demo_evidence directories
    demo_evidence_path = "./validation/outputs/demo_evidence"
    if safe_remove_dir(demo_evidence_path):
        print(f"  [OK] Removed: {demo_evidence_path}")
    
    print("  Done\n")
    
    # PHASE 5: Delete old cleanup scripts
    print("[PHASE 5] Removing old cleanup scripts...")
    old_scripts = [
        "./firmware/cleanup.bat",
        "./firmware/cleanup.py",
        "./firmware/do_cleanup.bat",
    ]
    
    for script in old_scripts:
        if safe_remove_file(script):
            print(f"  [OK] Removed: {script}")
    print("  Done\n")
    
    # PHASE 6: Move PROJECT_STRUCTURE.md
    print("[PHASE 6] Moving PROJECT_STRUCTURE.md to docs/...")
    if os.path.isfile("./PROJECT_STRUCTURE.md"):
        if os.path.isfile("./docs/PROJECT_STRUCTURE.md"):
            safe_remove_file("./PROJECT_STRUCTURE.md")
            print(f"  [OK] File already in docs/, removed root copy")
        else:
            safe_move_file("./PROJECT_STRUCTURE.md", "./docs/PROJECT_STRUCTURE.md")
            print(f"  [OK] Moved: PROJECT_STRUCTURE.md -> docs/")
    print("  Done\n")
    
    # PHASE 7: Archive cleanup_project.bat
    print("[PHASE 7] Archiving cleanup_project.bat...")
    if os.path.isfile("./cleanup_project.bat"):
        os.makedirs("./docs/archive", exist_ok=True)
        safe_move_file("./cleanup_project.bat", "./docs/archive/cleanup_project.bat")
        print(f"  [OK] Moved: cleanup_project.bat -> docs/archive/")
    print("  Done\n")
    
    print("="*60)
    print("  CLEANUP COMPLETE!")
    print("="*60)
    print("\nProject is now cleaner and well-organized:")
    print("  - All Python caches removed")
    print("  - Build artifacts cleaned")
    print("  - Test outputs archived/deleted")
    print("  - Old cleanup scripts removed")
    print("  - Documentation centralized")
    print("\nCurrent directory structure is now production-ready.\n")

if __name__ == "__main__":
    main()
