import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.event import Event, EventClassification, EventType

logger = logging.getLogger(__name__)


class TimelineReconstructionService:
    """Deterministic timeline engine for road accident investigation.
    
    Reconstructs an authoritative, chronological chain of events.
    Strictly categorizes every event under epistemic classifications:
    - DIRECT_OBSERVATION: Direct sensor readouts, logged brake flags, video frames.
    - DERIVED_VALUE: Calculated metrics (e.g. deceleration from delta velocity, optical flow).
    - AI_INFERENCE: Extracted claims, NLP statement entity inferences.
    - MODEL_ASSUMPTION: Extrapolations or hypothesized impact points.
    """

    def create_event(
        self,
        db: Session,
        incident_id: str,
        timestamp: datetime,
        event_type: str,
        description: str,
        classification: EventClassification,
        vehicle_id: Optional[str] = None,
        source_evidence_ids: Optional[List[str]] = None,
        source_row_numbers: Optional[List[int]] = None,
        confidence: Optional[float] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Creates and persists an event in the database."""
        event_id = f"EVT-{uuid.uuid4().hex[:10].upper()}"
        
        event = Event(
            id=event_id,
            incident_id=incident_id,
            timestamp=timestamp,
            vehicle_id=vehicle_id,
            event_type=event_type,
            description=description,
            source_evidence_ids=json.dumps(source_evidence_ids or []),
            source_row_numbers=json.dumps(source_row_numbers or []),
            classification=classification,
            confidence=confidence,
            raw_data=json.dumps(raw_data) if raw_data else None,
        )

        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_chronological_timeline(
        self,
        db: Session,
        incident_id: str,
        vehicle_id: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieves and compiles the deterministic chronological timeline for an incident."""
        query = db.query(Event).filter(Event.incident_id == incident_id)

        if vehicle_id:
            query = query.filter(Event.vehicle_id == vehicle_id)
        if classification:
            query = query.filter(Event.classification == classification)

        # Deterministic chronological order
        events = query.order_by(Event.timestamp.asc(), Event.created_at.asc()).all()

        classifications_breakdown = {
            EventClassification.DIRECT_OBSERVATION.value: 0,
            EventClassification.DERIVED_VALUE.value: 0,
            EventClassification.AI_INFERENCE.value: 0,
            EventClassification.MODEL_ASSUMPTION.value: 0,
        }

        vehicle_set = set()
        formatted_events = []

        for e in events:
            classifications_breakdown[e.classification.value] = (
                classifications_breakdown.get(e.classification.value, 0) + 1
            )
            if e.vehicle_id:
                vehicle_set.add(e.vehicle_id)

            formatted_events.append({
                "id": e.id,
                "incident_id": e.incident_id,
                "timestamp": e.timestamp,
                "vehicle_id": e.vehicle_id,
                "event_type": e.event_type,
                "description": e.description,
                "source_evidence_ids": json.loads(e.source_evidence_ids) if e.source_evidence_ids else [],
                "source_row_numbers": json.loads(e.source_row_numbers) if e.source_row_numbers else [],
                "classification": e.classification,
                "confidence": e.confidence,
                "raw_data": json.loads(e.raw_data) if e.raw_data else None,
                "created_at": e.created_at,
            })

        time_span = None
        if events:
            time_span = {
                "start": events[0].timestamp,
                "end": events[-1].timestamp,
            }

        return {
            "incident_id": incident_id,
            "total_events": len(events),
            "chronological_order_verified": True,
            "classifications_breakdown": classifications_breakdown,
            "vehicle_ids": sorted(list(vehicle_set)),
            "time_span": time_span,
            "events": formatted_events,
        }


# Global singleton
timeline_service = TimelineReconstructionService()
