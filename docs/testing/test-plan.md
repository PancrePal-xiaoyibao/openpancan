# OpenPanCan — Real Integration Test Plan

> **Target runtime**: deepseek v4 flash compatible  
> **Approach**: pytest + httpx + pytest-asyncio + real process spawning

This test plan covers every module with a real end-to-end test strategy that a coding assistant can implement without guessing.

---

## 1. Test Infrastructure

### 1.1 Dependencies (`tests/requirements.txt` or `pyproject.toml` [dependency-groups.test])

```toml
[dependency-groups]
test = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "pytest-mock>=3.14",
]
```

### 1.2 Directory Structure

```
tests/
├── conftest.py                    # shared fixtures
├── integration/
│   ├── conftest.py               # gateway + module process spawning
│   ├── test_pipeline.py          # 6-step end-to-end
│   ├── test_gateway.py           # dispatch, health, lifespan
│   └── test_doctor.py            # health check CLI
├── unit/
│   ├── conftest.py
│   ├── test_cancer_annotation.py
│   ├── test_cancer_driver_rank.py
│   ├── test_cancer_scoring.py
│   ├── test_cancer_ppi.py
│   └── test_somatic_scoring.py
├── fixtures/
│   ├── sample.vcf                # 10-variant minimal VCF
│   ├── hpo_terms.txt             # 5 HPO IDs
│   ├── clinical_notes.txt        # sample clinical text
│   └── ranked_output.csv         # expected ranked output
└── utils/
    └── helpers.py                 # test utilities
```

---

## 2. Unit Tests

### 2.1 `test_cancer_annotation.py`

**Module**: `vep_service.cancer_annotation`

```python
# Test cases (pytest)
def test_pancreatic_driver_genes_contains_kras():
    assert "KRAS" in PANCREATIC_CANCER_DRIVER_GENES

def test_kras_hotspot_mutations_complete():
    assert "G12D" in KRAS_HOTSPOT_MUTATIONS
    assert KRAS_HOTSPOT_MUTATIONS["G12D"]["oncokb_level"] == 1

def test_add_cancer_annotations_adds_cosmic_column():
    df = pd.DataFrame({"SYMBOL": ["KRAS"], "HGVS_P": ["p.G12D"]})
    result = add_cancer_annotations(df)
    assert "cosmic_id" in result.columns
    assert result.iloc[0]["is_cancer_hotspot"] == True

def test_add_cancer_annotations_non_driver_gene():
    df = pd.DataFrame({"SYMBOL": ["BRCA1"], "HGVS_P": ["p.V600E"]})
    result = add_cancer_annotations(df)
    assert result.iloc[0]["is_cancer_hotspot"] == False
```

### 2.2 `test_cancer_driver_rank.py`

**Module**: `variant_rank.cancer_driver_rank`

```python
def test_score_clinvar_significance():
    ranker = CancerDriverRanker()
    assert ranker.score_clinvar_significance("Pathogenic") == 5.0
    assert ranker.score_clinvar_significance("Benign") == -5.0

def test_score_vaf_clonal():
    ranker = CancerDriverRanker()
    # VAF 0.4 is in the "clonal" range (0.3-0.6)
    assert ranker.score_vaf(0.4) > 0

def test_two_pass_scoring():
    ranker = CancerDriverRanker()
    df = pd.DataFrame({
        "SYMBOL": ["KRAS", "TP53"],
        "clinvar_significance": ["Pathogenic", "Pathogenic"],
        "consequence": ["missense_variant", "missense_variant"],
        "VAF": [0.35, 0.40],
        "is_cancer_hotspot": [True, False],
        "cosmic_id": ["COSM521", "COSM442"],
    })
    scored = ranker.score_variants(df)
    ranked = ranker.rank_variants(scored)
    assert "driver_score" in ranked.columns
    assert ranked.iloc[0]["SYMBOL"] == "KRAS"  # should rank first

def test_theta_weights_sum_to_one():
    ranker = CancerDriverRanker()
    total = sum(ranker.theta.values())
    assert abs(total - 1.0) < 0.01
```

### 2.3 `test_cancer_scoring.py`

**Module**: `phenotype_score.cancer_scoring`

```python
def test_gene_phenotype_score_kras():
    scorer = CancerPhenotypeScorer()
    score = scorer.score_gene_phenotype("KRAS", {})
    assert score > 0.5  # KRAS should score high

def test_variant_phenotype_score_hotspot():
    scorer = CancerPhenotypeScorer()
    score = scorer.score_variant_phenotype(pd.Series({
        "is_cancer_hotspot": True,
        "impact": "HIGH",
    }))
    assert score > 0

def test_score_gene_phenotype_unknown_gene():
    scorer = CancerPhenotypeScorer()
    score = scorer.score_gene_phenotype("UNKNOWN_GENE_XYZ", {})
    assert 0 <= score <= 1.0
```

### 2.4 `test_cancer_ppi.py`

**Module**: `ppi_score.cancer_ppi`

```python
def test_kras_ppi_score_high():
    scorer = CancerPPIScorer()
    score = scorer.compute_ppi_score("KRAS", {"TP53": 1.0, "SMAD4": 1.0})
    assert score > 0

def test_non_pathway_gene_low_score():
    scorer = CancerPPIScorer()
    score = scorer.compute_ppi_score("UNKNOWN_GENE", {})
    assert score == 0.0

def test_network_returns_dataframe():
    scorer = CancerPPIScorer()
    df = scorer.score_interaction_network("KRAS")
    assert "gene" in df.columns
    assert "score" in df.columns
```

---

## 3. Integration Tests (Process-Based)

### 3.1 `test_gateway.py`

**Strategy**: Spawn the gateway as a subprocess, send HTTP requests.

```python
import subprocess
import time
import httpx
import pytest

GATEWAY_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def gateway_process():
    """Start the gateway once per test session."""
    proc = subprocess.Popen(
        ["uv", "run", "--project", "gateway", "--", "uvicorn", "gateway.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for health
    for _ in range(60):
        try:
            if httpx.get(f"{GATEWAY_URL}/health", timeout=3).status_code == 200:
                yield proc
                break
        except httpx.ConnectError:
            time.sleep(1)
    else:
        pytest.fail("Gateway did not start")
    proc.terminate()
    proc.wait()

def test_health_endpoint(gateway_process):
    resp = httpx.get(f"{GATEWAY_URL}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"

def test_dispatch_to_vep(gateway_process):
    resp = httpx.get(f"{GATEWAY_URL}/m/vep_service/health")
    assert resp.status_code == 200

def test_dispatch_unknown_module(gateway_process):
    resp = httpx.get(f"{GATEWAY_URL}/m/nonexistent/health")
    assert resp.status_code == 404

def test_dispatch_down_module(gateway_process):
    resp = httpx.get(f"{GATEWAY_URL}/m/phenotype_rag/health")
    # May be 503 if module failed to start
    assert resp.status_code in (200, 503)

def test_pipeline_status(gateway_process):
    resp = httpx.get(f"{GATEWAY_URL}/pipeline/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "vep_service" in body
    assert "report" in body
```

### 3.2 `test_pipeline.py`

**Strategy**: Run the full 6-step pipeline against real module APIs (running in test mode).

```python
import asyncio
import httpx
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.mark.asyncio
async def test_step_hpo_rag():
    """Step 1: Clinical text → HPO IDs"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://127.0.0.1:8002/api/v1/extract",
            json={"notes": [{"patient_id": "1", "clinical_note": "Patient with pancreatic ductal adenocarcinoma, KRAS mutation positive, stage III"}]},
        )
    assert resp.status_code == 202
    body = resp.json()
    assert "job_id" in body

@pytest.mark.asyncio
async def test_step_vep_upload():
    """Step 2: VCF upload → annotated CSV"""
    vcf_path = FIXTURES / "sample.vcf"
    with open(vcf_path, "rb") as f:
        resp = await httpx.AsyncClient().post(
            "http://127.0.0.1:8001/run-upload",
            files={"file": ("sample.vcf", f, "text/plain")},
            data={"hgvs": "true", "fork": "2"},
        )
    assert resp.status_code == 202
    assert "job_id" in resp.json()

@pytest.mark.asyncio
async def test_full_pipeline_smoke():
    """End-to-end: submit VCF + text, verify all 6 steps complete"""
    artifacts = asyncio.run(run_pipeline(
        vcf_path=str(FIXTURES / "sample.vcf"),
        symptom_text="Pancreatic ductal adenocarcinoma, KRAS G12D mutation, stage III",
        output_dir="test_outputs",
    ))
    assert Path(artifacts["vep_csv"]).exists()
    assert Path(artifacts["report_md"]).exists()
```

---

## 4. Test Execution Order

```bash
# 1. Unit tests (fast, no processes needed)
pytest tests/unit/ -v

# 2. Integration tests (need modules running)
pytest tests/integration/ -v --timeout=300

# 3. Full pipeline test (needs all 7 modules)
pytest tests/integration/test_pipeline.py -v --timeout=600

# 4. All tests
pytest tests/ -v --timeout=600
```

## 5. CI Integration (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-groups
      - run: pytest tests/ -v --timeout=600
```

## 6. Current Blockers

The following bugs (identified in code review) must be fixed before tests can pass:

| Bug | File | Fix |
|-----|------|-----|
| 7 × 204 status code assertion | PanCancerSystem `api/*.py` | Add `response_class=Response` |
| String-vs-float comparison | `vep_runner.py` | Cast `_simulate_polyphen` return to float |
| Column name mismatch | `variant_rank/api.py` | `"score"` → `"phenotype_score"` |
| PPI filename mismatch | `ppi_score/api.py` + `pipeline/runner.py` | Standardize on `ppi_score.csv` |
| FE/BE field name mismatch | `PanCancerSystem/frontend/src/types/index.ts` | Align with backend DTOs |
