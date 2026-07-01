"""
Cancer Phenotype Extraction Pipeline.

Implements rule-based and LLM-assisted extraction of cancer phenotypes
from clinical text, including HPO term mapping, tumor characteristics,
biomarker status, and treatment history for pancreatic cancer patients.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pancreatic Cancer HPO Terms
# ---------------------------------------------------------------------------
PANCREATIC_CANCER_HPO_TERMS: dict[str, dict[str, Any]] = {
    # Core pancreatic cancer phenotypes
    "pancreatic adenocarcinoma": {
        "hpo_id": "HP:0002894",
        "term": "Neoplasm of the pancreas",
        "category": "tumor_characteristic",
    },
    "pancreatic ductal adenocarcinoma": {
        "hpo_id": "HP:0002894",
        "term": "Neoplasm of the pancreas",
        "category": "tumor_characteristic",
    },
    "pancreatic neuroendocrine tumor": {
        "hpo_id": "HP:0002894",
        "term": "Neoplasm of the pancreas",
        "category": "tumor_characteristic",
    },
    # Symptoms
    "jaundice": {
        "hpo_id": "HP:0000952",
        "term": "Jaundice",
        "category": "symptom",
    },
    "obstructive jaundice": {
        "hpo_id": "HP:0000952",
        "term": "Jaundice",
        "category": "symptom",
    },
    "pruritus": {
        "hpo_id": "HP:0000989",
        "term": "Pruritus",
        "category": "symptom",
    },
    "abdominal pain": {
        "hpo_id": "HP:0002027",
        "term": "Abdominal pain",
        "category": "symptom",
    },
    "epigastric pain": {
        "hpo_id": "HP:0410019",
        "term": "Epigastric pain",
        "category": "symptom",
    },
    "back pain": {
        "hpo_id": "HP:0003418",
        "term": "Back pain",
        "category": "symptom",
    },
    "weight loss": {
        "hpo_id": "HP:0001824",
        "term": "Weight loss",
        "category": "symptom",
    },
    "unintentional weight loss": {
        "hpo_id": "HP:0001824",
        "term": "Weight loss",
        "category": "symptom",
    },
    "cachexia": {
        "hpo_id": "HP:0004426",
        "term": "Cachexia",
        "category": "symptom",
    },
    "anorexia": {
        "hpo_id": "HP:0002039",
        "term": "Anorexia",
        "category": "symptom",
    },
    "loss of appetite": {
        "hpo_id": "HP:0002039",
        "term": "Anorexia",
        "category": "symptom",
    },
    "nausea": {
        "hpo_id": "HP:0002018",
        "term": "Nausea",
        "category": "symptom",
    },
    "vomiting": {
        "hpo_id": "HP:0002013",
        "term": "Vomiting",
        "category": "symptom",
    },
    "nausea and vomiting": {
        "hpo_id": "HP:0002017",
        "term": "Nausea and vomiting",
        "category": "symptom",
    },
    "ascites": {
        "hpo_id": "HP:0001541",
        "term": "Ascites",
        "category": "symptom",
    },
    "fatigue": {
        "hpo_id": "HP:0012378",
        "term": "Fatigue",
        "category": "symptom",
    },
    "malaise": {
        "hpo_id": "HP:0032313",
        "term": "Malaise",
        "category": "symptom",
    },
    "depression": {
        "hpo_id": "HP:0000716",
        "term": "Depressive episode",
        "category": "comorbidity",
    },
    "anxiety": {
        "hpo_id": "HP:0000739",
        "term": "Anxiety",
        "category": "comorbidity",
    },
    # Metabolic
    "diabetes mellitus": {
        "hpo_id": "HP:0000819",
        "term": "Diabetes mellitus",
        "category": "comorbidity",
    },
    "new-onset diabetes": {
        "hpo_id": "HP:0000819",
        "term": "Diabetes mellitus",
        "category": "comorbidity",
    },
    "hyperglycemia": {
        "hpo_id": "HP:0003074",
        "term": "Hyperglycemia",
        "category": "lab_result",
    },
    "glucose intolerance": {
        "hpo_id": "HP:0000832",
        "term": "Glucose intolerance",
        "category": "lab_result",
    },
    # Vascular
    "deep vein thrombosis": {
        "hpo_id": "HP:0002625",
        "term": "Deep venous thrombosis",
        "category": "comorbidity",
    },
    "thrombosis": {
        "hpo_id": "HP:0004936",
        "term": "Venous thrombosis",
        "category": "comorbidity",
    },
    "pulmonary embolism": {
        "hpo_id": "HP:0002204",
        "term": "Pulmonary embolism",
        "category": "comorbidity",
    },
    # Pancreatitis
    "pancreatitis": {
        "hpo_id": "HP:0001733",
        "term": "Pancreatitis",
        "category": "comorbidity",
    },
    "acute pancreatitis": {
        "hpo_id": "HP:0001733",
        "term": "Pancreatitis",
        "category": "comorbidity",
    },
    "chronic pancreatitis": {
        "hpo_id": "HP:0006280",
        "term": "Chronic pancreatitis",
        "category": "comorbidity",
    },
    # Lab abnormalities
    "elevated CA19-9": {
        "hpo_id": "HP:0032205",
        "term": "Abnormal tumor marker level",
        "category": "lab_result",
    },
    "elevated bilirubin": {
        "hpo_id": "HP:0002910",
        "term": "Elevated total bilirubin",
        "category": "lab_result",
    },
    "elevated alkaline phosphatase": {
        "hpo_id": "HP:0003155",
        "term": "Elevated alkaline phosphatase",
        "category": "lab_result",
    },
    # Metastasis patterns
    "liver metastasis": {
        "hpo_id": "HP:0025490",
        "term": "Liver metastasis",
        "category": "metastasis",
    },
    "peritoneal metastasis": {
        "hpo_id": "HP:0033808",
        "term": "Peritoneal metastasis",
        "category": "metastasis",
    },
    "peritoneal carcinomatosis": {
        "hpo_id": "HP:0033808",
        "term": "Peritoneal metastasis",
        "category": "metastasis",
    },
    "lung metastasis": {
        "hpo_id": "HP:0033810",
        "term": "Lung metastasis",
        "category": "metastasis",
    },
    "lymph node metastasis": {
        "hpo_id": "HP:0025559",
        "term": "Lymph node metastasis",
        "category": "metastasis",
    },
    # Genetic/hereditary
    "family history of pancreatic cancer": {
        "hpo_id": "HP:0033773",
        "term": "Family history of pancreatic cancer",
        "category": "family_history",
    },
    "BRCA1 mutation": {
        "hpo_id": "HP:0033746",
        "term": "BRCA1-related cancer susceptibility",
        "category": "biomarker",
    },
    "BRCA2 mutation": {
        "hpo_id": "HP:0033747",
        "term": "BRCA2-related cancer susceptibility",
        "category": "biomarker",
    },
}


# ---------------------------------------------------------------------------
# CancerPhenotypePipeline
# ---------------------------------------------------------------------------
class CancerPhenotypePipeline:
    """
    Extracts pancreatic cancer phenotypes from clinical notes using
    rule-based matching and (optionally) LLM-assisted extraction.
    """

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.hpo_map = PANCREATIC_CANCER_HPO_TERMS

    def extract_hpo_terms(self, text: str) -> list[dict[str, Any]]:
        """
        Extract HPO terms and IDs from clinical text using rule-based matching.

        Parameters
        ----------
        text : str
            Clinical note text.

        Returns
        -------
        list[dict]
            List of extracted HPO terms with metadata.
        """
        results: list[dict[str, Any]] = []
        text_lower = text.lower()
        seen_terms: set[str] = set()

        for term_key, term_data in self.hpo_map.items():
            if term_key.lower() in text_lower and term_key not in seen_terms:
                seen_terms.add(term_key)

                # Find evidence span
                span_start = text_lower.find(term_key.lower())
                span_end = span_start + len(term_key)
                evidence_span = text[span_start:span_end] if span_start >= 0 else term_key

                # Compute confidence based on specificity
                confidence = 0.7
                if len(term_key) > 15:
                    confidence = 0.9
                elif term_key in ("jaundice", "ascites", "pancreatitis"):
                    confidence = 0.85

                results.append({
                    "hpo_id": term_data["hpo_id"],
                    "hpo_term": term_data["term"],
                    "phenotype_type": term_data["category"],
                    "confidence": confidence,
                    "evidence_span": evidence_span,
                })

        return results

    def extract_tumor_characteristics(self, text: str) -> dict[str, Any]:
        """
        Extract tumor-related characteristics from clinical text.

        Returns dict with: tumor_location, tumor_size_cm, tnm_stage,
        histology, grade.
        """
        result: dict[str, Any] = {
            "tumor_location": None,
            "tumor_size_cm": None,
            "tnm_stage": None,
            "histology": None,
            "grade": None,
            "confidence": 0.6,
        }

        text_lower = text.lower()

        # Tumor location
        loc_patterns = [
            (r"pancreatic\s*head", "head of pancreas"),
            (r"head\s*of\s*(?:the\s*)?pancreas", "head of pancreas"),
            (r"pancreatic\s*body", "body of pancreas"),
            (r"body\s*of\s*(?:the\s*)?pancreas", "body of pancreas"),
            (r"pancreatic\s*tail", "tail of pancreas"),
            (r"tail\s*of\s*(?:the\s*)?pancreas", "tail of pancreas"),
            (r"pancreatic\s*neck", "neck of pancreas"),
            (r"uncinate\s*process", "uncinate process"),
        ]
        for pattern, location in loc_patterns:
            if re.search(pattern, text_lower):
                result["tumor_location"] = location
                result["confidence"] = 0.85
                break

        # Tumor size
        size_match = re.search(
            r"(\d+\.?\d*)\s*cm(?:\s*(?:mass|tumor|lesion))?", text_lower
        )
        if size_match:
            result["tumor_size_cm"] = float(size_match.group(1))
            result["confidence"] = max(result["confidence"], 0.8)

        # TNM stage
        tnm_patterns = [
            (r"stage\s*IV\s*[AB]?", "Stage IV"),
            (r"stage\s*III\s*[AB]?", "Stage III"),
            (r"stage\s*II\s*[AB]?", "Stage II"),
            (r"stage\s*I\s*[AB]?", "Stage I"),
            (r"T\d+N\d+M\d+", None),  # Direct TNM
        ]
        for pattern, stage in tnm_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result["tnm_stage"] = stage or match.group(0).upper()
                result["confidence"] = max(result["confidence"], 0.85)
                break

        # Histology
        hist_patterns = [
            (r"ductal\s*adenocarcinoma", "pancreatic ductal adenocarcinoma"),
            (r"adenocarcinoma", "adenocarcinoma"),
            (r"neuroendocrine\s*tumor", "pancreatic neuroendocrine tumor"),
            (r"ipmn", "intraductal papillary mucinous neoplasm (IPMN)"),
            (r"acinar\s*cell\s*carcinoma", "acinar cell carcinoma"),
            (r"pancreatoblastoma", "pancreatoblastoma"),
        ]
        for pattern, histology in hist_patterns:
            if re.search(pattern, text_lower):
                result["histology"] = histology
                result["confidence"] = max(result["confidence"], 0.85)
                break

        # Grade
        grade_patterns = [
            (r"well[-\s]differentiated", "G1 (well differentiated)"),
            (r"moderately[-\s]differentiated", "G2 (moderately differentiated)"),
            (r"poorly[-\s]differentiated", "G3 (poorly differentiated)"),
            (r"undifferentiated", "G4 (undifferentiated)"),
            (r"grade\s*1", "G1"),
            (r"grade\s*2", "G2"),
            (r"grade\s*3", "G3"),
            (r"grade\s*4", "G4"),
        ]
        for pattern, grade in grade_patterns:
            if re.search(pattern, text_lower):
                result["grade"] = grade
                result["confidence"] = max(result["confidence"], 0.8)
                break

        return result

    def extract_biomarker_status(self, text: str) -> list[dict[str, Any]]:
        """
        Extract biomarker and molecular testing results.

        Returns list of biomarker findings.
        """
        results: list[dict[str, Any]] = []
        text_lower = text.lower()

        # KRAS mutations
        kras_pattern = r"kras\s*([A-Z]\d+[A-Z])"
        match = re.search(kras_pattern, text_lower)
        if match:
            results.append({
                "biomarker": "KRAS",
                "result": f"{match.group(1)} mutation",
                "method": "NGS" if "ngs" in text_lower else "unknown",
                "confidence": 0.9,
            })
        elif "kras wild" in text_lower or "kras wt" in text_lower:
            results.append({
                "biomarker": "KRAS",
                "result": "wild-type",
                "method": "NGS",
                "confidence": 0.85,
            })

        # TP53
        tp53_pattern = r"tp53\s*([A-Z]\d+[A-Z*])"
        match = re.search(tp53_pattern, text_lower)
        if match:
            results.append({
                "biomarker": "TP53",
                "result": f"{match.group(1)} mutation",
                "method": "NGS",
                "confidence": 0.9,
            })

        # MSI status
        if "msi-h" in text_lower or "msi high" in text_lower:
            results.append({
                "biomarker": "MSI",
                "result": "MSI-H (high)",
                "method": "IHC/NGS",
                "confidence": 0.9,
            })
        elif "mss" in text_lower or "msi stable" in text_lower:
            results.append({
                "biomarker": "MSI",
                "result": "MSS (stable)",
                "method": "IHC/NGS",
                "confidence": 0.85,
            })

        # TMB
        tmb_pattern = r"tmb\s*(\d+\.?\d*)\s*mut"
        match = re.search(tmb_pattern, text_lower)
        if match:
            results.append({
                "biomarker": "TMB",
                "result": f"{match.group(1)} mut/Mb",
                "method": "NGS",
                "confidence": 0.9,
            })

        # HER2
        if "her2" in text_lower:
            if "positive" in text_lower or "3+" in text_lower:
                results.append({
                    "biomarker": "HER2",
                    "result": "positive (IHC 3+)",
                    "method": "IHC",
                    "confidence": 0.85,
                })
            elif "negative" in text_lower:
                results.append({
                    "biomarker": "HER2",
                    "result": "negative",
                    "method": "IHC",
                    "confidence": 0.85,
                })

        # dMMR
        if "dmmr" in text_lower:
            results.append({
                "biomarker": "dMMR",
                "result": "deficient",
                "method": "IHC",
                "confidence": 0.85,
            })
        elif "pmmr" in text_lower or "mmr proficient" in text_lower:
            results.append({
                "biomarker": "dMMR",
                "result": "proficient (pMMR)",
                "method": "IHC",
                "confidence": 0.85,
            })

        # BRCA
        for brca in ["brca1", "brca2"]:
            if brca in text_lower:
                status = "mutation" if "mutation" in text_lower or "pathogenic" in text_lower else "VUS"
                results.append({
                    "biomarker": brca.upper(),
                    "result": status,
                    "method": "NGS",
                    "confidence": 0.85,
                })

        # SMAD4
        if "smad4" in text_lower:
            status = "loss" if "loss" in text_lower or "mutation" in text_lower else "intact"
            results.append({
                "biomarker": "SMAD4",
                "result": status,
                "method": "IHC/NGS",
                "confidence": 0.8,
            })

        return results

    def extract_treatment_history(self, text: str) -> list[dict[str, Any]]:
        """
        Extract oncologic treatment history from clinical text.

        Returns list of treatment records.
        """
        results: list[dict[str, Any]] = []
        text_lower = text.lower()

        # Surgical procedures
        surgery_patterns = [
            (r"whipple", "Whipple procedure (pancreaticoduodenectomy)"),
            (r"pancreaticoduodenectomy", "Whipple procedure (pancreaticoduodenectomy)"),
            (r"distal\s*pancreatectomy", "Distal pancreatectomy"),
            (r"total\s*pancreatectomy", "Total pancreatectomy"),
            (r"central\s*pancreatectomy", "Central pancreatectomy"),
            (r"enucleation", "Tumor enucleation"),
            (r"bypass\s*surgery", "Palliative bypass surgery"),
            (r"biliary\s*stent", "Biliary stent placement"),
            (r"celiac\s*plexus\s*block", "Celiac plexus block"),
        ]
        for pattern, surgery in surgery_patterns:
            if re.search(pattern, text_lower):
                results.append({
                    "treatment": surgery,
                    "type": "surgery",
                    "date_or_status": "performed",
                    "confidence": 0.85,
                })

        # Chemotherapy regimens
        chemo_patterns = [
            (r"folfirinox", "FOLFIRINOX"),
            (r"modified\s*folfirinox", "Modified FOLFIRINOX (mFOLFIRINOX)"),
            (r"gemcitabine\s*[-/]\s*nab.paclitaxel", "Gemcitabine + nab-paclitaxel"),
            (r"gemcitabine", "Gemcitabine"),
            (r"nab.paclitaxel", "Nab-paclitaxel"),
            (r"nal-iri", "Nanoliposomal irinotecan (nal-IRI)"),
            (r"5-fu", "5-Fluorouracil"),
            (r"capecitabine", "Capecitabine"),
            (r"oxaliplatin", "Oxaliplatin-based"),
            (r"irinotecan", "Irinotecan"),
            (r"cisplatin", "Cisplatin"),
            (r"s-1", "S-1 (tegafur/gimeracil/oteracil)"),
        ]
        for pattern, chemo in chemo_patterns:
            if re.search(pattern, text_lower):
                # Check for cycles
                cycles_match = re.search(
                    pattern + r".*?(\d+)\s*(?:cycles|rounds|courses)", text_lower
                )
                date_or_status = f"{cycles_match.group(1)} cycles" if cycles_match else "administered"
                results.append({
                    "treatment": chemo,
                    "type": "chemotherapy",
                    "date_or_status": date_or_status,
                    "confidence": 0.85,
                })

        # Radiation
        if re.search(r"radiation|radiotherapy|sbrt|imrt|stereotactic", text_lower):
            results.append({
                "treatment": "Radiation therapy",
                "type": "radiation",
                "date_or_status": "administered",
                "confidence": 0.85,
            })

        # Targeted therapy
        if re.search(r"parp\s*inhibitor|olaparib|rucaparib|niraparib", text_lower):
            results.append({
                "treatment": "PARP inhibitor",
                "type": "targeted",
                "date_or_status": "administered",
                "confidence": 0.9,
            })
        if re.search(r"sotorasib|adagrasib|kras\s*g12c\s*inhibitor", text_lower):
            results.append({
                "treatment": "KRAS G12C inhibitor",
                "type": "targeted",
                "date_or_status": "administered",
                "confidence": 0.9,
            })

        return results

    def run(self, note_text: str) -> dict[str, Any]:
        """
        Run the full phenotype extraction pipeline on a clinical note.

        Parameters
        ----------
        note_text : str
            Free-text clinical note.

        Returns
        -------
        dict
            Structured phenotype extraction results with keys:
            hpo_terms, tumor_characteristics, biomarkers, treatments.
        """
        logger.info("Running phenotype extraction on %d char note", len(note_text))

        hpo_terms = self.extract_hpo_terms(note_text)
        tumor_chars = self.extract_tumor_characteristics(note_text)
        biomarkers = self.extract_biomarker_status(note_text)
        treatments = self.extract_treatment_history(note_text)

        result = {
            "hpo_terms": hpo_terms,
            "tumor_characteristics": tumor_chars,
            "biomarkers": biomarkers,
            "treatments": treatments,
        }

        logger.info(
            "Extracted %d HPO terms, %d biomarkers, %d treatments",
            len(hpo_terms), len(biomarkers), len(treatments),
        )

        return result
