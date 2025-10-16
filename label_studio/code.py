"""
Code Repository Extractor

This script scans the entire repository directory for code files (.py, .js, .jsx, .ts, .tsx, .vue, .css, .html, etc.)
and outputs them to a single text file with file paths and contents.

Usage:
    python code.py

Output:
    repository_code_export.txt - Contains all code files with their paths
"""

import os
from pathlib import Path
from datetime import datetime

# Code file extensions to include
CODE_EXTENSIONS = {
    # Python
    '.py',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    # Web
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    # Vue/React/Angular
    '.vue', '.svelte',
    # Config files
    '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.config',
    # Shell scripts
    '.sh', '.bash', '.zsh',
    # Other
    '.sql', '.md', '.txt', '.env.example'
}

# Directories to exclude
EXCLUDE_DIRS = {
    '__pycache__',
    'node_modules',
    '.git',
    '.venv',
    'venv',
    'env',
    '.env',
    'dist',
    'build',
    '.next',
    '.nuxt',
    'coverage',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'htmlcov',
    'site-packages',
    '.idea',
    '.vscode',
    'migrations',  # Django migrations can be verbose
}

# Files to exclude
EXCLUDE_FILES = {
    'package-lock.json',
    'yarn.lock',
    'poetry.lock',
    'Pipfile.lock',
    '.DS_Store',
    'thumbs.db',
}

def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed based on extension and exclusions."""
    # Check if any parent directory is in exclude list
    for parent in file_path.parents:
        if parent.name in EXCLUDE_DIRS:
            return False

    # Check if filename is in exclude list
    if file_path.name in EXCLUDE_FILES:
        return False

    # Check if extension is in our list
    if file_path.suffix.lower() in CODE_EXTENSIONS:
        return True

    # Check for files without extensions that might be config files
    if not file_path.suffix and file_path.name in ['Dockerfile', 'Makefile', 'Procfile', '.env.example']:
        return True

    return False

def get_relative_path(file_path: Path, root_dir: Path) -> str:
    """Get relative path from root directory."""
    try:
        return str(file_path.relative_to(root_dir))
    except ValueError:
        return str(file_path)

def read_file_content(file_path: Path) -> str:
    """Read file content with fallback encodings."""
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            return f"[ERROR READING FILE: {e}]"

    return "[ERROR: Could not decode file with any supported encoding]"

def scan_repository(root_dir: Path, output_file: Path):
    """Scan repository and write all code files to output."""

    print(f"Scanning repository at: {root_dir}")
    print(f"Output file: {output_file}")
    print("-" * 80)

    file_count = 0
    error_count = 0

    with open(output_file, 'w', encoding='utf-8') as out:
        # Write header
        out.write("=" * 80 + "\n")
        out.write(f"REPOSITORY CODE EXPORT\n")
        out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"Root Directory: {root_dir}\n")
        out.write("=" * 80 + "\n\n")

        # Walk through directory tree
        for file_path in sorted(root_dir.rglob('*')):
            if not file_path.is_file():
                continue

            if not should_process_file(file_path):
                continue

            relative_path = get_relative_path(file_path, root_dir)

            try:
                content = read_file_content(file_path)

                # Write file header
                out.write("\n" + "=" * 80 + "\n")
                out.write(f"FILE: {relative_path}\n")
                out.write(f"SIZE: {file_path.stat().st_size} bytes\n")
                out.write("=" * 80 + "\n\n")

                # Write file content
                out.write(content)

                # Add trailing newlines
                if not content.endswith('\n'):
                    out.write('\n')
                out.write('\n')

                file_count += 1
                print(f"✓ Processed: {relative_path}")

            except Exception as e:
                error_count += 1
                print(f"✗ Error processing {relative_path}: {e}")

                # Write error to output file
                out.write("\n" + "=" * 80 + "\n")
                out.write(f"FILE: {relative_path}\n")
                out.write(f"ERROR: {e}\n")
                out.write("=" * 80 + "\n\n")

        # Write footer
        out.write("\n" + "=" * 80 + "\n")
        out.write(f"EXPORT COMPLETE\n")
        out.write(f"Files processed: {file_count}\n")
        out.write(f"Errors encountered: {error_count}\n")
        out.write("=" * 80 + "\n")

    print("-" * 80)
    print(f"Export complete!")
    print(f"Files processed: {file_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Output saved to: {output_file}")

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()

    # Output file in the same directory
    output_file = script_dir / "repository_code_export.txt"

    print("=" * 80)
    print("CODE REPOSITORY EXTRACTOR")
    print("=" * 80)
    print()

    # Confirm with user
    print(f"This will scan: {script_dir}")
    print(f"Output file: {output_file}")
    print()
    response = input("Proceed? (y/n): ").strip().lower()

    if response != 'y':
        print("Operation cancelled.")
        return

    print()

    # Run the scan
    scan_repository(script_dir, output_file)

    # Show file size
    file_size = output_file.stat().st_size
    if file_size > 1024 * 1024:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    elif file_size > 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size} bytes"

    print(f"\nOutput file size: {size_str}")
    print("\nYou can now copy the contents of repository_code_export.txt to another LLM!")

if __name__ == "__main__":
    main()
