# Contributing to The Polite Web Scraper

Thank you for your interest in contributing! This guide explains how to get started, our coding standards, and how to submit changes.

---

## 🚀 Quick Start

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/polite-web-scraper.git
cd polite-web-scraper

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install all dependencies (including dev tools)
pip install -r requirements.txt
pip install ruff pytest-cov

# 4. Run the test suite to verify setup
python -m pytest tests/ -v

# 5. Run the full scraping pipeline
python src/main.py
```

---

## 📂 Project Structure

```
polite-web-scraper/
├── src/                    # Source modules
│   ├── main.py             # Pipeline orchestrator
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Centralized configuration
│   ├── schemas.py          # Pydantic data models
│   ├── normalizer.py       # Data normalization
│   ├── extract.py          # HTML field extraction
│   ├── storage.py          # JSON/SQLite persistence
│   ├── exporters.py        # Multi-format exporters
│   ├── dashboard.py        # Visual HTML dashboard generator
│   ├── server.py           # REST API server
│   ├── analytics.py        # Statistical analysis engine
│   ├── audit.py            # Cryptographic integrity auditor
│   ├── validators.py       # Data quality validators
│   ├── notifications.py    # Event notification system
│   ├── comparator.py       # Dataset change tracker
│   ├── cache_manager.py    # Advanced cache with TTL
│   ├── rate_limiter.py     # Token-bucket rate limiter
│   ├── circuit_breaker.py  # Circuit breaker pattern
│   ├── headers.py          # HTTP header manager
│   ├── terminal_ui.py      # Terminal UI renderer
│   └── ...
├── tests/                  # Pytest test suite
├── output/                 # Generated output files
├── cache/                  # HTTP response cache
└── .github/workflows/      # CI/CD pipeline
```

---

## 🧪 Testing

We use **pytest** for testing. All new features must include corresponding unit tests.

```bash
# Run full test suite
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_config.py -v
```

### Test Guidelines
- Place test files in `tests/` with the naming convention `test_<module>.py`
- Each module should have at least 80% test coverage
- Use `pytest` fixtures and `tmp_path` for temporary file operations
- Mock external HTTP requests — never make real network calls in tests
- Use `monkeypatch` for environment variable testing

---

## 🎨 Code Style

We use **Ruff** for linting and formatting:

```bash
# Check for lint issues
ruff check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix
```

### Style Rules
- **Line length**: 100 characters max
- **Python version**: 3.10+ (use `from __future__ import annotations` for type hints)
- **Type hints**: All public functions must have type annotations
- **Docstrings**: All modules, classes, and public functions need docstrings
- **Imports**: Sorted with `isort` rules (handled by Ruff)

---

## 🔀 Submitting Changes

### Branch Naming
- `feature/<short-description>` for new features
- `fix/<short-description>` for bug fixes
- `docs/<short-description>` for documentation updates
- `test/<short-description>` for test additions

### Pull Request Process
1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Ensure lint passes: `ruff check src/ tests/`
5. Update `CHANGELOG.md` with your changes
6. Open a pull request with a clear description

### Commit Message Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(module): add new feature description
fix(module): fix specific bug description
test(module): add tests for feature
docs(readme): update API documentation
refactor(module): restructure without changing behavior
chore(ci): update CI pipeline configuration
```

---

## 🏗️ Architecture Decisions

### Design Principles
1. **Zero external web framework** — Server is built on Python stdlib `http.server`
2. **Polite by default** — Rate limiting, respectful headers, and cache-first approach
3. **Schema-first validation** — Pydantic v2 for all data contracts
4. **Observable** — Every stage produces metrics, logs, and audit trails
5. **Modular** — Each feature is an independent module with its own tests

### Adding a New Module
1. Create `src/new_module.py` with a module docstring
2. Add exports to `src/__init__.py` and `__all__`
3. Create `tests/test_new_module.py`
4. Update `README.md` if the feature is user-facing
5. Update `CHANGELOG.md`

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.
