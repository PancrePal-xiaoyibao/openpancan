# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-01

### Added
- Initial project scaffold: 7 microservice modules + Gateway + Pipeline Runner + Doctor CLI
- **Gateway** (port 8000): subprocess orchestrator with HTTP transparent dispatch
- **Pipeline Runner**: 6-step cancer genomics pipeline (HPO_RAG → VEP → Phenotype → PPI → Rank → Report)
- **VEP Service** (port 8001): VCF annotation + cancer-specific enrichment (COSMIC/TCGA/OncoKB)
- **Phenotype RAG** (port 8002): LLM-based cancer phenotype extraction from clinical notes
- **Phenotype Score** (port 8003): Cancer gene scoring via COSMIC Census + TCGA frequencies
- **PPI Score** (port 8004): Pancreatic cancer pathway PPI network scoring
- **Variant Rank** (port 8005): Cancer driver mutation ranking (somatic + germline)
- **Report** (port 8006): Pancreatic cancer genomic report generation (SSE streaming)
- **PanCancerSystem** (port 8007): Full-stack web app (React + FastAPI + SQLite)
- Docker multi-stage builds (production + development)
- Documentation: README (EN/ZH), DEVLOG, glossary, database config guide
- Gene Base repository: 5-language READMEs (EN/ZH/JA/KO/FR), docs structure

### Infrastructure
- uv-based dependency management (PEP 621 pyproject.toml across all modules)
- hatchling build backend
- Makefile with install/start/doctor/stop targets
- .env.example with all configuration variables
- .gitignore covering Python, Node, Docker, data files

### Acknowledgment
- Architecture inspired by [OpenRare](https://github.com/OpenRare2026/OpenRare) (open-source rare disease genomic analysis system)
