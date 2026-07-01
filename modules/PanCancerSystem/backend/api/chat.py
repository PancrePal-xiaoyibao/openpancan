"""Chat and WebSocket endpoints for patient conversations."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CancerPatient, SomaticVariant, GermlineVariant, TreatmentRecord
from backend.database.session import get_db

logger = logging.getLogger("pan_cancer_system.chat")

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ChatQuestion(BaseModel):
    patient_id: int
    question: str = Field(..., min_length=1, description="Clinical question about the patient")


class ChatResponse(BaseModel):
    patient_id: int
    question: str
    answer: str


# ---------------------------------------------------------------------------
# Active WebSocket connections store
# ---------------------------------------------------------------------------
_active_connections: dict[int, list[WebSocket]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_patient_context(
    patient: CancerPatient,
    somatic_variants: list[SomaticVariant],
    germline_variants: list[GermlineVariant],
    treatments: list[TreatmentRecord],
) -> str:
    """Build a context summary for the chat model."""
    lines = [
        f"## Patient: {patient.name}",
        f"Age: {patient.age or 'Unknown'}",
        f"Sex: {patient.sex or 'Unknown'}",
        f"Diagnosis: {patient.diagnosis or 'Unknown'}",
        f"Tumor Location: {patient.tumor_location or 'Unknown'}",
        f"Tumor Stage: {patient.tumor_stage or 'Unknown'}",
        f"Tumor Grade: {patient.tumor_grade or 'Unknown'}",
        f"Histology: {patient.histology_type or 'Unknown'}",
        f"CA19-9: {patient.ca19_9_level or 'Unknown'} U/mL",
        "",
    ]

    if patient.biomarkers:
        lines.append("## Biomarkers")
        for gene, status in patient.biomarkers.items():
            lines.append(f"- {gene}: {status}")
        lines.append("")

    if somatic_variants:
        lines.append("## Somatic Variants")
        for v in somatic_variants:
            lines.append(
                f"- {v.gene or 'Intergenic'} {v.chromosome}:{v.position} {v.ref}>{v.alt} "
                f"(VAF: {v.vaf or 'N/A'}, Impact: {v.impact or 'N/A'}, "
                f"ClinVar: {v.clinvar_significance or 'N/A'})"
            )
        lines.append("")

    if germline_variants:
        lines.append("## Germline Variants")
        for v in germline_variants:
            lines.append(
                f"- {v.gene or 'Intergenic'} {v.chromosome}:{v.position} {v.ref}>{v.alt} "
                f"(ACMG: {v.acmg_classification or 'N/A'}, "
                f"ClinVar: {v.clinvar_significance or 'N/A'})"
            )
        lines.append("")

    if treatments:
        lines.append("## Treatment History")
        for t in treatments:
            lines.append(
                f"- {t.treatment_type}: {t.drug_name or t.regimen or 'N/A'} "
                f"({t.start_date or '?'} to {t.end_date or '?'}): {t.response or 'N/A'}"
            )
        lines.append("")

    lines.extend([
        f"## Family History: {patient.family_history or 'Not reported'}",
        f"## Smoking Status: {patient.smoking_status or 'Not reported'}",
        f"## Alcohol History: {patient.alcohol_history or 'Not reported'}",
    ])

    return "\n".join(lines)


async def _generate_answer(question: str, context: str) -> str:
    """Generate an AI answer to a clinical question about a patient.

    Uses LLM if configured, otherwise returns a rule-based response.
    """
    from backend.config import settings

    # Try LLM-based response
    if settings.LLM_API_KEY:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": settings.LLM_MODEL_NAME,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a pancreatic cancer clinical assistant. "
                                "Answer questions about the patient based on the provided "
                                "clinical and genomic context. Be concise, evidence-based, "
                                "and highlight actionable findings."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"## Patient Context\n\n{context}\n\n## Question\n\n{question}",
                        },
                    ],
                    "max_tokens": 600,
                    "temperature": 0.3,
                }
                response = await client.post(
                    f"{settings.LLM_API_BASE_URL}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning("LLM API returned status %d", response.status_code)
        except Exception as exc:
            logger.warning("LLM API call failed: %s", exc)

    # Fallback: rule-based response
    return _fallback_answer(question, context)


def _fallback_answer(question: str, context: str) -> str:
    """Provide a rule-based fallback answer when LLM is unavailable."""
    question_lower = question.lower()

    if "variant" in question_lower or "mutation" in question_lower:
        if "kras" in question_lower:
            return (
                "KRAS is the most commonly mutated gene in pancreatic cancer (90-95% of cases). "
                "KRAS G12D, G12V, and G12R are the most frequent variants. KRAS G12C mutations "
                "(~1-2% of cases) may be targetable with sotorasib or adagrasib. "
                "Please review the patient's specific KRAS variant details above."
            )
        elif "brca" in question_lower:
            return (
                "BRCA1/2 mutations in pancreatic cancer are important biomarkers. "
                "Patients with germline or somatic BRCA mutations may benefit from "
                "PARP inhibitor therapy (olaparib, niraparib, rucaparib) and "
                "platinum-based chemotherapy. Genetic counseling is recommended for germline findings."
            )
        return (
            "I found the following variants in this patient (see context above). "
            "Each variant should be assessed for pathogenicity, clinical actionability, "
            "and potential therapeutic implications."
        )

    if "treatment" in question_lower or "therapy" in question_lower:
        return (
            "Treatment recommendations should be based on tumor stage, molecular profile, "
            "and performance status. Standard first-line options include FOLFIRINOX or "
            "gemcitabine + nab-paclitaxel. For patients with actionable mutations, "
            "targeted therapies or clinical trials may be appropriate. "
            "Check the treatment history and recommendations endpoints for details."
        )

    if "prognosis" in question_lower:
        return (
            "Pancreatic cancer prognosis depends on stage at diagnosis, tumor resectability, "
            "molecular subtype, performance status, and response to therapy. "
            "Stage I-II resectable disease has a 5-year survival of 20-37% with adjuvant therapy. "
            "Metastatic disease has a median survival of 8-12 months with current therapies."
        )

    if "trial" in question_lower or "clinical trial" in question_lower:
        return (
            "Clinical trial matching is available through the /api/trials/match/{patient_id} endpoint. "
            "Trials are matched based on the patient's genomic variants. Consider NTRK, MSI-H, "
            "BRCA, KRAS G12C, and other actionable alterations for trial eligibility."
        )

    return (
        "Based on the patient's clinical and genomic profile shown above, I recommend reviewing "
        "the key genomic findings, treatment history, and clinical trial options. "
        "Please ask a more specific question about variants, treatments, prognosis, or clinical trials."
    )


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------


@router.post("/ask", response_model=ChatResponse, tags=["chat"])
async def ask_question(
    data: ChatQuestion,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Ask a clinical question about a specific patient."""
    # Get patient
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    # Get variants and treatments
    som_result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.patient_id == data.patient_id)
    )
    somatic_variants = som_result.scalars().all()

    germ_result = await db.execute(
        select(GermlineVariant).where(GermlineVariant.patient_id == data.patient_id)
    )
    germline_variants = germ_result.scalars().all()

    tx_result = await db.execute(
        select(TreatmentRecord).where(TreatmentRecord.patient_id == data.patient_id)
    )
    treatments = tx_result.scalars().all()

    # Build context and generate answer
    context = _build_patient_context(patient, list(somatic_variants), list(germline_variants), list(treatments))
    answer = await _generate_answer(data.question, context)

    return ChatResponse(
        patient_id=data.patient_id,
        question=data.question,
        answer=answer,
    )


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------


@router.websocket("/ws/{patient_id}")
async def chat_websocket(websocket: WebSocket, patient_id: int):
    """WebSocket endpoint for real-time chat about a patient."""
    await websocket.accept()

    if patient_id not in _active_connections:
        _active_connections[patient_id] = []
    _active_connections[patient_id].append(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to PanCancerSystem chat for patient {patient_id}. Ask clinical questions.",
        })

        # Get patient context (need a sync DB session)
        from backend.database.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CancerPatient).where(CancerPatient.id == patient_id)
            )
            patient = result.scalar_one_or_none()
            if not patient:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Patient not found: {patient_id}",
                })
                await websocket.close()
                return

            som_result = await db.execute(
                select(SomaticVariant).where(SomaticVariant.patient_id == patient_id)
            )
            somatic_variants = som_result.scalars().all()

            germ_result = await db.execute(
                select(GermlineVariant).where(GermlineVariant.patient_id == patient_id)
            )
            germline_variants = germ_result.scalars().all()

            tx_result = await db.execute(
                select(TreatmentRecord).where(TreatmentRecord.patient_id == patient_id)
            )
            treatments = tx_result.scalars().all()

            context = _build_patient_context(
                patient,
                list(somatic_variants),
                list(germline_variants),
                list(treatments),
            )

            # Send context summary
            await websocket.send_json({
                "type": "context",
                "patient_name": patient.name,
                "diagnosis": patient.diagnosis,
                "variant_count": len(somatic_variants) + len(germline_variants),
            })

            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    question = message.get("question", "")
                    if not question:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Please provide a 'question' field.",
                        })
                        continue

                    # Echo question
                    await websocket.send_json({
                        "type": "user",
                        "message": question,
                    })

                    # Generate answer
                    answer = await _generate_answer(question, context)
                    await websocket.send_json({
                        "type": "assistant",
                        "message": answer,
                    })

                except json.JSONDecodeError:
                    # Treat raw text as question
                    question = data.strip()
                    if question:
                        await websocket.send_json({
                            "type": "user",
                            "message": question,
                        })
                        answer = await _generate_answer(question, context)
                        await websocket.send_json({
                            "type": "assistant",
                            "message": answer,
                        })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for patient %d", patient_id)
    except Exception as exc:
        logger.exception("WebSocket error for patient %d", patient_id)
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        if patient_id in _active_connections:
            _active_connections[patient_id].remove(websocket)
            if not _active_connections[patient_id]:
                del _active_connections[patient_id]
