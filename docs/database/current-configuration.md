# OpenPanCan — Cancer Gene Database Configuration Reference

> **Status**: Database content is currently a curated stub. The **integration interfaces** are stable; only the data sources need to be swapped in.

This document describes what database data each module currently uses, where it lives in the code, and the precise env-var/path configuration.

---

## 1. Module → Database Mapping

| Module | Database(s) | Source File | Config Env Vars |
|--------|-------------|-------------|-----------------|
| `vep_service` | COSMIC CGC, TCGA-PAAD, OncoKB, ClinVar, KRAS hotspots | `modules/vep_service/src/vep_service/cancer_annotation.py` | `VEP_CACHE_DIR`, `VEP_FASTA_FILE`, `VEP_ASSEMBLY`, `COSMIC_DATA_DIR`, `TCGA_DATA_DIR`, `VEP_PLUGINS` |
| `phenotype_rag` | HPO, cancer phenotype terms | `modules/phenotype_rag/src/phenotype_rag/pipeline.py` | `LLM_API_KEY`, `LLM_API_BASE_URL`, `HPO_DATA_DIR` |
| `phenotype_score` | COSMIC CGC, TCGA-PAAD freq, gene-phenotype map | `modules/phenotype_score/src/phenotype_score/cancer_scoring.py` | `TCGA_DATA_DIR`, `COSMIC_DATA_DIR` |
| `ppi_score` | STRING DB, BioGRID, GTEx, DepMap | `modules/ppi_score/src/ppi_score/cancer_ppi.py` | `PPI_DB_PATH`, `STRING_DB_DIR`, `GTEx_DATA_DIR`, `DEPMAP_DATA_DIR` |
| `variant_rank` | COSMIC hotspots, OncoKB, TCGA, ClinVar, ACMG | `modules/variant_rank/src/variant_rank/{cancer_driver_rank,somatic_scoring}.py` | `ONCOKB_API_KEY`, `VEP_OUTPUT_CACHE_DIR` |
| `report` | Drug recommendations, clinical trials | `modules/report/src/report/report/{drug_recommendations,clinical_trials}.py` | `DGIDB_API_KEY`, `CLINICALTRIALS_API_KEY` |
| `PanCancerSystem` | Internal SQLite (`openpancan.db`) + all of the above via HTTP | `modules/PanCancerSystem/backend/database/models.py` | `DATABASE_URL`, `SECRET_KEY` |

---

## 2. Currently Bundled (Stub) Data

| Constant | File | Entries | Source in Real World |
|----------|------|---------|----------------------|
| `PANCREATIC_CANCER_DRIVER_GENES` | cancer_annotation.py:20 | 14 genes | COSMIC Cancer Gene Census |
| `KRAS_HOTSPOT_MUTATIONS` | cancer_annotation.py:39 | ~10 hotspots | COSMIC mutation dataset |
| `COSMIC_CANCER_GENE_CENSUS` | cancer_annotation.py | ~20 genes | COSMIC CGC export |
| `TCGA_PAAD_FREQUENCIES` | cancer_annotation.py | ~20 gene freqs | TCGA PAAD MAF |
| `_ONCOKB_LEVEL_MAP` | cancer_annotation.py | ~10 entries | OncoKB API |
| `CANCER_HOTSPOT_DB` | somatic_scoring.py:20 | ~25 hotspots | COSMIC mutation dataset |
| `PANCREATIC_CANCER_PPI` | cancer_ppi.py:26 | 14 genes, ~80 interactions | STRING DB v12 |
| `PANCREATIC_CANCER_HPO_TERMS` | pipeline.py:23 | ~45 HPO terms | HPO ontology (16k terms) |
| `GENE_PHENOTYPE_BASE_SCORES` | cancer_scoring.py | ~20 gene scores | COSMIC + literature |
| `DRUG_RECOMMENDATIONS` | drug_recommendations.py | 18 drug entries | DGIdb + NCCN guidelines |
| `PANCREATIC_CLINICAL_TRIALS` | clinical_trials.py | 16 trial entries | ClinicalTrials.gov |

---

## 3. Environment Configuration

```bash
# In .env (copy from .env.example first)

# === LLM API (Phenotype RAG) ===
LLM_API_KEY=sk-...your-groq-or-openai-key...
LLM_API_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL_NAME=llama-3.1-70b-versatile

# === OncoKB API (variant_rank) ===
ONCOKB_API_KEY=your-oncokb-token

# === PubMed (literature search) ===
PUBMED_API_KEY=your-ncbi-key

# === Reference Data Directories ===
VEP_CACHE_DIR=./reference_data/vep_cache
VEP_FASTA_FILE=./reference_data/vep_cache/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
VEP_ASSEMBLY=GRCh38
COSMIC_DATA_DIR=./reference_data/cosmic
TCGA_DATA_DIR=./reference_data/tcga
GTEx_DATA_DIR=./reference_data/gtex
HPO_DATA_DIR=./reference_data/hpo
STRING_DB_DIR=./reference_data/string
DEPMAP_DATA_DIR=./reference_data/depmap

# === PanCancerSystem Database ===
DATABASE_URL=sqlite+aiosqlite:///./openpancan.db
# For PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/openpancan

SECRET_KEY=replace-with-a-long-random-string
```

---

## 4. Module-Specific Configuration Files

### 4.1 vep_service (`modules/vep_service/src/vep_service/config.py`)

```python
class Settings:
    VEP_CACHE_DIR: str          # VEP reference data (e.g., FASTA, gff)
    VEP_FASTA_FILE: str         # Path to reference genome
    VEP_ASSEMBLY: str           # "GRCh38" or "GRCh37"
    VEP_FORK: int               # Parallel workers (default: 8)
    VEP_PLUGINS: str            # Comma-separated: "COSMIC,OncoKB,ClinVar"
    COSMIC_DATA_DIR: str        # COSMIC vcf/tab files
    TCGA_DATA_DIR: str          # TCGA MAF files
    UPLOAD_DIR: str             # Where uploaded VCFs go
    OUTPUT_DIR: str             # Where annotated CSVs go
```

### 4.2 phenotype_rag (`modules/phenotype_rag/src/phenotype_rag/config.py`)

```python
class Settings:
    LLM_API_KEY: str
    LLM_API_BASE_URL: str
    LLM_MODEL_NAME: str
    EMBEDDING_MODEL_NAME: str   # default: "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
    FAISS_INDEX_PATH: str       # cached vector DB
    HPO_DATA_DIR: str           # hp.obo + phenotype.hpoa
    PROMPTS_FILE: str           # cancer_prompts.json
    SIMILARITY_THRESHOLD: float # default: 0.65
    MAX_RESULTS: int            # default: 10
```

### 4.3 ppi_score (`modules/ppi_score/src/ppi_score/config.py`)

```python
class Settings:
    PPI_DB_PATH: str            # STRING protein.links.detailed.v12.0.txt.gz
    STRING_DB_DIR: str          # Unzipped STRING files
    GTEx_DATA_DIR: str          # GTEx median TPM by gene
    DEPMAP_DATA_DIR: str        # CRISPRGeneEffect.csv
    HPO_DATA_DIR: str
    SOURCE_WEIGHTS: dict        # {string: 0.4, biogrid: 0.3, ...}
    T_GTEX_TPM_CUTOFF: float
    T_TAU_CUTOFF: float
    T_TOP_N_EXPR: int
```

### 4.4 variant_rank (`modules/variant_rank/src/variant_rank/config.py`)

```python
class Settings:
    PANCREATIC_CANCER_DRIVER_THETA: dict   # weighted feature vector
    KRAS_HOTSPOT_MUTATIONS: dict
    PANCREATIC_CANCER_GERMLINE_PREDISPOSITION: dict
    HOTSPOT_THERAPIES: dict                # mutation -> drug list
```

### 4.5 PanCancerSystem (`modules/PanCancerSystem/backend/config.py`)

```python
class Settings:
    DATABASE_URL: str            # sqlite+aiosqlite:///./openpancan.db
    SECRET_KEY: str              # JWT signing
    ALGORITHM: str               # "HS256"
    VEP_API_BASE_URL: str        # http://localhost:8001
    PHENOTYPE_RAG_API_BASE_URL: str
    PHENOTYPE_SCORE_API_BASE_URL: str
    PPI_SCORE_API_BASE_URL: str
    VARIANT_RANK_API_BASE_URL: str
    REPORT_API_BASE_URL: str
    LLM_API_KEY: str
    LLM_API_BASE_URL: str
    LLM_MODEL_NAME: str
    ONCOKB_API_KEY: str
    CORS_ORIGINS: list[str]
    UPLOAD_DIR: str
    MAX_UPLOAD_SIZE: int         # bytes
```

---

## 5. Reference Data Directory Layout

Expected layout (create once, all modules read from these paths):

```
reference_data/
├── vep_cache/
│   ├── Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
│   ├── Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz.fai
│   └── Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz.gzi
├── cosmic/
│   ├── CosmicMutantExportCensus.tsv.gz
│   ├── CosmicCancerGeneCensus.tsv
│   └── CosmicMutationData.tsv.gz
├── tcga/
│   └── tcga_paad_mc3_public.tsv
├── gtex/
│   ├── GTEx_Analysis_v11_RSEMv1.3.3_gene_median_tpm.gct.gz
│   └── rna_tissue_consensus.tsv
├── hpo/
│   ├── hp.obo
│   ├── phenotype.hpoa
│   └── genes_to_disease.txt
├── string/
│   ├── 9606.protein.links.detailed.v12.0.txt.gz
│   └── 9606.protein.info.v12.0.txt.gz
├── depmap/
│   ├── CRISPRGeneEffect.csv
│   └── Model.csv
├── hgnc/
│   └── hgnc_complete_set.txt
├── reactome/
│   ├── Ensembl2Reactome.txt
│   └── ReactomePathwaysRelation.txt
└── clinvar/
    └── variant_summary.txt.gz
```

---

## 6. Status Indicators

The data integration is **two-layer**:

1. **Data Access Layer (DAL)** — *implemented* ✅
   - Pydantic models for all entities
   - Settings/env-var system
   - Pydantic schemas for API I/O
   - File path resolution

2. **Data Loading Layer** — *stub* ⚠️
   - All hardcoded constants
   - No file loaders
   - No API clients (OncoKB, ClinicalTrials.gov)

The DAL is production-quality and ready. Replacing the loading layer does **not** require changes to:
- API contracts
- Scoring algorithms
- Pipeline orchestration
- Frontend types
- Database schema

See `docs/database/integration-guide.md` for step-by-step instructions on wiring real data.
