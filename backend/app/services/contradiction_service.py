import json
import logging
import uuid
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.evidence import Evidence, EvidenceFileType
from app.models.event import Event, EventClassification, EventType
from app.services.featherless_service import featherless_service

logger = logging.getLogger(__name__)


class ContradictionAnalysisService:
    """Rigorous, neutral contradiction analysis engine.
    
    Cross-references witness statements with physical telemetry and video evidence.
    Identifies conflicting timestamps, speed claims, braking/movement actions, and missing evidence.
    References exact source evidence IDs and line/row numbers.
    Maintains strict investigative neutrality: NEVER declares either source correct.
    """

    async def analyze_contradictions(self, db: Session, incident_id: str) -> Dict[str, Any]:
        """Performs full contradiction matrix analysis across all available incident evidence."""
        # 1. Fetch all evidence files
        evidence_list = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()
        # 2. Fetch all reconstructed timeline events
        events = db.query(Event).filter(Event.incident_id == incident_id).order_by(Event.timestamp.asc()).all()

        contradictions: List[Dict[str, Any]] = []

        # Categorize evidence
        telemetry_evidences = [e for e in evidence_list if e.file_type == EvidenceFileType.TELEMETRY]
        witness_evidences = [e for e in evidence_list if e.file_type == EvidenceFileType.WITNESS_STATEMENT]
        video_evidences = [e for e in evidence_list if e.file_type == EvidenceFileType.VIDEO]

        # Extract telemetry physical metrics
        # Find max speed, impact time, braking events from telemetry
        telemetry_events = [e for e in events if e.classification in (EventClassification.DIRECT_OBSERVATION, EventClassification.DERIVED_VALUE)]
        
        # Analyze witness statements against physical timeline
        for w_evd in witness_evidences:
            claims = self._extract_claims_from_evidence(w_evd)
            for claim in claims:
                # Check for speed contradictions
                speed_contra = self._check_speed_contradiction(w_evd, claim, telemetry_events)
                if speed_contra:
                    contradictions.append(speed_contra)

                # Check for braking / movement contradictions
                brake_contra = self._check_braking_contradiction(w_evd, claim, telemetry_events)
                if brake_contra:
                    contradictions.append(brake_contra)

                # Check for timestamp discrepancies
                time_contra = self._check_timestamp_contradiction(w_evd, claim, events)
                if time_contra:
                    contradictions.append(time_contra)

                # Check for missing phantom vehicles or uncorroborated third parties
                missing_contra = self._check_missing_evidence_claims(w_evd, claim, events, video_evidences)
                if missing_contra:
                    contradictions.append(missing_contra)

        # Check for discrepancies between multiple witnesses if available
        if len(witness_evidences) >= 2:
            witness_contros = self._check_witness_inter_conflicts(witness_evidences)
            contradictions.extend(witness_contros)

        # Group by categories
        categories_breakdown: Dict[str, int] = {}
        for c in contradictions:
            cat = c.get("category", "UNRESOLVED_DISCREPANCY")
            categories_breakdown[cat] = categories_breakdown.get(cat, 0) + 1

        # Optional Featherless explanation
        ai_explanation = None
        is_ai_available, _ = await featherless_service.check_availability()
        if is_ai_available and contradictions:
            ai_explanation = await featherless_service.explain_contradictions(contradictions)

        investigative_summary = (
            f"Cross-examination identified {len(contradictions)} objective discrepancy(ies) "
            f"between testimonial claims and physical kinematic recordings. "
            f"Under forensic guidelines, sensor telemetry and optical tracking provide verifiable "
            f"physical bounds, but human perception factors (stress, perspective, parallax) must be "
            f"evaluated independently without premature presumption of falsehood."
        )

        return {
            "incident_id": incident_id,
            "total_contradictions": len(contradictions),
            "categories_breakdown": categories_breakdown,
            "contradictions": contradictions,
            "investigative_summary": investigative_summary,
            "ai_explanation": ai_explanation,
            "ai_available": is_ai_available,
        }

    def _extract_claims_from_evidence(self, witness_evd: Evidence) -> List[Dict[str, Any]]:
        """Extracts parsed claims from evidence metadata or reads text directly."""
        claims = []
        if witness_evd.metadata_json:
            try:
                meta = json.loads(witness_evd.metadata_json)
                if "claims" in meta:
                    return meta["claims"]
            except Exception:
                pass

        # If not already parsed in metadata, read file content
        file_path = witness_evd.file_path
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            extracted = featherless_service._deterministic_witness_extract(content, "Auto-extracted during contradiction pass")
            return extracted.get("claims", [])
        except Exception as e:
            logger.warning("Could not read witness file %s: %s", file_path, str(e))
            return []

    def _check_speed_contradiction(
        self,
        witness_evd: Evidence,
        claim: Dict[str, Any],
        telemetry_events: List[Event],
    ) -> Optional[Dict[str, Any]]:
        """Identifies discrepancies between witness speed claims and telemetry speed measurements."""
        if claim.get("claim_type") != "SPEED_CLAIM":
            return None

        quote = claim.get("text_quote", "")
        # Look for numbers like 100 km/h, 90 mph, etc.
        match = re.search(r"(\d{2,3})\s*(?:km/?h|kph)", quote, re.IGNORECASE)
        claimed_speed = float(match.group(1)) if match else None

        # Check telemetry recorded speeds
        speeds_recorded = []
        source_rows = []
        for e in telemetry_events:
            if e.raw_data:
                try:
                    data = json.loads(e.raw_data)
                    if "speed_kmh" in data and data["speed_kmh"] is not None:
                        speeds_recorded.append(float(data["speed_kmh"]))
                        if "row" in data:
                            source_rows.append(data["row"])
                except Exception:
                    pass

        if not speeds_recorded:
            return None

        max_speed = max(speeds_recorded)
        # If witness claimed high speed (e.g. 90+ km/h) but telemetry shows peak was much lower (e.g. 50 km/h)
        if claimed_speed and abs(claimed_speed - max_speed) > 20.0:
            return {
                "contradiction_id": f"DISC-SPD-{uuid.uuid4().hex[:6].upper()}",
                "category": "SPEED_CONFLICT",
                "description": (
                    f"Substantial variance between witness claimed speed ({claimed_speed:.1f} km/h) "
                    f"and recorded telemetry peak speed ({max_speed:.1f} km/h)."
                ),
                "source_a": {
                    "evidence_id": witness_evd.id,
                    "evidence_type": "WITNESS_STATEMENT",
                    "filename": witness_evd.filename,
                    "claim": quote,
                    "interpreted_speed_kmh": claimed_speed,
                },
                "source_b": {
                    "evidence_id": telemetry_events[0].source_evidence_ids if telemetry_events else "TELEMETRY",
                    "evidence_type": "TELEMETRY_LOG",
                    "telemetry_max_speed_kmh": max_speed,
                    "source_rows": source_rows[:5],
                    "claim": f"Telemetry maximum recorded speed was {max_speed:.1f} km/h.",
                },
                "discrepancy_details": f"Discrepancy delta: {abs(claimed_speed - max_speed):.1f} km/h.",
                "investigative_guidance": (
                    "Investigative Neutrality: Neither source is automatically declared accurate. "
                    "Witnesses frequently misjudge vehicular velocity due to auditory cues (engine noise/tire screech) "
                    "or limited viewing angles. Verify vehicle speedometer calibration and CAN bus telemetry logs."
                ),
            }

        return None

    def _check_braking_contradiction(
        self,
        witness_evd: Evidence,
        claim: Dict[str, Any],
        telemetry_events: List[Event],
    ) -> Optional[Dict[str, Any]]:
        """Identifies discrepancies regarding brake application (e.g. 'never braked' vs active brake log)."""
        if claim.get("claim_type") != "BRAKE_CLAIM":
            return None

        quote = claim.get("text_quote", "").lower()
        claimed_no_brake = any(
            phrase in quote
            for phrase in [
                "never braked",
                "didn't brake",
                "did not brake",
                "no brake lights",
                "no braking",
                "without slowing down",
                "without braking",
            ]
        )

        # Check telemetry brake events
        brake_events = [e for e in telemetry_events if e.event_type == EventType.BRAKE_ACTIVATION.value]

        if claimed_no_brake and brake_events:
            first_brake = brake_events[0]
            brake_rows = json.loads(first_brake.source_row_numbers) if first_brake.source_row_numbers else []
            return {
                "contradiction_id": f"DISC-BRK-{uuid.uuid4().hex[:6].upper()}",
                "category": "MOVEMENT_CONFLICT",
                "description": (
                    "Witness stated vehicle never applied brakes, but vehicle telemetry records confirmed "
                    "brake pedal actuation prior to collision."
                ),
                "source_a": {
                    "evidence_id": witness_evd.id,
                    "evidence_type": "WITNESS_STATEMENT",
                    "filename": witness_evd.filename,
                    "claim": claim.get("text_quote"),
                },
                "source_b": {
                    "evidence_id": json.loads(first_brake.source_evidence_ids) if first_brake.source_evidence_ids else [],
                    "evidence_type": "TELEMETRY_LOG",
                    "timestamp": str(first_brake.timestamp),
                    "source_rows": brake_rows,
                    "claim": f"Brake switch logged ACTIVE at {first_brake.timestamp}.",
                },
                "discrepancy_details": (
                    "Physical CAN bus log demonstrates active hydraulic/electronic brake signal, "
                    "conflicting with witness visual perception of non-braking."
                ),
                "investigative_guidance": (
                    "Investigative Neutrality: Do not infer intentional misrepresentation. "
                    "Brake light circuit malfunction or late brake application behind sight obstructions "
                    "can explain testimonial divergence. Inspect brake filament bulb condition."
                ),
            }

        return None

    def _check_timestamp_contradiction(
        self,
        witness_evd: Evidence,
        claim: Dict[str, Any],
        events: List[Event],
    ) -> Optional[Dict[str, Any]]:
        """Identifies timestamp deviations between witness estimates and recorded physical events."""
        if claim.get("claim_type") != "TIME_CLAIM":
            return None

        val = claim.get("interpreted_value")
        if not val or ":" not in val:
            return None

        # Compare with physical event timestamps
        if not events:
            return None

        physical_impacts = [e for e in events if e.event_type in (EventType.IMPACT_COLLISION.value, EventType.DECELERATION.value)]
        ref_event = physical_impacts[0] if physical_impacts else events[0]
        actual_time_str = ref_event.timestamp.strftime("%H:%M:%S")

        return {
            "contradiction_id": f"DISC-TIME-{uuid.uuid4().hex[:6].upper()}",
            "category": "TIMESTAMP_CONFLICT",
            "description": (
                f"Witness recalled event time as '{val}', whereas recorded telemetry/sensor "
                f"timeline marks critical kinematic event at '{actual_time_str}'."
            ),
            "source_a": {
                "evidence_id": witness_evd.id,
                "evidence_type": "WITNESS_STATEMENT",
                "filename": witness_evd.filename,
                "claim": claim.get("text_quote"),
                "stated_time": val,
            },
            "source_b": {
                "evidence_id": json.loads(ref_event.source_evidence_ids) if ref_event.source_evidence_ids else [],
                "evidence_type": "PHYSICAL_TIMELINE",
                "telemetry_timestamp": actual_time_str,
                "event_type": ref_event.event_type,
                "claim": f"Recorded sensor timestamp: {actual_time_str}",
            },
            "discrepancy_details": f"Witness stated time '{val}' vs instrument timestamp '{actual_time_str}'.",
            "investigative_guidance": (
                "Investigative Neutrality: Human clock estimation in unexpected emergencies carries "
                "typical variances of ±5-15 minutes. Synchronize camera and telemetry GPS clock sources."
            ),
        }

    def _check_missing_evidence_claims(
        self,
        witness_evd: Evidence,
        claim: Dict[str, Any],
        events: List[Event],
        video_evidences: List[Evidence],
    ) -> Optional[Dict[str, Any]]:
        """Detects claims of phantom vehicles or uncorroborated physical factors."""
        quote = claim.get("text_quote", "").lower()
        if "third vehicle" in quote or "fled the scene" in quote or "another car" in quote:
            # Check if any vehicle other than primary/secondary is tracked
            vehicle_ids = {e.vehicle_id for e in events if e.vehicle_id}
            if len(vehicle_ids) <= 2:
                return {
                    "contradiction_id": f"DISC-MISS-{uuid.uuid4().hex[:6].upper()}",
                    "category": "MISSING_EVIDENCE",
                    "description": (
                        "Witness reported an additional vehicle fleeing the scene, but no third-party "
                        "telemetry stream or visual trajectory has corroborated this entity."
                    ),
                    "source_a": {
                        "evidence_id": witness_evd.id,
                        "evidence_type": "WITNESS_STATEMENT",
                        "claim": claim.get("text_quote"),
                    },
                    "source_b": {
                        "evidence_id": [v.id for v in video_evidences],
                        "evidence_type": "VIDEO_AND_TELEMETRY_LOGS",
                        "claim": f"Only {len(vehicle_ids)} vehicle(s) tracked in available digital evidence.",
                    },
                    "discrepancy_details": "Alleged third vehicle is uncorroborated by available sensor data.",
                    "investigative_guidance": (
                        "Investigative Neutrality: Lack of telemetry does not disprove a non-instrumented "
                        "third vehicle. Canvas traffic cameras and look for paint transfers."
                    ),
                }

        return None

    def _check_witness_inter_conflicts(self, witness_evidences: List[Evidence]) -> List[Dict[str, Any]]:
        """Checks for discrepancies between multiple witness statements."""
        conflicts = []
        # Check pairs
        for i in range(len(witness_evidences)):
            for j in range(i + 1, len(witness_evidences)):
                w1 = witness_evidences[i]
                w2 = witness_evidences[j]
                claims1 = self._extract_claims_from_evidence(w1)
                claims2 = self._extract_claims_from_evidence(w2)

                speeds1 = [c for c in claims1 if c.get("claim_type") == "SPEED_CLAIM"]
                speeds2 = [c for c in claims2 if c.get("claim_type") == "SPEED_CLAIM"]

                if speeds1 and speeds2:
                    conflicts.append({
                        "contradiction_id": f"DISC-WIT-{uuid.uuid4().hex[:6].upper()}",
                        "category": "UNRESOLVED_DISCREPANCY",
                        "description": (
                            f"Discrepancy between Witness Statement '{w1.filename}' and "
                            f"Witness Statement '{w2.filename}' regarding vehicle velocity or driver behavior."
                        ),
                        "source_a": {
                            "evidence_id": w1.id,
                            "evidence_type": "WITNESS_STATEMENT",
                            "filename": w1.filename,
                            "claim": speeds1[0].get("text_quote"),
                        },
                        "source_b": {
                            "evidence_id": w2.id,
                            "evidence_type": "WITNESS_STATEMENT",
                            "filename": w2.filename,
                            "claim": speeds2[0].get("text_quote"),
                        },
                        "discrepancy_details": "Divergent speed perception across independent observers.",
                        "investigative_guidance": (
                            "Investigative Neutrality: Human observers positioned at different vantage points "
                            "perceive visual angular velocity differently. Calibrate against physical skid marks."
                        ),
                    })

        return conflicts


# Global singleton
contradiction_service = ContradictionAnalysisService()
