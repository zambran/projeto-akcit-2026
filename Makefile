.PHONY: venv install install-dev run test clean

VENV_DIR = .venv

# Detecta SO e ajusta caminhos do venv
ifeq ($(OS),Windows_NT)
	PYTHON_CMD = python
	VENV_BIN = $(VENV_DIR)/Scripts
	RM_VENV = if exist $(VENV_DIR) rmdir /s /q $(VENV_DIR)
	RM_CACHE = for /d /r . %%d in (__pycache__ *.egg-info .pytest_cache) do @if exist "%%d" rmdir /s /q "%%d"
else
	PYTHON_CMD = python3
	VENV_BIN = $(VENV_DIR)/bin
	RM_VENV = rm -rf $(VENV_DIR)
	RM_CACHE = find . -type d \( -name __pycache__ -o -name "*.egg-info" -o -name .pytest_cache \) -exec rm -rf {} +
endif

PIP = $(VENV_BIN)/pip
PYTEST = $(VENV_BIN)/pytest

venv:
	$(PYTHON_CMD) -m venv $(VENV_DIR)

install: venv
	$(PIP) install -r requirements.txt

install-dev: venv
	$(PIP) install -r requirements.txt
	$(PIP) install pytest>=7.0 pytest-cov>=4.0

run: install
	$(PIP) install -e .
	@echo ""
	@echo "Installed! Activate the virtual environment and use 'tracker'."
	@echo "  Linux/macOS: source .venv/bin/activate"
	@echo "  Windows:     .venv\\Scripts\\activate"
	@echo "  Example:     tracker start \"my task\""

test: install-dev
	$(PYTEST)

clean:
	$(RM_VENV)
	$(RM_CACHE)
