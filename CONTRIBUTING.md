# Contributing to OpenPanCan

Thank you for your interest in contributing to OpenPanCan!

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html).

## How to Contribute

### Reporting Issues

- Search existing issues before opening a new one
- Use issue templates when available
- Provide reproduction steps, environment details, and logs

### Suggesting Features

- Open a feature request issue describing the use case
- Discuss with maintainers before implementing large changes

### Development Setup

```bash
git clone https://github.com/OpenPanCan/openpancan.git
cd openpancan
cp .env.example .env
make install
```

### Code Standards

- Python: follow PEP 8, use type annotations, add docstrings
- TypeScript: strict mode, descriptive variable names
- Commit messages: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- All PRs must include tests

### Module Development

Each module is independently runnable. To add a new module:

1. Create `modules/<name>/pyproject.toml`
2. Create `modules/<name>/src/<name>/api.py` (FastAPI server)
3. Register in `gateway/src/gateway/main.py` `MODULES` dict
4. Add to `Makefile` for individual start target
5. Add doctor check in `doctor/main.py`

### Pull Request Process

1. Fork the repo and create a feature branch
2. Make changes with clear commit messages
3. Add tests for new functionality
4. Ensure `make install` succeeds
5. Update documentation (README, DEVLOG)
6. Open PR with description of changes

### Database Data Contributions

Real database data (COSMIC, TCGA, OncoKB, etc.) is not committed to the repo. To contribute data:

1. Download from the official source
2. Process into the format described in `docs/database/integration-guide.md`
3. Open an issue with the source version and download URL
