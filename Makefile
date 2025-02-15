.PHONY: install compile sync clean update run test

# Install pip-tools
install-tools:
	pip install pip-tools

# Compile requirements
compile:
	pip-compile --generate-hashes requirements.in

# Install dependencies
sync:
	pip-sync requirements.txt

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Update all packages to latest versions
update:
	pip-compile --upgrade requirements.in
	pip-sync requirements.txt

# Run the example
run:
	python example.py

# Install and setup everything
setup: install-tools compile sync

# Default target
all: setup 