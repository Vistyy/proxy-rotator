#!/usr/bin/env python
import tomli
import sys
from pathlib import Path


def read_pyproject_toml():
    """Read dependencies from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)

    main_deps = pyproject["project"]["dependencies"]
    test_deps = pyproject["project"]["optional-dependencies"]["test"]
    return main_deps, test_deps


def write_requirements_in(main_deps, test_deps):
    """Write dependencies to requirements.in."""
    with open("requirements.in", "w") as f:
        f.write("# Main dependencies\n")
        for dep in main_deps:
            f.write(f"{dep}\n")

        f.write("\n# Test dependencies\n")
        for dep in test_deps:
            f.write(f"{dep}\n")


def main():
    """Sync dependencies from pyproject.toml to requirements.in."""
    try:
        main_deps, test_deps = read_pyproject_toml()
        write_requirements_in(main_deps, test_deps)
        print("Successfully synced dependencies from pyproject.toml to requirements.in")
        return 0
    except Exception as e:
        print(f"Error syncing dependencies: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
