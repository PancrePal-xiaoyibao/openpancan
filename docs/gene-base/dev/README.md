# Development Guides

This directory contains development guides, onboarding documentation, and coding standards for contributing to OpenPanCan Gene Base.

## What Goes Here

- **Environment Setup** — Step-by-step instructions for setting up a local development environment: required tools, Python version, virtual environment, dependency installation, and configuration.
- **Coding Standards** — Code style guidelines (PEP 8), naming conventions, docstring standards, type hinting requirements, and linting/formatting tool configurations.
- **Contribution Workflow** — How to contribute: forking, branching strategy, commit message conventions, pull request process, code review expectations, and merge criteria.
- **Testing Guide** — Testing framework setup, how to write and run unit tests, integration tests, data validation tests, and coverage requirements.
- **Data Pipeline Development** — Guide for developing new ETL pipelines: data source integration patterns, transformation best practices, error handling, and data quality validation.
- **API Development** — How to add new API endpoints, versioning, documentation with OpenAPI, and API testing.
- **Database Migrations** — Schema change management, migration tools (e.g., Alembic), and rollback procedures.
- **CI/CD Pipeline** — Overview of the continuous integration and deployment pipeline: what runs on push/PR, how to interpret results, and how to fix common failures.
- **Troubleshooting** — Common development issues and their solutions.

## File Naming Convention

```
topic-guide.md
```

Examples:
- `environment-setup.md`
- `contribution-workflow.md`
- `testing-guide.md`
- `etl-pipeline-development.md`

## Quick Start for New Contributors

### Prerequisites

- Python 3.10 or later
- Git 2.30 or later
- A code editor (VS Code recommended)
- Docker (optional, for containerized development)

### Setup

```bash
# Clone the repository
git clone https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-.git
cd openpancan-gene-base

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify setup
python -m pytest tests/
```

### First Contribution

1. Find an issue labeled `good first issue` in the issue tracker
2. Comment on the issue to express interest
3. Fork the repository and create a feature branch
4. Make your changes following the coding standards
5. Write/run tests to verify your changes
6. Submit a pull request with a clear description

## Technology Stack

| Component | Technology |
|-----------|------------|
| Core Language | Python 3.10+ |
| Data Processing | Pandas, Polars, NumPy |
| Database | PostgreSQL + SQLAlchemy |
| API Framework | FastAPI |
| ML Framework | PyTorch / scikit-learn |
| Testing | pytest |
| Linting | ruff, mypy |
| Documentation | Markdown, MkDocs |
| Containerization | Docker |
| CI/CD | GitHub Actions |
