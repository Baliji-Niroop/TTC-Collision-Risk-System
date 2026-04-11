#!/usr/bin/env python3
"""
Execute file operations tasks
"""
import os
import pathlib
import sys

def main():
    # Base directory
    base_dir = r'C:\Users\niroo\Downloads\TTC'
    os.chdir(base_dir)
    
    results = []
    
    # 1. Delete live_data.txt
    try:
        os.remove(r'LOGS\live_data.txt')
        results.append('✓ Deleted: LOGS/live_data.txt')
    except FileNotFoundError:
        results.append('✗ Not found: LOGS/live_data.txt')
    except Exception as e:
        results.append(f'✗ Error deleting LOGS/live_data.txt: {e}')
    
    # 2. Delete ttc_system.log
    try:
        os.remove(r'LOGS\ttc_system.log')
        results.append('✓ Deleted: LOGS/ttc_system.log')
    except FileNotFoundError:
        results.append('✗ Not found: LOGS/ttc_system.log')
    except Exception as e:
        results.append(f'✗ Error deleting LOGS/ttc_system.log: {e}')
    
    # 3. Create LOGS\archive directory
    try:
        logs_archive = pathlib.Path(r'LOGS\archive')
        logs_archive.mkdir(exist_ok=True)
        results.append('✓ Created: LOGS/archive')
    except Exception as e:
        results.append(f'✗ Error creating LOGS/archive: {e}')
    
    # 4. Create build directory
    try:
        build_dir = pathlib.Path('build')
        build_dir.mkdir(exist_ok=True)
        results.append('✓ Created: build')
    except Exception as e:
        results.append(f'✗ Error creating build: {e}')
    
    # 5. Create .gitkeep file
    try:
        gitkeep_file = pathlib.Path('build') / '.gitkeep'
        gitkeep_file.touch()
        results.append('✓ Created: build/.gitkeep')
    except Exception as e:
        results.append(f'✗ Error creating build/.gitkeep: {e}')
    
    # 6. Create README.md with content
    try:
        readme_content = '''# Build Artifacts Directory

This directory is used for storing build artifacts generated during the build process.

## Purpose
- Compiled output files
- Built binaries and executables
- Intermediate compilation outputs
- Generated deployment packages

## .gitkeep
The `.gitkeep` file ensures this directory is tracked by Git even when empty.
'''
        readme_file = pathlib.Path('build') / 'README.md'
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        results.append('✓ Created: build/README.md')
    except Exception as e:
        results.append(f'✗ Error creating build/README.md: {e}')
    
    # Print results
    print('\n'.join(results))
    print(f'\n{"=" * 50}')
    print('All tasks completed!')
    print(f'{"=" * 50}')

if __name__ == '__main__':
    main()
