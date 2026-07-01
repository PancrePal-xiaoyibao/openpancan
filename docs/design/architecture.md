# OpenPanCan — System Architecture

> **Version**: 0.1.0  
> **Last Updated**: 2026-07-01

---

## 1. Overview

OpenPanCan is a **microservice-based genomic analysis platform** for pancreatic ductal adenocarcinoma (PDAC). It follows a 6-step pipeline architecture where each step is an independent HTTP service, orchestrated by a central Gateway.

### Design Principles

1. **Module Isolation** — Each module runs as an independent process with its own Python environment
2. **HTTP Communication** — All inter-module communication goes over HTTP (no shared memory or imports)
3. **Async Job Pattern** — Heavy computations run asynchronously with job ID polling
4. **Graceful Degradation** — Optional pipeline steps can fail without breaking the full flow
5. **Horizontal Scalability** — Modules can be scaled independently

---

## 2. System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │  React SPA  │    │  CLI Runner │    │  API Client │               │
│  │ (port 8007) │    │  pipeline/  │    │  curl/httpx │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTP
┌───────────────────────────────▼──────────────────────────────────────┐
│                        GATEWAY (port 8000)                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI + subprocess spawning + HTTP transparent proxy       │ │
│  │  /m/{module}/{path} → http://127.0.0.1:{port}/{path}          │ │
│  │  Health polling + graceful shutdown                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┬─────────────────┘
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────────┐
│8001 VEP │8002 RAG │8003 PHE │8004 PPI │8005 RNK │8006 RPT │8007 PanCan  │
│ Service │ Extract │  Score  │  Score  │  Rank   │ Report  │   System    │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────────┘
      │           │           │           │           │           │
      └───────────┴───────────┴───────────┴───────────┴───────────┘
                          DATA FLOW (6-STEP PIPELINE)
```

---

## 3. Module Specifications

### 3.1 Gateway (`gateway/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8000 |
| **Framework** | FastAPI |
| **Runtime** | `uv run --project gateway uvicorn gateway.main:app` |
| **Responsibility** | Spawn modules, route HTTP, health check |
| **Endpoints** | `/health`, `/pipeline/status`, `/m/{module}/{path}` |
| **State** | In-memory `_procs` dict + `_dead` set |

### 3.2 VEP Service (`modules/vep_service/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8001 |
| **Input** | VCF file upload |
| **Output** | Annotated CSV (VEP columns + COSMIC/TCGA/OncoKB) |
| **Pattern** | Async job (POST → job_id → poll → download) |
| **Dependencies** | pysam (for VCF parsing) |
| **Current State** | Mock VEP runner with deterministic output |

### 3.3 Phenotype RAG (`modules/phenotype_rag/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8002 |
| **Input** | Clinical notes (JSON) |
| **Output** | HPO IDs + cancer phenotype types |
| **Pattern** | Async job with rule-based + LLM fallback |
| **Dependencies** | Optional: faiss-cpu, sentence-transformers |
| **Current State** | Rule-based extraction (45 HPO terms hardcoded) |

### 3.4 Phenotype Score (`modules/phenotype_score/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8003 |
| **Input** | VEP CSV + HPO file |
| **Output** | Gene phenotype score CSV + variant score CSV |
| **Pattern** | Async job with file upload |
| **Dependencies** | pandas |
| **Current State** | Hardcoded gene scores (~20 genes) |

### 3.5 PPI Score (`modules/ppi_score/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8004 |
| **Input** | Gene CSV + VEP CSV + HPO IDs |
| **Output** | PPI network score CSV |
| **Pattern** | Async job with progress tracking |
| **Dependencies** | (planned: STRING DB loader) |
| **Current State** | Hardcoded 14-gene PPI dict |

### 3.6 Variant Rank (`modules/variant_rank/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8005 |
| **Input** | VEP CSV + gene score CSV + PPI CSV |
| **Output** | Ranked driver mutation CSV |
| **Pattern** | Async job with two-pass scoring |
| **Dependencies** | pandas, polars, duckdb |
| **Current State** | Full weighted theta scoring (best module) |

### 3.7 Report (`modules/report/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8006 |
| **Input** | Ranked CSV + HPO + clinical text |
| **Output** | Markdown report (PDF planned) |
| **Pattern** | SSE streaming (real-time progress) |
| **Dependencies** | sse-starlette |
| **Current State** | 18 drug recommendations, 16 clinical trials hardcoded |

### 3.8 PanCancerSystem (`modules/PanCancerSystem/`)

| Aspect | Specification |
|--------|---------------|
| **Port** | 8007 |
| **Backend** | FastAPI + SQLAlchemy (async SQLite) |
| **Frontend** | React + TypeScript + TailwindCSS |
| **Database** | CancerPatient, SomaticVariant, GermlineVariant, ACMGEvidence, AMPASCOCAPTier, TreatmentRecord, ClinicalReport |
| **API Routers** | 12 endpoints (patients, variants, ACMG, AMP/ASCO/CAP, treatment, trials, chat, report, settings) |
| **WebSocket** | `/api/chat/ws/{patient_id}` for real-time chat |
| **Docker** | Multi-stage build (Node → Python → nginx) |

---

## 4. Data Flow

### 4.1 6-Step Pipeline

```
Step 1 (optional): HPO_RAG
    Input:  symptom_text (clinical notes)
    Output: hpo_ids.txt, cancer_phenotypes.tsv
    Module: phenotype_rag (8002)

Step 2 (required): VEP
    Input:  vcf_path, hpo_ids, chromosomes
    Output: vep_output.csv (VEP + COSMIC/TCGA columns)
    Module: vep_service (8001)

Step 3 (optional): Phenotype
    Input:  vep_csv, hpo_file
    Output: gene_phenotype_score.csv, variant_phenotype_score.csv
    Module: phenotype_score (8003)

Step 4 (optional): PPI
    Input:  gene_csv, vep_csv, hpo_ids
    Output: ppi_score.csv
    Module: ppi_score (8004)

Step 5 (optional): Rank
    Input:  vep_csv, gene_csv, ppi_csv
    Output: ranked_output.csv
    Module: variant_rank (8005)

Step 6 (required): Report
    Input:  ranked_csv, hpo_file, symptom_text
    Output: report.md, report.pdf (PDF pending)
    Module: report (8006)
```

### 4.2 Async Job Pattern

All modules (except Report) use the same async job pattern:

```
1. Client POST /upload → Server returns {job_id: "xxx", status: "queued"}
2. Client polls GET /status/{job_id} → Server returns {status: "running", progress: 0.5}
3. Client polls until status = "completed"
4. Client downloads GET /files/{job_id}/{filename}
```

### 4.3 SSE Streaming (Report)

Report module uses Server-Sent Events for real-time updates:

```
1. Client POST /report/stream → Server opens SSE connection
2. Server sends events: {type: "phase", phase: "loading", progress: 0.1}
3. Server sends events: {type: "md", content: "...markdown chunk..."}
4. Server sends event: {type: "done", run_id: "xxx", pdf_url: "..."}
5. Connection closes
```

---

## 5. Database Schema

### PanCancerSystem SQLite Tables

```
CancerPatient
    id, name, age, sex, ethnicity, diagnosis, tumor_location, tumor_stage,
    tumor_grade, histology_type, biomarkers (JSON), treatment_history (JSON),
    hpo_terms (JSON), created_at, updated_at

SomaticVariant
    id, patient_id, chromosome, position, ref, alt, gene, variant_type,
    VAF, tumor_depth, normal_depth, cosmic_id, oncokb_level, is_cancer_hotspot,
    consequence, impact, hgvs_c, hgvs_p, clinvar_significance, ...

GermlineVariant
    id, patient_id, chromosome, position, ref, alt, gene, variant_type,
    consequence, gnomad_af, clinvar_significance, acmg_classification, ...

ACMGEvidence
    id, germline_variant_id, criterion, evidence_level, description, is_applied

AMPASCOCAPTier
    id, somatic_variant_id, tier (I/II/III/IV), evidence_category, confidence

TreatmentRecord
    id, patient_id, treatment_type, drug_name, regimen, response

ClinicalReport
    id, patient_id, report_type, markdown_path, pdf_path, created_at

VEPJob
    id, patient_id, job_id, status, vcf_path, output_csv_path
```

---

## 6. Deployment

### 6.1 Docker Compose

```yaml
services:
  app:
    build: modules/PanCancerSystem/docker/Dockerfile
    ports:
      - "8181:8181"  # nginx frontend
      - "8007:8007"  # backend API
    volumes:
      - ./data:/data
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/openpancan.db
```

### 6.2 Production Considerations

- Use PostgreSQL instead of SQLite
- Add Redis for job state persistence
- Add Prometheus + Grafana for monitoring
- Add JWT authentication
- Add rate limiting

---

## 7. Status Summary

| Component | Implementation | Data Integration | Tests |
|-----------|----------------|------------------|-------|
| Gateway | ✅ Complete | N/A | ❌ None |
| Pipeline Runner | ✅ Complete | N/A | ❌ None |
| VEP Service | ✅ API | ⚠️ Mock | ❌ None |
| Phenotype RAG | ✅ API | ⚠️ Stub | ❌ None |
| Phenotype Score | ✅ API | ⚠️ Stub | ❌ None |
| PPI Score | ✅ API | ⚠️ Stub | ❌ None |
| Variant Rank | ✅ Full | ⚠️ Stub | ❌ None |
| Report | ✅ SSE | ⚠️ Stub | ❌ None |
| PanCancerSystem Backend | ✅ Full | ⚠️ Stub | ❌ None |
| PanCancerSystem Frontend | ✅ Full | N/A | ❌ None |
| Docker | ✅ Complete | N/A | ❌ None |

**Legend**: ✅ = Production-ready code, ⚠️ = Functional with stub data, ❌ = Not implemented

---

## 8. Roadmap

See [DEVLOG.md](../DEVLOG.md) for detailed task breakdown and priorities.