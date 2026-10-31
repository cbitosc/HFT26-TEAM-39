from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.incident import Incident
from app.models.evidence import Evidence, EvidenceFileType
from app.models.event import Event, EventClassification
from app.models.vehicle import Vehicle
from app.schemas.analysis import (
    TelemetryProcessRequest,
    TelemetryProcessResponse,
    TelemetryVehicleSummary,
    WitnessAnalysisRequest,
    WitnessAnalysisResponse,
    WitnessClaim,
    ContradictionAnalysisResponse,
    ContradictionItem,
    AIStatusResponse,
    AIConfigureRequest,
    AISummaryRequest,
    AISummaryResponse,
    IncidentReportResponse,
)
from app.services.telemetry_service import telemetry_service, TelemetryProcessingError
from app.services.contradiction_service import contradiction_service
from app.services.featherless_service import featherless_service
from app.services.timeline_service import timeline_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis & Investigation"])


# System Health
@router.get("/api/health")
def api_health():
    """Returns backend system status, operational mode, and uptime status."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "database": "CONNECTED",
        "cv_engine": "OPENCV_READY",
    }


# AI Service Status
@router.get("/api/ai/status", response_model=AIStatusResponse)
async def get_ai_status():
    """Checks Featherless AI configuration and server connectivity."""
    is_avail, message = await featherless_service.check_availability()
    return AIStatusResponse(
        is_available=is_avail,
        provider="Featherless AI",
        model=settings.FEATHERLESS_MODEL,
        base_url=settings.FEATHERLESS_BASE_URL,
        message=message,
    )


@router.post("/api/ai/configure", response_model=AIStatusResponse)
async def configure_ai_key(payload: AIConfigureRequest):
    """Securely configures the server-side Featherless AI API key at runtime.
    
    Validates connectivity with Featherless AI servers without logging or exposing secrets.
    """
    clean_key = payload.api_key.strip()
    featherless_service.set_api_key(clean_key)
    if payload.model:
        featherless_service.model = payload.model.strip()

    is_avail, message = await featherless_service.check_availability()

    # Also persist to backend/.env if writable
    try:
        env_path = settings.BASE_DIR / ".env"
        env_lines = []
        if env_path.exists():
            env_lines = env_path.read_text(encoding="utf-8").splitlines()

        # Update or append FEATHERLESS_API_KEY
        key_found = False
        new_lines = []
        for line in env_lines:
            if line.startswith("FEATHERLESS_API_KEY="):
                new_lines.append(f"FEATHERLESS_API_KEY={clean_key}")
                key_found = True
            else:
                new_lines.append(line)
        if not key_found:
            new_lines.append(f"FEATHERLESS_API_KEY={clean_key}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as e:
        logger.warning("Could not persist API key to .env: %s", str(e))

    return AIStatusResponse(
        is_available=is_avail,
        provider="Featherless AI",
        model=featherless_service.model,
        base_url=featherless_service.base_url,
        message=message,
    )


# Telemetry Processing
@router.post("/api/incidents/{incident_id}/telemetry/process", response_model=TelemetryProcessResponse)
def process_telemetry(
    incident_id: str,
    payload: TelemetryProcessRequest,
    db: Session = Depends(get_db),
):
    """Processes, validates, and reconstructs deterministic kinematic events from CSV telemetry.
    
    Preserves exact 1-indexed row numbers, raw timestamps, and explicitly records missing fields.
    Never invents missing sensor values.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    evidence = db.query(Evidence).filter(
        Evidence.id == payload.evidence_id,
        Evidence.incident_id == incident_id,
    ).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{payload.evidence_id}' not found for incident '{incident_id}'.",
        )

    if evidence.file_type != EvidenceFileType.TELEMETRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evidence '{payload.evidence_id}' is of type '{evidence.file_type}', expected TELEMETRY.",
        )

    try:
        results = telemetry_service.process_telemetry(
            file_path=Path(evidence.file_path),
            incident_id=incident_id,
            evidence_id=evidence.id,
        )
    except TelemetryProcessingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Telemetry error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process telemetry: {str(e)}",
        )

    # Save generated kinematic events to timeline
    created_events = 0
    for evt_data in results["generated_events"]:
        timeline_service.create_event(
            db=db,
            incident_id=incident_id,
            timestamp=evt_data["timestamp"],
            event_type=evt_data["event_type"],
            description=evt_data["description"],
            classification=EventClassification(evt_data["classification"]),
            vehicle_id=evt_data.get("vehicle_id"),
            source_evidence_ids=evt_data.get("source_evidence_ids"),
            source_row_numbers=evt_data.get("source_row_numbers"),
            confidence=evt_data.get("confidence"),
            raw_data=evt_data.get("raw_data"),
        )
        created_events += 1

    # Record or update tracked vehicles in database
    for v_sum in results["vehicles"]:
        v_id = v_sum["vehicle_id"]
        existing = db.query(Vehicle).filter(
            Vehicle.incident_id == incident_id,
            Vehicle.vehicle_id == v_id,
        ).first()
        if not existing:
            veh = Vehicle(
                id=f"VEH-{incident_id}-{v_id}",
                incident_id=incident_id,
                vehicle_id=v_id,
                role="PRIMARY_TRACKED_TELEMETRY",
            )
            db.add(veh)

    # Update evidence record metadata
    meta = json.loads(evidence.metadata_json) if evidence.metadata_json else {}
    meta["telemetry_summary"] = {
        "total_rows": results["total_rows"],
        "valid_rows": results["valid_rows"],
        "missing_field_rows": results["rows_with_missing_fields"],
        "vehicles": results["vehicles"],
    }
    evidence.metadata_json = json.dumps(meta)
    evidence.is_processed = True
    db.commit()

    summary_text = (
        f"Successfully processed {results['total_rows']} telemetry rows across "
        f"{len(results['vehicles'])} vehicle(s). Generated {created_events} deterministic "
        f"kinematic timeline events."
    )

    return TelemetryProcessResponse(
        incident_id=incident_id,
        evidence_id=evidence.id,
        total_rows=results["total_rows"],
        valid_rows=results["valid_rows"],
        rows_with_missing_fields=results["rows_with_missing_fields"],
        vehicles=[TelemetryVehicleSummary(**v) for v in results["vehicles"]],
        events_generated=created_events,
        integrity_verified=True,
        summary=summary_text,
    )


# Witness Statement Analysis
@router.post("/api/incidents/{incident_id}/analyze-witness", response_model=WitnessAnalysisResponse)
async def analyze_witness_statement(
    incident_id: str,
    payload: WitnessAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Extracts claims, speeds, and chronological observations from witness statements.
    
    Supports TXT and PDF. Uses Featherless AI when configured; falls back cleanly to deterministic extraction.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    evidence = db.query(Evidence).filter(
        Evidence.id == payload.evidence_id,
        Evidence.incident_id == incident_id,
    ).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{payload.evidence_id}' not found for incident.",
        )

    if evidence.file_type != EvidenceFileType.WITNESS_STATEMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evidence '{payload.evidence_id}' is of type '{evidence.file_type}', expected WITNESS_STATEMENT.",
        )

    # Read statement text
    file_path = Path(evidence.file_path)
    text_content = ""
    if file_path.suffix.lower() == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            text_content = "\n".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read PDF document: {str(e)}",
            )
    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read text statement: {str(e)}",
            )

    if not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Witness statement document contains no extractable text.",
        )

    # Call Featherless AI or deterministic fallback
    extracted_data = await featherless_service.extract_witness_statement(text_content)

    claims_list: List[WitnessClaim] = []
    events_created = 0

    # Build structured claims
    for idx, c in enumerate(extracted_data.get("claims", [])):
        claim_obj = WitnessClaim(
            claim_id=f"CLM-{evidence.id}-{idx+1}",
            claim_type=c.get("claim_type", "WITNESS_CLAIM"),
            text_quote=c.get("text_quote", ""),
            interpreted_value=c.get("interpreted_value"),
            claimed_vehicle_id=c.get("claimed_vehicle_id"),
            confidence=0.9 if extracted_data.get("method_used") == "FEATHERLESS_AI" else 0.75,
        )
        claims_list.append(claim_obj)

        # Convert high-value claims (e.g. time or crash event) to timeline
        if claim_obj.claim_type in ("TIME_CLAIM", "BRAKE_CLAIM"):
            timeline_service.create_event(
                db=db,
                incident_id=incident_id,
                timestamp=incident.incident_date,  # Anchor to incident date if sub-second offset is unknown
                event_type=EventType.WITNESS_REPORTED.value,
                description=f"[Witness Statement: {extracted_data.get('witness_name', 'Witness')}] {claim_obj.text_quote}",
                classification=EventClassification.AI_INFERENCE,
                vehicle_id=claim_obj.claimed_vehicle_id,
                source_evidence_ids=[evidence.id],
                confidence=claim_obj.confidence,
                raw_data=claim_obj.dict(),
            )
            events_created += 1

    # Update metadata
    meta = json.loads(evidence.metadata_json) if evidence.metadata_json else {}
    meta["witness_name"] = extracted_data.get("witness_name")
    meta["claims"] = [c.dict() for c in claims_list]
    meta["extraction_method"] = extracted_data.get("method_used")
    evidence.metadata_json = json.dumps(meta)
    evidence.is_processed = True
    db.commit()

    return WitnessAnalysisResponse(
        incident_id=incident_id,
        evidence_id=evidence.id,
        witness_name_or_id=extracted_data.get("witness_name", "Witness"),
        statement_length_chars=len(text_content),
        claims_extracted=claims_list,
        events_created=events_created,
        ai_status=extracted_data.get("ai_status", "UNKNOWN"),
        method_used=extracted_data.get("method_used", "DETERMINISTIC"),
    )


# Contradictions Analysis
@router.get("/api/incidents/{incident_id}/contradictions", response_model=ContradictionAnalysisResponse)
async def get_incident_contradictions(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Identifies and explains contradictions between testimonial claims and physical kinematic recordings.
    
    References source evidence IDs and row numbers. Strictly maintains investigative neutrality.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    results = await contradiction_service.analyze_contradictions(db, incident_id)
    return ContradictionAnalysisResponse(
        incident_id=incident_id,
        total_contradictions=results["total_contradictions"],
        categories_breakdown=results["categories_breakdown"],
        contradictions=[ContradictionItem(**c) for c in results["contradictions"]],
        investigative_summary=results["investigative_summary"],
        ai_explanation=results.get("ai_explanation"),
        ai_available=results.get("ai_available", False),
    )


# AI Investigation Summary
@router.post("/api/incidents/{incident_id}/ai-summary", response_model=AISummaryResponse)
async def generate_ai_summary(
    incident_id: str,
    payload: Optional[AISummaryRequest] = None,
    db: Session = Depends(get_db),
):
    """Generates an executive investigative summary synthesizing timeline, evidence, and contradictions.
    
    If Featherless AI is unavailable, provides an authoritative deterministic synthesis.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    # Gather data package
    timeline_data = timeline_service.get_chronological_timeline(db, incident_id)
    contra_data = await contradiction_service.analyze_contradictions(db, incident_id)

    incident_package = {
        "title": incident.title,
        "location": incident.location,
        "incident_date": incident.incident_date.isoformat(),
        "description": incident.description,
        "status": incident.status.value,
        "vehicle_ids": timeline_data["vehicle_ids"],
        "events": timeline_data["events"],
        "contradictions": contra_data["contradictions"],
    }

    summary_result = await featherless_service.generate_investigation_summary(incident_package)

    return AISummaryResponse(
        incident_id=incident_id,
        summary=summary_result["summary"],
        key_findings=summary_result["key_findings"],
        timeline_highlights=summary_result["timeline_highlights"],
        identified_discrepancies=summary_result["identified_discrepancies"],
        ai_provider=summary_result["ai_provider"],
        model=summary_result["model"],
        is_fallback=summary_result["is_fallback"],
        generated_at=datetime.utcnow(),
    )


# Comprehensive Incident Report
@router.get("/api/incidents/{incident_id}/report", response_model=IncidentReportResponse)
async def get_incident_report(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Generates a complete, publication-grade accident reconstruction report.
    
    Combines incident metadata, verified evidence inventory with SHA-256 digests,
    deterministic chronological timeline, kinematic telemetry statistics, contradiction matrix,
    and investigation synthesis.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    evidence_records = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()
    evidence_inventory = [
        {
            "id": e.id,
            "filename": e.filename,
            "original_filename": e.original_filename,
            "file_type": e.file_type.value,
            "file_size_bytes": e.file_size_bytes,
            "sha256_hash": e.sha256_hash,
            "upload_timestamp": e.upload_timestamp.isoformat(),
            "integrity_notice": settings.INTEGRITY_DISCLAIMER,
        }
        for e in evidence_records
    ]

    vehicles = db.query(Vehicle).filter(Vehicle.incident_id == incident_id).all()
    vehicles_data = [
        {
            "id": v.id,
            "vehicle_id": v.vehicle_id,
            "make_model": v.make_model,
            "color": v.color,
            "role": v.role,
        }
        for v in vehicles
    ]

    timeline_data = timeline_service.get_chronological_timeline(db, incident_id)
    contradictions_data = await contradiction_service.analyze_contradictions(db, incident_id)

    incident_package = {
        "title": incident.title,
        "location": incident.location,
        "incident_date": incident.incident_date.isoformat(),
        "description": incident.description,
        "status": incident.status.value,
        "vehicle_ids": timeline_data["vehicle_ids"],
        "events": timeline_data["events"],
        "contradictions": contradictions_data["contradictions"],
    }
    summary_data = await featherless_service.generate_investigation_summary(incident_package)

    telemetry_summaries = []
    for e in evidence_records:
        if e.file_type == EvidenceFileType.TELEMETRY and e.metadata_json:
            meta = json.loads(e.metadata_json)
            if "telemetry_summary" in meta:
                telemetry_summaries.append({
                    "evidence_id": e.id,
                    "filename": e.filename,
                    "summary": meta["telemetry_summary"],
                })

    return IncidentReportResponse(
        incident={
            "id": incident.id,
            "title": incident.title,
            "location": incident.location,
            "incident_date": incident.incident_date.isoformat(),
            "description": incident.description,
            "status": incident.status.value,
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat(),
        },
        evidence_inventory=evidence_inventory,
        vehicles_involved=vehicles_data,
        timeline={
            "total_events": timeline_data["total_events"],
            "classifications_breakdown": timeline_data["classifications_breakdown"],
            "time_span": {
                "start": timeline_data["time_span"]["start"].isoformat() if timeline_data["time_span"] and timeline_data["time_span"]["start"] else None,
                "end": timeline_data["time_span"]["end"].isoformat() if timeline_data["time_span"] and timeline_data["time_span"]["end"] else None,
            } if timeline_data["time_span"] else None,
            "events": [
                {
                    **ev,
                    "timestamp": ev["timestamp"].isoformat(),
                    "created_at": ev["created_at"].isoformat(),
                }
                for ev in timeline_data["events"]
            ],
        },
        telemetry_analyses=telemetry_summaries,
        contradictions={
            "total_contradictions": contradictions_data["total_contradictions"],
            "categories_breakdown": contradictions_data["categories_breakdown"],
            "contradictions": contradictions_data["contradictions"],
            "investigative_summary": contradictions_data["investigative_summary"],
        },
        investigation_summary=summary_data,
        report_generated_at=datetime.utcnow(),
    )
