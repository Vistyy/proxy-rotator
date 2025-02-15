# Proxy Rotator

A proxy rotation and management system.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/proxy-rotator.git
cd proxy-rotator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
make setup
```

## Dependency Management

Dependencies are managed in `pyproject.toml`. The workflow is:

1. Edit dependencies in `pyproject.toml` under:
   - `project.dependencies` for main dependencies
   - `project.optional-dependencies.test` for test dependencies
   - `project.optional-dependencies.dev` for development tools

2. After changing dependencies, run:
```bash
make compile  # Generates requirements.in and requirements.txt
make sync    # Installs the exact versions from requirements.txt
```

3. To update all dependencies to their latest versions:
```bash
make update
```

## Running Tests

```bash
make test
```

This will:
- Install the package in development mode
- Run all tests with coverage reporting
- Generate an HTML coverage report in `htmlcov/` 