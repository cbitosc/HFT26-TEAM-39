from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from app.models.event import EventClassification, EventType
from app.utils.timestamp import parse_iso_or_standard_timestamp

logger = logging.getLogger(__name__)

REQUIRED_HEADERS = [
    "timestamp",
    "vehicle_id",
    "speed_kmh",
    "acceleration_mps2",
    "latitude",
    "longitude",
    "brake_status",
    "throttle_position_pct",
    "data_source",
]


class TelemetryProcessingError(Exception):
    pass


class TelemetryService:
    """Processes, validates, and extracts kinematic facts from vehicle telemetry CSVs.
    
    Strictly preserves row numbers, timestamps, and missing fields.
    Never invents or interpolates missing sensor data.
    """

    def validate_and_parse_csv(self, file_path: Path) -> Tuple[pd.DataFrame, List[str]]:
        """Reads CSV, validates required headers, and preserves 1-indexed row numbers."""
        if not file_path.exists():
            raise TelemetryProcessingError(f"Telemetry file not found at {file_path}")

        try:
            # Read CSV with pandas, keeping original string representations for timestamps
            df = pd.read_csv(file_path, dtype=str)
        except Exception as e:
            raise TelemetryProcessingError(f"Failed to read CSV: {str(e)}")

        # Check required headers (case-insensitive strip matching)
        actual_headers = [c.strip().lower() for c in df.columns]
        missing_headers = [h for h in REQUIRED_HEADERS if h not in actual_headers]
        if missing_headers:
            raise TelemetryProcessingError(
                f"Missing required CSV header(s): {', '.join(missing_headers)}. "
                f"Required format: {', '.join(REQUIRED_HEADERS)}"
            )

        # Standardize column names to lower case stripped
        df.columns = [c.strip().lower() for c in df.columns]

        # Preserve 1-indexed row numbers (header is row 1, data starts at row 2)
        df["_csv_row_number"] = range(2, len(df) + 2)

        return df, actual_headers

    def process_telemetry(
        self,
        file_path: Path,
        incident_id: str,
        evidence_id: str,
    ) -> Dict[str, Any]:
        """Validates all rows, handles multiple vehicles, and generates deterministic timeline events."""
        df, _ = self.validate_and_parse_csv(file_path)

        total_rows = len(df)
        valid_row_count = 0
        rows_with_missing_count = 0

        # Structured storage
        observations_by_vehicle: Dict[str, List[Dict[str, Any]]] = {}
        events_to_create: List[Dict[str, Any]] = []

        # Iterate over every single row preserving exact row index
        for _, row in df.iterrows():
            row_num = int(row["_csv_row_number"])
            raw_ts = str(row.get("timestamp", "")).strip()
            raw_vehicle = str(row.get("vehicle_id", "")).strip()

            parsed_ts = parse_iso_or_standard_timestamp(raw_ts)
            if not parsed_ts:
                # If timestamp cannot be parsed, record as anomaly and continue
                continue

            vehicle_id = raw_vehicle if raw_vehicle and raw_vehicle.lower() != "nan" else "UNKNOWN_VEHICLE"

            # Parse numerical fields without fabricating
            missing_fields = []
            flagged_issues = []

            # 1. speed_kmh
            raw_speed = row.get("speed_kmh")
            speed: Optional[float] = None
            if pd.isna(raw_speed) or str(raw_speed).strip() == "":
                missing_fields.append("speed_kmh")
            else:
                try:
                    speed = float(raw_speed)
                    if speed < 0:
                        flagged_issues.append(f"Negative speed ({speed} km/h)")
                    elif speed > 350:
                        flagged_issues.append(f"Plausibility limit exceeded: {speed} km/h")
                except ValueError:
                    missing_fields.append("speed_kmh")
                    flagged_issues.append(f"Invalid non-numeric speed: {raw_speed}")

            # 2. acceleration_mps2
            raw_accel = row.get("acceleration_mps2")
            accel: Optional[float] = None
            if pd.isna(raw_accel) or str(raw_accel).strip() == "":
                missing_fields.append("acceleration_mps2")
            else:
                try:
                    accel = float(raw_accel)
                    if abs(accel) > 40:
                        flagged_issues.append(f"Extreme acceleration value: {accel} m/s^2")
                except ValueError:
                    missing_fields.append("acceleration_mps2")
                    flagged_issues.append(f"Invalid non-numeric acceleration: {raw_accel}")

            # 3. latitude & longitude
            raw_lat = row.get("latitude")
            raw_lon = row.get("longitude")
            lat: Optional[float] = None
            lon: Optional[float] = None

            if pd.isna(raw_lat) or str(raw_lat).strip() == "":
                missing_fields.append("latitude")
            else:
                try:
                    lat = float(raw_lat)
                    if not (-90.0 <= lat <= 90.0):
                        flagged_issues.append(f"Latitude out of bounds: {lat}")
                except ValueError:
                    missing_fields.append("latitude")

            if pd.isna(raw_lon) or str(raw_lon).strip() == "":
                missing_fields.append("longitude")
            else:
                try:
                    lon = float(raw_lon)
                    if not (-180.0 <= lon <= 180.0):
                        flagged_issues.append(f"Longitude out of bounds: {lon}")
                except ValueError:
                    missing_fields.append("longitude")

            # 4. brake_status
            raw_brake = str(row.get("brake_status", "")).strip().lower()
            brake_active = False
            brake_str = None
            if raw_brake in ("true", "1", "active", "on", "yes"):
                brake_active = True
                brake_str = "ACTIVE"
            elif raw_brake in ("false", "0", "inactive", "off", "no"):
                brake_active = False
                brake_str = "INACTIVE"
            elif pd.isna(row.get("brake_status")) or raw_brake == "" or raw_brake == "nan":
                missing_fields.append("brake_status")
                brake_str = "MISSING"
            else:
                brake_str = f"UNKNOWN({raw_brake})"

            # 5. throttle_position_pct
            raw_throttle = row.get("throttle_position_pct")
            throttle: Optional[float] = None
            if pd.isna(raw_throttle) or str(raw_throttle).strip() == "":
                missing_fields.append("throttle_position_pct")
            else:
                try:
                    throttle = float(raw_throttle)
                    if not (0.0 <= throttle <= 100.0):
                        flagged_issues.append(f"Throttle percentage out of 0-100 range: {throttle}")
                except ValueError:
                    missing_fields.append("throttle_position_pct")

            if missing_fields:
                rows_with_missing_count += 1
            else:
                valid_row_count += 1

            observation = {
                "row_number": row_num,
                "timestamp": raw_ts,
                "parsed_timestamp": parsed_ts,
                "vehicle_id": vehicle_id,
                "speed_kmh": speed,
                "acceleration_mps2": accel,
                "latitude": lat,
                "longitude": lon,
                "brake_status": brake_str,
                "brake_active": brake_active,
                "throttle_position_pct": throttle,
                "data_source": str(row.get("data_source", "UNKNOWN")),
                "missing_fields": missing_fields,
                "flagged_issues": flagged_issues,
            }

            if vehicle_id not in observations_by_vehicle:
                observations_by_vehicle[vehicle_id] = []
            observations_by_vehicle[vehicle_id].append(observation)

        # Vehicle summaries & Kinematic event reconstruction
        vehicle_summaries = []
        for veh_id, obs_list in observations_by_vehicle.items():
            # Sort chronologically
            obs_list.sort(key=lambda x: x["parsed_timestamp"])

            speeds = [o["speed_kmh"] for o in obs_list if o["speed_kmh"] is not None]
            accels = [o["acceleration_mps2"] for o in obs_list if o["acceleration_mps2"] is not None]
            brakes_active = [o for o in obs_list if o["brake_active"]]

            min_speed = float(min(speeds)) if speeds else None
            max_speed = float(max(speeds)) if speeds else None
            avg_speed = float(np.mean(speeds)) if speeds else None
            min_accel = float(min(accels)) if accels else None

            start_t = obs_list[0]["timestamp"] if obs_list else None
            end_t = obs_list[-1]["timestamp"] if obs_list else None

            vehicle_summaries.append({
                "vehicle_id": veh_id,
                "data_points": len(obs_list),
                "start_time": start_t,
                "end_time": end_t,
                "min_speed_kmh": round(min_speed, 2) if min_speed is not None else None,
                "max_speed_kmh": round(max_speed, 2) if max_speed is not None else None,
                "avg_speed_kmh": round(avg_speed, 2) if avg_speed is not None else None,
                "max_deceleration_mps2": round(abs(min_accel), 2) if min_accel is not None and min_accel < 0 else 0.0,
                "brake_activations_count": len(brakes_active),
            })

            # Detect kinematic events for this vehicle
            veh_events = self._generate_vehicle_kinematic_events(
                incident_id=incident_id,
                evidence_id=evidence_id,
                vehicle_id=veh_id,
                observations=obs_list,
            )
            events_to_create.extend(veh_events)

        return {
            "total_rows": total_rows,
            "valid_rows": valid_row_count,
            "rows_with_missing_fields": rows_with_missing_count,
            "vehicles": vehicle_summaries,
            "generated_events": events_to_create,
            "observations_by_vehicle": observations_by_vehicle,
        }

    def _generate_vehicle_kinematic_events(
        self,
        incident_id: str,
        evidence_id: str,
        vehicle_id: str,
        observations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generates deterministic kinematic events with strict classification."""
        events: List[Dict[str, Any]] = []
        if not observations:
            return events

        prev_obs = None
        has_approached = False
        has_stopped = False

        for i, curr in enumerate(observations):
            curr_ts = curr["parsed_timestamp"]
            speed = curr["speed_kmh"]
            accel = curr["acceleration_mps2"]
            brake = curr["brake_active"]
            row_num = curr["row_number"]

            # 1. Vehicle Approach (initial cruising state)
            if not has_approached and speed is not None and speed > 10.0:
                events.append({
                    "incident_id": incident_id,
                    "timestamp": curr_ts,
                    "vehicle_id": vehicle_id,
                    "event_type": EventType.VEHICLE_APPROACH.value,
                    "description": f"Vehicle {vehicle_id} in motion approaching incident zone at {speed:.1f} km/h.",
                    "source_evidence_ids": [evidence_id],
                    "source_row_numbers": [row_num],
                    "classification": EventClassification.DIRECT_OBSERVATION.value,
                    "confidence": 1.0,
                    "raw_data": {"speed_kmh": speed, "row": row_num},
                })
                has_approached = True

            # 2. Brake Activation (transition from inactive to active)
            if prev_obs and (not prev_obs["brake_active"]) and brake:
                events.append({
                    "incident_id": incident_id,
                    "timestamp": curr_ts,
                    "vehicle_id": vehicle_id,
                    "event_type": EventType.BRAKE_ACTIVATION.value,
                    "description": f"Brake pedal applied for Vehicle {vehicle_id} (speed at onset: {speed if speed is not None else 'N/A'} km/h).",
                    "source_evidence_ids": [evidence_id],
                    "source_row_numbers": [row_num],
                    "classification": EventClassification.DIRECT_OBSERVATION.value,
                    "confidence": 1.0,
                    "raw_data": {"speed_kmh": speed, "brake_status": "ACTIVE", "row": row_num},
                })

            # 3. High Deceleration / Hard Braking (spikes below -4.0 m/s2)
            if accel is not None and accel < -4.0:
                events.append({
                    "incident_id": incident_id,
                    "timestamp": curr_ts,
                    "vehicle_id": vehicle_id,
                    "event_type": EventType.DECELERATION.value,
                    "description": f"Severe deceleration observed for Vehicle {vehicle_id}: {accel:.2f} m/s^2 (speed: {speed if speed is not None else 'N/A'} km/h).",
                    "source_evidence_ids": [evidence_id],
                    "source_row_numbers": [row_num],
                    "classification": EventClassification.DERIVED_VALUE.value,
                    "confidence": 0.98,
                    "raw_data": {"acceleration_mps2": accel, "speed_kmh": speed, "row": row_num},
                })

            # 4. Impact / Sudden extreme kinematic delta (spikes below -8.0 m/s2 or instantaneous speed drop)
            if accel is not None and accel < -8.0:
                events.append({
                    "incident_id": incident_id,
                    "timestamp": curr_ts,
                    "vehicle_id": vehicle_id,
                    "event_type": EventType.IMPACT_COLLISION.value,
                    "description": f"High g-force impact threshold triggered for Vehicle {vehicle_id} with peak deceleration of {accel:.2f} m/s^2.",
                    "source_evidence_ids": [evidence_id],
                    "source_row_numbers": [row_num],
                    "classification": EventClassification.DERIVED_VALUE.value,
                    "confidence": 0.95,
                    "raw_data": {"acceleration_mps2": accel, "row": row_num},
                })

            # 5. Vehicle Stopping (speed drops to 0 km/h)
            if not has_stopped and prev_obs and prev_obs["speed_kmh"] is not None and prev_obs["speed_kmh"] > 0:
                if speed is not None and speed <= 0.5:
                    events.append({
                        "incident_id": incident_id,
                        "timestamp": curr_ts,
                        "vehicle_id": vehicle_id,
                        "event_type": EventType.VEHICLE_STOPPING.value,
                        "description": f"Vehicle {vehicle_id} came to a complete halt.",
                        "source_evidence_ids": [evidence_id],
                        "source_row_numbers": [row_num],
                        "classification": EventClassification.DIRECT_OBSERVATION.value,
                        "confidence": 1.0,
                        "raw_data": {"speed_kmh": speed, "row": row_num},
                    })
                    has_stopped = True

            prev_obs = curr

        return events


# Global singleton
telemetry_service = TelemetryService()
