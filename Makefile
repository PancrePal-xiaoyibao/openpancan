# =============================================================================
# OpenPanCan – Makefile
# =============================================================================

.PHONY: help install start stop doctor clean

# ---------------------------------------------------------------------------
# Default target
# ---------------------------------------------------------------------------
help:
	@echo "OpenPanCan – Pancreatic Cancer Genomic Analysis System"
	@echo ""
	@echo "Usage:"
	@echo "  make install       Install all module dependencies with uv"
	@echo "  make start         Start all modules via the Gateway (port 8000)"
	@echo "  make doctor        Run health checks on all modules"
	@echo "  make stop           Stop all running gateway processes"
	@echo "  make clean          Remove temp files and outputs"
	@echo ""
	@echo "Individual modules:"
	@echo "  make vep            Start VEP service (port 8001)"
	@echo "  make rag            Start Phenotype RAG (port 8002)"
	@echo "  make phenotype      Start Phenotype Score (port 8003)"
	@echo "  make ppi            Start PPI Score (port 8004)"
	@echo "  make rank           Start Variant Rank (port 8005)"
	@echo "  make report-srv     Start Report service (port 8006)"
	@echo "  make system         Start PanCancerSystem (port 8007)"

# ---------------------------------------------------------------------------
# Install dependencies
# ---------------------------------------------------------------------------
install:
	@echo "=== Installing OpenPanCan dependencies ==="
	uv sync --project gateway
	uv sync --project pipeline
	uv sync --project doctor
	uv sync --project modules/vep_service
	uv sync --project modules/phenotype_rag
	uv sync --project modules/phenotype_score
	uv sync --project modules/ppi_score
	uv sync --project modules/variant_rank
	uv sync --project modules/report
	@echo "=== Dependencies installed ==="

# ---------------------------------------------------------------------------
# Start all modules via gateway
# ---------------------------------------------------------------------------
start:
	@echo "=== Starting OpenPanCan Gateway ==="
	uv run --project gateway -- uvicorn gateway.main:app --host 0.0.0.0 --port 8000

# ---------------------------------------------------------------------------
# Doctor health check
# ---------------------------------------------------------------------------
doctor:
	uv run --project doctor -- python doctor/main.py

# ---------------------------------------------------------------------------
# Individual module start commands
# ---------------------------------------------------------------------------
vep:
	uv run --project modules/vep_service -- uvicorn vep_service.api:app --host 0.0.0.0 --port 8001

rag:
	uv run --project modules/phenotype_rag -- uvicorn phenotype_rag.server:app --host 0.0.0.0 --port 8002

phenotype:
	uv run --project modules/phenotype_score -- uvicorn phenotype_score.api:app --host 0.0.0.0 --port 8003

ppi:
	uv run --project modules/ppi_score -- uvicorn ppi_score.api:app --host 0.0.0.0 --port 8004

rank:
	uv run --project modules/variant_rank -- uvicorn variant_rank.api:app --host 0.0.0.0 --port 8005

report-srv:
	uv run --project modules/report -- uvicorn report.api.main:app --host 0.0.0.0 --port 8006

system:
	uv run --project modules/PanCancerSystem -- uvicorn main:app --host 0.0.0.0 --port 8007

# ---------------------------------------------------------------------------
# Stop
# ---------------------------------------------------------------------------
stop:
	pkill -f "uvicorn gateway.main" || true
	pkill -f "uvicorn vep_service.api" || true
	pkill -f "uvicorn phenotype_rag.server" || true
	pkill -f "uvicorn phenotype_score.api" || true
	pkill -f "uvicorn ppi_score.api" || true
	pkill -f "uvicorn variant_rank.api" || true
	pkill -f "uvicorn report.api.main" || true
	pkill -f "uvicorn main:app" || true

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
clean:
	rm -rf temp_uploads outputs *.log *.db
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
