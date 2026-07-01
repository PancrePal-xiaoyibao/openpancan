# OpenPanCan — Real Gene Database Integration Guide

> **Goal**: Replace every hardcoded stub constant with real data from authoritative sources.

This guide is written to be **directly executable** by both humans and AI coding assistants (e.g. DeepSeek v4 Flash). Each section gives: the target file, what to replace, where to download real data from, and a drop-in code template.

---

## Phase 1: COSMIC Cancer Gene Census

**Replace**: `modules/vep_service/src/vep_service/cancer_annotation.py` → `COSMIC_CANCER_GENE_CENSUS` (lines 87-179)

**Source**: https://cancer.sanger.ac.uk/cosmic/download
- File: `Cosmic_CancerGeneCensus_Tier1.tsv` (free tier) or full CGC export
- License: Academic use only (registration required for some files)

**Drop-in replacement**:

```python
# modules/vep_service/src/vep_service/data_loaders/cosmic_cgc.py

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

from vep_service.config import settings

logger = logging.getLogger(__name__)

_CGC_CACHE: dict[str, dict[str, Any]] | None = None


def _load_cgc_from_file() -> dict[str, dict[str, Any]]:
    """Load COSMIC Cancer Gene Census from local TSV."""
    path = Path(settings.COSMIC_DATA_DIR) / "CosmicCancerGeneCensus.tsv"
    if not path.exists():
        logger.warning("CGC file not found at %s — falling back to empty dict", path)
        return {}

    df = pd.read_csv(path, sep="\t")
    # Expected columns: GENE_SYMBOL, ROLE, TIER, SYNONYMS, HALLMARK, SOMATIC, GERMLINE
    out: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        symbol = str(row["GENE_SYMBOL"]).upper()
        out[symbol] = {
            "role": row.get("ROLE", ""),
            "tier": int(row.get("TIER", 0)) if pd.notna(row.get("TIER")) else 0,
            "synonyms": str(row.get("SYNONYMS", "")).split(";"),
            "is_hallmark": bool(row.get("HALLMARK", False)),
        }
    return out


def get_cosmic_cgc() -> dict[str, dict[str, Any]]:
    """Get COSMIC CGC, with lazy load + module-level cache."""
    global _CGC_CACHE
    if _CGC_CACHE is None:
        _CGC_CACHE = _load_cgc_from_file()
    return _CGC_CACHE
```

Then in `cancer_annotation.py`:
```python
# DELETE the hardcoded COSMIC_CANCER_GENE_CENSUS dict
# REPLACE all lookups with:
from vep_service.data_loaders.cosmic_cgc import get_cosmic_cgc

def get_gene_role(gene_symbol: str) -> str:
    return get_cosmic_cgc().get(gene_symbol.upper(), {}).get("role", "unknown")
```

**Verification**:
```python
assert len(get_cosmic_cgc()) > 500  # real CGC has ~700 genes
assert get_cosmic_cgc()["KRAS"]["role"] == "oncogene"
```

---

## Phase 2: TCGA-PAAD Mutation Frequencies

**Replace**: `cancer_annotation.py` → `TCGA_PAAD_FREQUENCIES`

**Source**: GDC Data Portal (https://portal.gdc.cancer.gov)
- Project: TCGA-PAAD
- File type: Mutect2 MAF (masked somatic mutations)
- Recommended: download via GDC Data Transfer Tool

**Drop-in replacement**:

```python
# modules/vep_service/src/vep_service/data_loaders/tcga_paad.py

import logging
from pathlib import Path

import pandas as pd

from vep_service.config import settings

logger = logging.getLogger(__name__)
_TCGA_CACHE: dict[str, float] | None = None


def _compute_tcga_paad_freq() -> dict[str, float]:
    maf_path = Path(settings.TCGA_DATA_DIR) / "tcga_paad_mc3_public.tsv"
    if not maf_path.exists():
        logger.warning("TCGA-PAAD MAF not found at %s", maf_path)
        return {}

    df = pd.read_csv(maf_path, sep="\t", comment="#", low_memory=False)
    # Expected columns include: Hugo_Symbol, Variant_Classification
    # Keep only damaging variants
    damaging = df[df["Variant_Classification"].isin([
        "Missense_Mutation", "Nonsense_Mutation", "Frame_Shift_Del",
        "Frame_Shift_Ins", "Splice_Site", "Translation_Start_Site",
    ])]
    gene_counts = damaging["Hugo_Symbol"].value_counts()
    n_patients = df["Tumor_Sample_Barcode"].nunique()
    return {gene: count / n_patients for gene, count in gene_counts.items()}


def get_tcga_paad_freq() -> dict[str, float]:
    global _TCGA_CACHE
    if _TCGA_CACHE is None:
        _TCGA_CACHE = _compute_tcga_paad_freq()
    return _TCGA_CACHE
```

**Note**: The real TCGA-PAAD has 185 patients. The frequency for KRAS in real data is ~0.93, TP53 ~0.75, SMAD4 ~0.22, CDKN2A ~0.18.

---

## Phase 3: OncoKB API Integration

**Replace**: `cancer_annotation.py` → `_ONCOKB_LEVEL_MAP` (sparse hardcoded map)

**Source**: https://www.oncokb.org/api
- Free academic access via token
- Endpoint: `https://www.oncokb.org/api/v1/annotate/mutations/byHGVS?hgvsg={hgvsg}`
- Headers: `Authorization: Bearer {ONCOKB_API_KEY}`

**Drop-in replacement**:

```python
# modules/variant_rank/src/variant_rank/services/oncokb_client.py

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)
_BASE_URL = "https://www.oncokb.org/api/v1"


class OncoKBClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ONCOKB_API_KEY", "")
        self._cache: dict[str, dict[str, Any]] = {}
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )

    async def annotate_variant(self, hgvsg: str) -> dict[str, Any]:
        """Returns oncogenic level, effect, and drugs for a variant."""
        if hgvsg in self._cache:
            return self._cache[hgvsg]
        try:
            resp = await self._client.get(
                "/annotate/mutations/byHGVS",
                params={"hgvsg": hgvsg},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("OncoKB lookup failed for %s: %s", hgvsg, exc)
            data = {}
        self._cache[hgvsg] = data
        return data

    def oncokb_level_to_score(self, level: str | None) -> float:
        """Map OncoKB level to numeric score."""
        mapping = {
            "LEVEL_1": 10.0, "LEVEL_2": 8.0,
            "LEVEL_3A": 6.0, "LEVEL_3B": 4.0,
            "LEVEL_4": 2.0, "LEVEL_R1": 1.0,
        }
        return mapping.get(level or "", 0.0)

    async def aclose(self):
        await self._client.aclose()
```

**Usage in `somatic_scoring.py`**:
```python
oncokb = OncoKBClient()
result = await oncokb.annotate_variant("7:g.140753336A>T")  # KRAS G12D
level = result.get("oncogenic", "")
score = oncokb.oncokb_level_to_score(level)
```

---

## Phase 4: STRING DB PPI Network

**Replace**: `modules/ppi_score/src/ppi_score/cancer_ppi.py` → `PANCREATIC_CANCER_PPI`

**Source**: https://string-db.org/download
- File: `9606.protein.links.detailed.v12.0.txt.gz` (Homo sapiens, Sapiens)
- Combined score threshold: ≥400 (medium confidence) or ≥700 (high)
- License: CC BY 4.0

**Drop-in replacement**:

```python
# modules/ppi_score/src/ppi_score/data_loaders/string_db.py

import gzip
import logging
from pathlib import Path
from typing import Any

from ppi_score.config import settings

logger = logging.getLogger(__name__)
_STRING_CACHE: dict[tuple[str, str], dict[str, float]] | None = None
_MIN_SCORE = 400  # medium confidence


def _parse_string_id(pid: str) -> str:
    """Strip '9606.' prefix from STRING protein IDs."""
    return pid.split(".")[-1] if pid.startswith("9606.") else pid


def _load_string_network() -> dict[tuple[str, str], dict[str, float]]:
    path = Path(settings.STRING_DB_DIR) / "9606.protein.links.detailed.v12.0.txt.gz"
    if not path.exists():
        logger.warning("STRING DB not found at %s", path)
        return {}

    out: dict[tuple[str, str], dict[str, float]] = {}
    with gzip.open(path, "rt") as f:
        header = f.readline().strip().split()
        for line in f:
            parts = line.strip().split()
            if len(parts) < len(header):
                continue
            p1, p2 = _parse_string_id(parts[0]), _parse_string_id(parts[1])
            score = float(parts[-1])  # combined_score is last column
            if score < _MIN_SCORE:
                continue
            key = tuple(sorted([p1, p2]))
            out[key] = {"combined": score}
    logger.info("Loaded %d STRING interactions (>=%d confidence)", len(out), _MIN_SCORE)
    return out


def get_string_network() -> dict[tuple[str, str], dict[str, float]]:
    global _STRING_CACHE
    if _STRING_CACHE is None:
        _STRING_CACHE = _load_string_network()
    return _STRING_CACHE
```

**Note**: Requires a STRING→HGNC symbol mapping file (`9606.protein.info.v12.0.txt.gz`) to convert protein IDs to gene symbols.

---

## Phase 5: GTEx Pancreas Expression

**Replace**: `ppi_score` — currently **not implemented** (no `GTEx` integration exists)

**Source**: https://gtexportal.org/home/datasets
- File: `GTEx_Analysis_v11_RSEMv1.3.3_gene_median_tpm.gct.gz`
- License: dbGaP

**Drop-in replacement**:

```python
# modules/ppi_score/src/ppi_score/data_loaders/gtex.py

import gzip
import logging
from pathlib import Path

import pandas as pd

from ppi_score.config import settings

logger = logging.getLogger(__name__)
_GTEX_CACHE: dict[str, dict[str, float]] | None = None
_PANCREAS_TISSUE = "Pancreas"


def _load_gtex() -> dict[str, dict[str, float]]:
    path = Path(settings.GTEx_DATA_DIR) / "GTEx_Analysis_v11_RSEMv1.3.3_gene_median_tpm.gct.gz"
    if not path.exists():
        return {}

    df = pd.read_csv(path, sep="\t", index_col=1, compression="gzip")
    df = df[df.columns[2:]]  # drop Description column
    df_t = df.T
    return {gene: dict(row) for gene, row in df_t.iterrows()}


def get_gtex_pancreas_tpm(gene: str) -> float:
    """Returns median TPM for gene in pancreas tissue."""
    global _GTEX_CACHE
    if _GTEX_CACHE is None:
        _GTEX_CACHE = _load_gtex()
    if not _GTEX_CACHE:
        return 0.0
    # Find the gene (GTEx uses ENSG IDs; we use HGNC symbols here)
    for g, tissues in _GTEX_CACHE.items():
        if g.upper() == gene.upper():
            return tissues.get(_PANCREAS_TISSUE, 0.0)
    return 0.0
```

---

## Phase 6: HPO Ontology

**Replace**: `modules/phenotype_rag/src/phenotype_rag/pipeline.py` → `PANCREATIC_CANCER_HPO_TERMS` (45-term dict)

**Source**: https://hpo.jax.org/app/data/ontology
- File: `hp.obo` (ontology) + `phenotype.hpoa` (disease annotations)
- License: Custom (free for academic / clinical use)

**Drop-in replacement**:

```python
# modules/phenotype_rag/src/phenotype_rag/data_loaders/hpo.py

import logging
import re
from pathlib import Path
from typing import Any

from phenotype_rag.config import settings

logger = logging.getLogger(__name__)
_HPO_CACHE: dict[str, dict[str, Any]] | None = None


def _parse_obo(path: Path) -> dict[str, dict[str, Any]]:
    """Minimal OBO parser for HPO."""
    out: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] = {}
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith("["):
                if current.get("id"):
                    out[current["id"]] = current
                current = {}
                continue
            if line == "[Term]":
                if current.get("id"):
                    out[current["id"]] = current
                current = {}
            elif ":" in line:
                key, _, value = line.partition(": ")
                current[key] = value
        if current.get("id"):
            out[current["id"]] = current
    return out


def _load_hpo() -> dict[str, dict[str, Any]]:
    path = Path(settings.HPO_DATA_DIR) / "hp.obo"
    if not path.exists():
        logger.warning("HPO ontology not found at %s", path)
        return {}
    return _parse_obo(path)


def get_hpo_term(hpo_id: str) -> dict[str, Any] | None:
    global _HPO_CACHE
    if _HPO_CACHE is None:
        _HPO_CACHE = _load_hpo()
    return _HPO_CACHE.get(hpo_id)


def get_hpo_by_name(name: str) -> list[dict[str, Any]]:
    """Fuzzy match HPO terms by name."""
    global _HPO_CACHE
    if _HPO_CACHE is None:
        _HPO_CACHE = _load_hpo()
    name_l = name.lower()
    pattern = re.compile(rf"\b{re.escape(name_l)}\b")
    return [
        {"id": tid, "name": t.get("name", "")}
        for tid, t in _HPO_CACHE.items()
        if name_l in t.get("name", "").lower()
    ]
```

---

## Phase 7: ClinicalTrials.gov API

**Replace**: `modules/PanCancerSystem/backend/api/trials.py` → `_PANCREATIC_CANCER_TRIALS`

**Source**: https://clinicaltrials.gov/api/v2/studies
- Free public API, no key required
- Endpoint: `https://clinicaltrials.gov/api/v2/studies?query.cond=pancreatic+cancer&filter.overallStatus=RECRUITING&pageSize=100&fields=NCTId,BriefTitle,EligibilityCriteria,InterventionName,Condition`

**Drop-in replacement**:

```python
# modules/PanCancerSystem/backend/services/clinicaltrials_client.py

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
_BASE = "https://clinicaltrials.gov/api/v2/studies"


async def search_pancreatic_cancer_trials(
    gene: str | None = None,
    status: str = "RECRUITING",
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Search active pancreatic cancer trials, optionally filtered by gene."""
    params = {
        "query.cond": "pancreatic cancer",
        "filter.overallStatus": status,
        "pageSize": str(page_size),
        "fields": ",".join([
            "NCTId", "BriefTitle", "OfficialTitle", "EligibilityCriteria",
            "InterventionName", "Condition", "Phase", "LeadSponsorName",
        ]),
    }
    if gene:
        params["query.intr"] = gene
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            return resp.json().get("studies", [])
        except httpx.HTTPError as exc:
            logger.warning("ClinicalTrials.gov lookup failed: %s", exc)
            return []
```

---

## Phase 8: Drug-Gene Database (DGIdb)

**Replace**: `modules/report/src/report/report/drug_recommendations.py` → `DRUG_RECOMMENDATIONS`

**Source**: https://dgidb.org/api
- Free public API
- Endpoint: `https://dgidb.org/api/v2/interactions?genes=BRCA1&sources=CIViC,DoCM,MyCancerGenome`

**Drop-in replacement**:

```python
# modules/report/src/report/services/dgidb_client.py

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
_BASE = "https://dgidb.org/api/v2"


async def get_drugs_for_gene(gene: str) -> list[dict[str, Any]]:
    """Return drug-gene interactions from DGIdb."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{_BASE}/interactions",
                params={"genes": gene, "sources": "CIViC,DoCM,MyCancerGenome"},
            )
            resp.raise_for_status()
            return resp.json().get("interactions", [])
        except httpx.HTTPError as exc:
            logger.warning("DGIdb lookup failed for %s: %s", gene, exc)
            return []
```

---

## Migration Checklist

After implementing each phase, verify:

- [ ] Module starts without import errors (`uv run --project modules/X python -c "import X"`)
- [ ] Health endpoint returns 200 (`curl http://localhost:PORT/health`)
- [ ] Integration with downstream modules still works
- [ ] Frontend displays non-empty data
- [ ] Test suite passes (see `docs/testing/`)

## Performance Notes

- **Cache aggressively**: All loaders use module-level dict cache. For multi-worker setups, use Redis or pre-compute to disk.
- **Lazy load**: Don't load at module import; wait until first request.
- **Truncate at startup**: For large files (STRING, GTEx), pre-process into smaller indexed files (parquet, sqlite) during a one-time setup step.

## Source Data Licenses

| Source | License | Use |
|--------|---------|-----|
| COSMIC | Academic only | Register at cancer.sanger.ac.uk |
| TCGA | Open (dbGaP) | Free for research |
| OncoKB | Free for academic | Register at oncokb.org |
| STRING | CC BY 4.0 | Open |
| GTEx | dbGaP controlled | Apply for access |
| HPO | HPO License | Free for clinical/research |
| ClinicalTrials.gov | Open (US Gov) | Free |
| DGIdb | Open | Free |

For commercial use, contact each source's licensing team.
