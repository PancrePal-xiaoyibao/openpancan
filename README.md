# OpenPanCan – Pancreatic Cancer Genomic Analysis System

> **Empowering precision oncology through open-source genomic analysis**

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**[English](README.md)** | **[中文](README_zh.md)** | **[日本語](docs/gene-base/README_ja.md)** | **[한국어](docs/gene-base/README_ko.md)** | **[Français](docs/gene-base/README_fr.md)**

---

OpenPanCan is an open-source, microservice-based genomic analysis platform purpose-built for pancreatic ductal adenocarcinoma (PDAC) research and clinical decision support. It processes somatic and germline variant data through a 6-step pipeline — from phenotype extraction to clinical report generation — and provides a full-stack web application for cancer patient management.

**OpenPanCan was inspired by and builds upon the architecture of [OpenRare](https://github.com/OpenRare2026/OpenRare), the open-source rare disease genomic analysis system. We gratefully acknowledge the OpenRare team for their pioneering work in open-source clinical genomics.**

---

## 🔬 Key Features

- **6-Step Cancer Genomics Pipeline**: Automated processing from VCF to clinical report
- **Cancer-Specific Variant Annotation**: VEP with COSMIC, TCGA, OncoKB enrichment
- **Cancer Driver Mutation Ranking**: Somatic (VAF, hotspot, COSMIC) + Germline (ACMG) scoring
- **Pancreatic Cancer Signaling Principle**: analyze upstream RTK/ERBB-MET-FGFR activation, downstream MAPK/PI3K-AKT-mTOR cascade reactivation, and lateral escape routes such as MYC amplification and invasion/metastasis modules
- **Targeted Therapy Recommendations**: PARP inhibitors, KRAS inhibitors, immunotherapy matching
- **Clinical Trial Matching**: Pancreatic cancer-specific trial search
- **Full-Stack Web Application**: React + TypeScript frontend with bilingual (EN/ZH) support

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gateway (Port 8000)                       │
│                 FastAPI HTTP Proxy                           │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┐───────┘
      │       │       │       │       │       │       │
   8001    8002    8003    8004    8005    8006    8007
   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴──────┐
   │VEP│   │RAG│   │PHE│   │PPI│   │RNK│   │RPT│   │PanCan  │
   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   │System  │
                                                      │(WebApp)│
                                                      └────────┘
```

### Modules

| Module | Port | Description |
|--------|------|-------------|
| **vep_service** | 8001 | VEP annotation + COSMIC/TCGA cancer enrichment |
| **phenotype_rag** | 8002 | LLM-based cancer phenotype extraction from clinical notes |
| **phenotype_score** | 8003 | Cancer gene scoring via COSMIC Census + TCGA frequencies |
| **ppi_score** | 8004 | Pancreatic cancer pathway PPI network scoring |
| **variant_rank** | 8005 | Cancer driver mutation ranking (somatic + germline) |
| **report** | 8006 | Pancreatic cancer genomic report generation (SSE streaming) |
| **PanCancerSystem** | 8007 | Full-stack web app (React + FastAPI) |

### Data Flow Pipeline

```
Clinical Text ──> [phenotype_rag] ──> HPO IDs + Cancer Phenotypes
VCF File ──> [vep_service] ──> Annotated CSV (COSMIC/TCGA fields)
HPO + Annotated CSV ──> [phenotype_score] ──> Gene/Variant Cancer Scores
Gene Score + VEP CSV + HPO ──> [ppi_score] ──> Cancer Pathway PPI Score
VEP CSV + Gene Score + PPI Score ──> [variant_rank] ──> Driver Mutation Ranked CSV
Ranked CSV + HPO + Clinical ──> [report] ──> Clinical Report (MD + PDF)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** >= 3.12
- **uv** (Python package manager) – `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **VEP** (optional, for VCF annotation) – Ensembl Variant Effect Predictor
- **Node.js** >= 20 (for frontend)

### Installation

```bash
# Clone the repository
git clone https://github.com/PancrePal-xiaoyibao/OpenPanCan.git
cd OpenPanCan

# Copy and edit environment configuration
cp .env.example .env

# Install all module dependencies
make install
```

### Running

```bash
# Start all modules via the Gateway
make start

# Or run individual modules
make vep         # VEP service on port 8001
make rag         # Phenotype RAG on port 8002
make phenotype   # Phenotype Score on port 8003
make ppi         # PPI Score on port 8004
make rank        # Variant Rank on port 8005
make report-srv  # Report service on port 8006
make system      # PanCancerSystem on port 8007
```

### Running the Full Pipeline

```bash
uv run --project pipeline -- python pipeline/main.py \
    -v path/to/input.vcf \
    -t "Patient with pancreatic ductal adenocarcinoma, stage III..."
```

### Health Check

```bash
make doctor
```

---

## 🧬 Cancer-Specific Gene Databases

OpenPanCan uses the following cancer-specific gene databases (replacing OpenRare's rare-disease-specific databases):

| Database | Purpose | Rare → Cancer Replacement |
|----------|---------|---------------------------|
| **COSMIC** | Cancer Gene Census, mutation frequencies | Replaces Orphanet/OMIM |
| **TCGA-PAAD** | Pancreatic adenocarcinoma mutation data | Replaces MONDO rare subset |
| **OncoKB** | Cancer gene oncogenic annotations | Replaces PanelApp panels |
| **Cancer Hotspot DB** | Known cancer driver mutations | New cancer-specific |
| **ClinVar** | Clinical variant significance | Retained (general) |
| **STRING DB** | Protein-protein interaction network | Retained (general) |
| **GTEx** | Tissue-specific gene expression | Retained (general) |
| **Reactome** | Biological pathway data | Retained (general) |
| **HPO** | Human Phenotype Ontology | Retained (general) |

For the curated pancreatic cancer gene database, see: [OpenPanCan Gene Base](https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-)

---

## 📚 Documentation

- **[Database Configuration](docs/database/current-configuration.md)** — Current stub data status + env vars
- **[Database Integration Guide](docs/database/integration-guide.md)** — Step-by-step real data wiring
- **[Testing Plan](docs/testing/test-plan.md)** — Unit + integration test strategy
- **[Gene Base](docs/gene-base/)** — Curated pancreatic cancer gene database (5 languages)
- **[Development Log](DEVLOG.md)** — Project completion status + roadmap
- **[API Reference](http://localhost:8000/docs)** — Interactive API docs (when Gateway running)
- **[Architecture Design](docs/design/)** — System architecture documentation

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🙏 Acknowledgments

**OpenPanCan is built upon the architecture of [OpenRare](https://github.com/OpenRare2026/OpenRare)** – the pioneering open-source rare disease genomic analysis system. The microservice architecture, HTTP-based module communication pattern, async job queue design, and pipeline orchestration approach are adapted from OpenRare's excellent engineering foundation. We are deeply grateful to the OpenRare team for their vision and open-source contribution that inspired and enabled this project.

---

## 📖 Glossary

| Term | Full Name | What It Means |
|------|-----------|---------------|
| **VCF** | Variant Call Format | The standard file format for storing genetic variant data — think of it as a spreadsheet of DNA changes found in a patient's genome |
| **VEP** | Variant Effect Predictor | A tool from Ensembl that annotates each variant with what it does — whether it changes a protein, where it falls in a gene, and how severe it might be |
| **HPO** | Human Phenotype Ontology | A standardized vocabulary of clinical symptoms and physical traits, used to describe a patient's presentation in computable form |
| **COSMIC** | Catalogue Of Somatic Mutations In Cancer | The world's largest database of mutations found in human cancers — tells us which mutations are known cancer drivers |
| **TCGA** | The Cancer Genome Atlas | A landmark cancer genomics program that sequenced over 20,000 tumors across 33 cancer types, including pancreatic adenocarcinoma (PAAD) |
| **OncoKB** | Oncology Knowledge Base | A precision oncology database from MSKCC that classifies cancer mutations by their clinical actionability (Level 1–4) |
| **PPI** | Protein–Protein Interaction | A network map of how proteins physically connect and communicate inside cells — helps identify key genes in cancer pathways |
| **GTEx** | Genotype-Tissue Expression | A database cataloging which genes are turned on (expressed) in different human tissues, including the pancreas |
| **ACMG** | American College of Medical Genetics | Publishes the standard guidelines for classifying germline (inherited) genetic variants as Pathogenic, Benign, or VUS (Variant of Uncertain Significance) |
| **AMP/ASCO/CAP** | Association for Molecular Pathology / American Society of Clinical Oncology / College of American Pathologists | Joint guidelines for classifying somatic (tumor-acquired) variants into four tiers based on clinical significance |
| **VAF** | Variant Allele Frequency | The percentage of DNA reads at a position that carry the mutation — helps distinguish true somatic drivers from sequencing noise |
| **SNV / INDEL** | Single Nucleotide Variant / Insertion-Deletion | The two most common types of small genetic changes: a single letter swap (SNV) or a short insertion/deletion (INDEL) |
| **PDAC** | Pancreatic Ductal Adenocarcinoma | The most common and deadliest form of pancreatic cancer, accounting for ~90% of cases |
| **SSE** | Server-Sent Events | A web technology for streaming real-time updates from server to browser — used by the report module to show live generation progress |

In short: OpenPanCan takes a **VCF** file of patient variants, runs them through **VEP** for annotation, enriches with **COSMIC/TCGA/OncoKB** cancer data, scores against **HPO** phenotypes and **PPI** cancer pathways, ranks driver mutations using **VAF** and **ACMG/AMP** guidelines, and delivers a clinical report for **PDAC** via **SSE** streaming.

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.
