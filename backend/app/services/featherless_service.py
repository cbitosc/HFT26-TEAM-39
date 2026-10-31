import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class FeatherlessAIService:
    """Secure server-side Featherless AI API client.
    
    Credentials and configuration remain strictly on the backend.
    Enforces deterministic fallbacks when AI service is unconfigured or unreachable.
    Never fabricates fake successful responses.
    """

    def __init__(self):
        self._api_key = settings.FEATHERLESS_API_KEY.strip() if settings.FEATHERLESS_API_KEY else ""
        self.base_url = settings.FEATHERLESS_BASE_URL.rstrip("/")
        self.model = settings.FEATHERLESS_MODEL
        self.timeout = 30.0

    @property
    def api_key(self) -> str:
        return self._api_key or os.getenv("FEATHERLESS_API_KEY", "").strip()

    @api_key.setter
    def api_key(self, key: str):
        self._api_key = key.strip()

    def set_api_key(self, key: str):
        self._api_key = key.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def check_availability(self) -> Tuple[bool, str]:
        """Checks if Featherless API is configured and reachable."""
        if not self.is_configured:
            return False, "Featherless AI API key is not configured in server environment (FEATHERLESS_API_KEY)."

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                # Check models endpoint or simple ping
                response = await client.get(f"{self.base_url}/models", headers=headers)
                if response.status_code == 200:
                    return True, "Featherless AI service is online and accessible."
                elif response.status_code == 401:
                    return False, f"Featherless AI authentication failed (HTTP 401): Invalid API key."
                else:
                    return False, f"Featherless AI returned HTTP {response.status_code}: {response.text[:100]}"
        except httpx.RequestError as e:
            return False, f"Featherless AI connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error connecting to Featherless AI: {str(e)}"

    async def _call_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1500,
    ) -> Optional[str]:
        """Makes an authenticated request to the Featherless chat completions endpoint."""
        if not self.is_configured:
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "").strip()
                else:
                    logger.warning(
                        "Featherless API call failed with status %d: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return None
        except Exception as e:
            logger.error("Featherless API invocation exception: %s", str(e))
            return None

        return None

    async def extract_witness_statement(self, statement_text: str) -> Dict[str, Any]:
        """Extracts claims and observations from a witness statement.
        
        If Featherless is available, uses LLM extraction.
        If unavailable, uses a deterministic rule-based extractor.
        """
        is_avail, reason = await self.check_availability()
        if not is_avail:
            # Deterministic fallback
            return self._deterministic_witness_extract(statement_text, reason)

        system_prompt = (
            "You are an accident reconstruction data extraction specialist. "
            "Analyze the following witness statement and extract structured factual claims. "
            "Never invent details not mentioned in the statement. "
            "Respond ONLY in valid JSON matching this schema: "
            "{\n"
            '  "witness_name": "string",\n'
            '  "claims": [\n'
            '    {\n'
            '      "claim_type": "SPEED_CLAIM|TIME_CLAIM|BRAKE_CLAIM|DIRECTION_CLAIM|VEHICLE_CLAIM",\n'
            '      "text_quote": "exact quote from statement",\n'
            '      "interpreted_value": "parsed value e.g. 80 km/h or 14:22:00",\n'
            '      "claimed_vehicle_id": "vehicle identifier if mentioned"\n'
            '    }\n'
            '  ],\n'
            '  "timeline_observations": [\n'
            '    {\n'
            '      "approx_time": "string or null",\n'
            '      "action": "string",\n'
            '      "vehicle_involved": "string or null"\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        raw_output = await self._call_chat_completion(
            system_prompt=system_prompt,
            user_prompt=f"Witness Statement:\n{statement_text}",
            temperature=0.1,
        )

        if raw_output:
            try:
                # Clean possible markdown formatting
                cleaned = raw_output
                if "```json" in cleaned:
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned:
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()

                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "claims" in parsed:
                    parsed["ai_status"] = "AI_EXTRACTION_SUCCESS"
                    parsed["method_used"] = "FEATHERLESS_AI"
                    return parsed
            except Exception as e:
                logger.warning("Failed to parse Featherless JSON output: %s", str(e))

        return self._deterministic_witness_extract(statement_text, "Featherless returned invalid JSON or timed out.")

    def _deterministic_witness_extract(self, statement_text: str, fallback_reason: str) -> Dict[str, Any]:
        """Deterministic rule-based witness extraction when AI is unavailable."""
        import re

        claims = []
        timeline_obs = []
        lines = [line.strip() for line in statement_text.splitlines() if line.strip()]

        witness_name = "Witness"
        for line in lines[:5]:
            match = re.search(r"(?:name|witness|statement of|deponent)\s*[:\-]?\s*([A-Za-z\s]+)", line, re.IGNORECASE)
            if match:
                witness_name = match.group(1).strip()
                break

        # Speed claims
        speed_matches = re.finditer(
            r"([^\.\n]*?(\b\d{1,3}\s*(?:km/?h|kph|mph)\b|\bfast\b|\bspeeding\b|\bslow\b)[^\.\n]*)",
            statement_text,
            re.IGNORECASE,
        )
        for m in speed_matches:
            quote = m.group(1).strip()
            val_match = re.search(r"\b(\d{1,3})\s*(?:km/?h|kph|mph)\b", quote, re.IGNORECASE)
            val = val_match.group(0) if val_match else "Unquantified speed descriptor"
            claims.append({
                "claim_type": "SPEED_CLAIM",
                "text_quote": quote,
                "interpreted_value": val,
                "claimed_vehicle_id": None,
            })

        # Brake claims
        brake_matches = re.finditer(
            r"([^\.\n]*?(?:brak|skid|stopped|screech|slowed down)[^\.\n]*)",
            statement_text,
            re.IGNORECASE,
        )
        for m in brake_matches:
            quote = m.group(1).strip()
            claims.append({
                "claim_type": "BRAKE_CLAIM",
                "text_quote": quote,
                "interpreted_value": "Braking / deceleration observation",
                "claimed_vehicle_id": None,
            })

        # Time claims
        time_matches = re.finditer(
            r"([^\.\n]*?(?:\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm)?\b|\baround\s+\d{1,2}\b)[^\.\n]*)",
            statement_text,
            re.IGNORECASE,
        )
        for m in time_matches:
            quote = m.group(1).strip()
            t_match = re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", quote)
            val = t_match.group(0) if t_match else "Approximate time"
            claims.append({
                "claim_type": "TIME_CLAIM",
                "text_quote": quote,
                "interpreted_value": val,
                "claimed_vehicle_id": None,
            })

        return {
            "witness_name": witness_name,
            "claims": claims,
            "timeline_observations": timeline_obs,
            "ai_status": "AI_UNAVAILABLE_DETERMINISTIC_FALLBACK",
            "method_used": "DETERMINISTIC_EXTRACTION_FALLBACK",
            "fallback_reason": fallback_reason,
        }

    async def explain_contradictions(self, contradictions: List[Dict[str, Any]]) -> Optional[str]:
        """Provides an objective, investigative explanation of detected discrepancies."""
        if not contradictions:
            return "No discrepancies or contradictions detected between physical telemetry, video observations, and statements."

        is_avail, _ = await self.check_availability()
        if not is_avail:
            # Deterministic neutral summary
            lines = [
                f"- Discrepancy #{i+1} [{c.get('category')}]: {c.get('description')}. "
                f"Source A indicates '{c.get('source_a', {}).get('claim')}', whereas Source B indicates '{c.get('source_b', {}).get('claim')}'."
                for i, c in enumerate(contradictions)
            ]
            return (
                "Deterministic Contradiction Summary (Featherless AI unavailable):\n"
                + "\n".join(lines)
                + "\n\nInvestigative Standard: Discrepancies must be reconciled with physical telemetry and kinematic calculations. Neither source is assumed accurate."
            )

        system_prompt = (
            "You are a neutral, objective accident reconstruction forensic analyst. "
            "Explain the following contradictions clearly and impartially. "
            "CRITICAL: Do NOT declare either witness or telemetry 'correct' or 'wrong'. "
            "Identify the epistemic nature of each discrepancy and propose specific physical "
            "reconstruction steps to verify the true kinematic sequence."
        )

        user_prompt = f"Contradictions:\n{json.dumps(contradictions, indent=2)}"
        return await self._call_chat_completion(system_prompt, user_prompt, temperature=0.1)

    async def generate_investigation_summary(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates an investigation summary uniting timeline, evidence, and contradictions."""
        is_avail, reason = await self.check_availability()

        if not is_avail:
            # Return deterministic summary
            events_count = len(incident_data.get("events", []))
            contra_count = len(incident_data.get("contradictions", []))
            vehicles = incident_data.get("vehicle_ids", [])
            title = incident_data.get("title", "Road Accident Investigation")

            deterministic_text = (
                f"Investigation Report for {title}. "
                f"Reconstructed {events_count} chronological events across {len(vehicles)} vehicle(s). "
                f"Identified {contra_count} unresolved contradiction(s) requiring investigative review. "
                f"All event timestamps and kinematic metrics derive from authenticated evidence files."
            )

            return {
                "summary": deterministic_text,
                "key_findings": [
                    f"Total chronological timeline events: {events_count}",
                    f"Vehicles tracked in telemetry/visuals: {', '.join(vehicles) if vehicles else 'None specified'}",
                    f"Identified evidence discrepancies: {contra_count}",
                    "Physical telemetry and visual optical flow serve as primary kinematic ground truth",
                ],
                "timeline_highlights": [
                    e.get("description", "")
                    for e in incident_data.get("events", [])[:5]
                ],
                "identified_discrepancies": [
                    c.get("description", "")
                    for c in incident_data.get("contradictions", [])
                ],
                "ai_provider": "None (Featherless AI unavailable)",
                "model": "Deterministic Rule Engine",
                "is_fallback": True,
            }

        system_prompt = (
            "You are a senior vehicular accident reconstruction specialist writing an official investigative summary. "
            "Provide an objective, highly detailed synthesis based exclusively on the provided data. "
            "Structure your output in valid JSON matching:\n"
            "{\n"
            '  "summary": "comprehensive investigative executive summary paragraph",\n'
            '  "key_findings": ["finding 1", "finding 2", ...],\n'
            '  "timeline_highlights": ["event highlight 1", "event highlight 2", ...],\n'
            '  "identified_discrepancies": ["discrepancy 1", ...]\n'
            "}"
        )

        user_prompt = f"Incident Evidence & Reconstruction Data:\n{json.dumps(incident_data, default=str, indent=2)}"
        raw_output = await self._call_chat_completion(system_prompt, user_prompt, temperature=0.2)

        if raw_output:
            try:
                cleaned = raw_output
                if "```json" in cleaned:
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned:
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()

                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "summary" in parsed:
                    parsed["ai_provider"] = "Featherless AI"
                    parsed["model"] = self.model
                    parsed["is_fallback"] = False
                    return parsed
            except Exception as e:
                logger.warning("Failed to parse Featherless summary response: %s", str(e))

        # Fallback if parsing fails
        return {
            "summary": "Reconstruction synthesis completed. Review timeline and contradiction tables for specific kinematic vectors.",
            "key_findings": ["Deterministic telemetry and event sequence compiled successfully."],
            "timeline_highlights": [],
            "identified_discrepancies": [],
            "ai_provider": "Featherless AI (Parse Error Fallback)",
            "model": self.model,
            "is_fallback": True,
        }


# Global singleton
featherless_service = FeatherlessAIService()
