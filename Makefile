.PHONY: install compile sync clean update run test dev-install sync-deps

# Install pip-tools and dev dependencies
install-tools:
	pip install -e ".[dev]"

# Sync requirements.in with pyproject.toml and compile requirements.txt
sync-deps:
	python scripts/sync_dependencies.py

# Compile requirements
compile: sync-deps
	pip-compile --generate-hashes requirements.in

# Install dependencies
sync:
	pip-sync requirements.txt

# Clean up Python cache files
clean:
	powershell -Command "Get-ChildItem -Path . -Filter '__pycache__' -Recurse -Directory | Remove-Item -Recurse -Force"
	powershell -Command "Get-ChildItem -Path . -Filter '*.pyc' -Recurse -File | Remove-Item -Force"
	powershell -Command "Get-ChildItem -Path . -Filter '*.pyo' -Recurse -File | Remove-Item -Force"

# Update all packages to latest versions
update: sync-deps
	pip-compile --upgrade --generate-hashes requirements.in
	pip-sync requirements.txt

# Run the example
run:
	python example.py

# Install and setup everything
setup: install-tools compile sync

# Install package in development mode with test dependencies
dev-install:
	pip install -e ".[test]"

# Run tests
test: dev-install
	pytest

# Default target
all: setup dev-install 