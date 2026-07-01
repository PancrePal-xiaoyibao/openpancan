# OpenPanCan Gene Base

**AI-Powered Insight Platform for Pancreatic Cancer Genomics**

---

## Overview

OpenPanCan Gene Base is a comprehensive, open-source gene database designed to power AI-driven genomic analysis for pancreatic cancer research. It aggregates, curates, and structures gene-level information from multiple authoritative data sources, providing a unified foundation for machine learning models, clinical decision support tools, and research applications.

Pancreatic cancer remains one of the most lethal malignancies, with a five-year survival rate below 12%. Understanding the genomic landscape — the mutations, pathways, and biomarkers that drive tumorigenesis and influence treatment response — is critical to improving outcomes. OpenPanCan Gene Base aims to accelerate this understanding by making high-quality gene data accessible, interoperable, and AI-ready.

## Key Pancreatic Cancer Genes

The database centers on the most clinically and biologically significant genes implicated in pancreatic ductal adenocarcinoma (PDAC):

| Gene | Role in Pancreatic Cancer |
|------|---------------------------|
| **KRAS** | Oncogene; activating mutations in >90% of PDAC cases. The primary driver of pancreatic tumorigenesis. |
| **TP53** | Tumor suppressor; inactivated in ~75% of PDAC. Loss enables genomic instability and unchecked proliferation. |
| **SMAD4** | Tumor suppressor; deleted or mutated in ~55% of PDAC. Loss correlates with metastatic spread and poor prognosis. |
| **CDKN2A** | Tumor suppressor (p16); inactivated in >90% of PDAC. Loss disrupts cell cycle regulation. |
| **BRCA1** | DNA repair; germline mutations confer elevated PDAC risk. Predictive biomarker for PARP inhibitor therapy. |
| **BRCA2** | DNA repair; the most common hereditary PDAC predisposition gene. Guides platinum-based chemotherapy and PARP inhibitor use. |
| **PALB2** | DNA repair (Fanconi anemia pathway); mutations increase PDAC risk and predict PARP inhibitor sensitivity. |
| **ATM** | DNA damage response; mutations found in ~5% of familial PDAC. Potential therapeutic target. |
| **ARID1A** | Chromatin remodeling (SWI/SNF complex); mutations in ~8% of PDAC. Emerging therapeutic target. |
| **RNF43** | Wnt pathway regulator; mutated in ~6% of PDAC, particularly in the pancreaticobiliary subtype. |
| **STK11** | Tumor suppressor (LKB1); rare but clinically relevant mutations associated with KRAS-driven cancers. |
| **TGFBR2** | TGF-β signaling receptor; mutations in ~5% of PDAC with microsatellite instability. |
| **MAP2K4** | Stress-activated kinase; recurrently mutated in PDAC. Plays a role in JNK signaling. |
| **GNAS** | G-protein signaling; mutations characteristic of intraductal papillary mucinous neoplasms (IPMNs). |
| **KDM6A** | Histone demethylase; mutations in ~5% of PDAC. Epigenetic regulator with sex-biased effects. |
| **RBM10** | RNA-binding protein; recurrent mutations in PDAC. Involved in alternative splicing regulation. |
| **SF3B1** | Spliceosome component; mutations found in PDAC and associated with aberrant splicing patterns. |

## Data Sources

OpenPanCan Gene Base integrates data from the following authoritative sources:

| Source | Description |
|--------|-------------|
| **COSMIC** (Catalogue of Somatic Mutations in Cancer) | The world's largest and most comprehensive resource for somatic mutations in cancer. Provides mutation frequencies, functional impact predictions, and drug resistance data. |
| **TCGA-PAAD** (The Cancer Genome Atlas — Pancreatic Adenocarcinoma) | Multi-omic characterization of pancreatic cancer including whole-exome sequencing, RNA-seq, methylation, and clinical data from hundreds of patients. |
| **OncoKB** (Precision Oncology Knowledge Base) | MSKCC-curated knowledge base of oncogenic variants, their biological and clinical significance, and FDA-approved or investigational therapies. |
| **ClinVar** | NCBI's public archive of human genetic variants with clinical significance interpretations, including germline cancer predisposition variants. |
| **GTEx** (Genotype-Tissue Expression) | Comprehensive gene expression and eQTL data across normal human tissues, providing baseline expression context for pancreatic tissue. |

## Repository Structure

```
openpancan-gene-base/
├── README.md                    # This file — English (primary)
├── README_zh.md                 # Chinese (中文)
├── README_ja.md                 # Japanese (日本語)
├── README_ko.md                 # Korean (한국어)
├── README_fr.md                 # French (Français)
├── .gitignore                   # Git ignore rules
│
├── docs/
│   ├── design/                  # Architecture and design documents
│   │   └── README.md
│   ├── spec/                    # Technical specifications
│   │   └── README.md
│   ├── tasks/                   # Task breakdown and progress tracking
│   │   └── README.md
│   └── dev/                     # Development guides
│       └── README.md
│
├── data/                        # Gene data files (see .gitignore)
├── scripts/                     # Data processing and ETL scripts
└── models/                      # AI/ML model definitions and configurations
```

### Directory Purposes

- **docs/design/** — Architecture and system design documents. Describes the overall structure of the gene database, data models, entity relationships, API designs, and integration patterns. This is where high-level decisions about the platform are documented.

- **docs/spec/** — Technical specifications. Detailed, implementable specifications for each component: data schemas, field definitions, validation rules, ETL pipeline specifications, and API endpoint contracts.

- **docs/tasks/** — Task breakdown and progress tracking. Project management artifacts: milestone plans, sprint backlogs, feature roadmaps, and task completion status. Keeps the team aligned on what needs to be done.

- **docs/dev/** — Development guides. Onboarding documentation for new contributors: environment setup, coding standards, contribution workflows, testing guidelines, and common development procedures.

## Relationship to OpenRare

OpenPanCan Gene Base draws significant inspiration from **[OpenRare](https://github.com/rare-disease/openrare)** — an open-source platform for rare disease genomic analysis. OpenRare pioneered the approach of building community-maintained, structured gene databases for disease-specific domains. We acknowledge and thank the OpenRare community for establishing patterns and practices that guide this project.

While OpenRare addresses the rare disease domain broadly, OpenPanCan Gene Base specializes specifically in pancreatic cancer, tailoring data models, gene curation, and AI integration to the unique requirements of PDAC research.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- A GitHub account (for contributing)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-.git
cd openpancan-gene-base

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Explore the data
python scripts/explore.py
```

## Contributing

We welcome contributions from the pancreatic cancer research community, bioinformaticians, software engineers, and anyone passionate about improving outcomes for pancreatic cancer patients.

Please see [docs/dev/README.md](docs/dev/README.md) for contribution guidelines and development setup instructions.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Contact

- **Project Lead**: PancrePal / Xiaoyibao Team
- **GitHub Issues**: [Submit an issue](https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-/discussions)

---

*Together, we can transform pancreatic cancer from a death sentence into a manageable condition.*
