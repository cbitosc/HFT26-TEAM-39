export const DEMO_CASE_ID = "DEMO-CASE-01";

// Authentic verified demonstration case: Multi-Vehicle Intersection Collision
export const DEMO_INCIDENT = {
  id: DEMO_CASE_ID,
  title: "State Route 85 & Almaden Expressway Collision",
  location: "SR-85 Northbound Exit 7, San Jose, CA",
  incident_date: "2026-10-30T14:22:15",
  description: "Two-vehicle collision involving a lead passenger sedan (Vehicle 1) and an approaching commercial utility van (Vehicle 2) near the off-ramp deceleration lane.",
  status: "UNDER_INVESTIGATION",
  created_at: "2026-10-30T14:45:00",
  updated_at: "2026-10-30T15:30:00",
  evidence_count: 3,
  event_count: 9,
  vehicle_ids: ["VEH_01", "VEH_02"],
  isDemo: true,
};

export const DEMO_EVIDENCE = [
  {
    id: "EVD-VIDEO-01",
    incident_id: "DEMO-CASE-01",
    filename: "dashcam_northbound_h264.mp4",
    original_filename: "dashcam_northbound_h264.mp4",
    file_type: "VIDEO",
    mime_type: "video/mp4",
    file_size_bytes: 48234900,
    sha256_hash: "a4c28f1190bc73901f4cbb8e84129487fa8390bce21908472910fae149830219",
    description: "Northbound forward-facing dashcam footage from secondary witness vehicle",
    vehicle_id: "VEH_02",
    upload_timestamp: "2026-10-30T14:50:12",
    is_processed: true,
    metadata: {
      cv_analysis: {
        frame_count: 450,
        fps: 30.0,
        duration_seconds: 15.0,
        resolution: "1920x1080",
        events_count: 3,
      }
    }
  },
  {
    id: "EVD-TELEM-01",
    incident_id: "DEMO-CASE-01",
    filename: "telemetry_canbus_log.csv",
    original_filename: "telemetry_canbus_log.csv",
    file_type: "TELEMETRY",
    mime_type: "text/csv",
    file_size_bytes: 145020,
    sha256_hash: "7f83a910bf38479e0a2948cde910384719283749102837482910394857102938",
    description: "High-frequency CAN bus telemetry log for Vehicle 1 and Vehicle 2",
    vehicle_id: "VEH_01",
    upload_timestamp: "2026-10-30T14:52:45",
    is_processed: true,
    metadata: {
      telemetry_summary: {
        total_rows: 32,
        valid_rows: 31,
        missing_field_rows: 1,
        vehicles: [
          {
            vehicle_id: "VEH_01",
            data_points: 18,
            min_speed_kmh: 0.0,
            max_speed_kmh: 52.4,
            avg_speed_kmh: 38.2,
            max_deceleration_mps2: 7.8,
            brake_activations_count: 1,
          },
          {
            vehicle_id: "VEH_02",
            data_points: 14,
            min_speed_kmh: 0.0,
            max_speed_kmh: 76.1,
            avg_speed_kmh: 62.0,
            max_deceleration_mps2: 9.4,
            brake_activations_count: 1,
          }
        ]
      }
    }
  },
  {
    id: "EVD-STMT-01",
    incident_id: "DEMO-CASE-01",
    filename: "witness_statement_martinez.txt",
    original_filename: "witness_statement_martinez.txt",
    file_type: "WITNESS_STATEMENT",
    mime_type: "text/plain",
    file_size_bytes: 1840,
    sha256_hash: "3b29481902837461928374950192837481920394857102938475610293847561",
    description: "Eyewitness statement from roadside bystander E. Martinez",
    vehicle_id: null,
    upload_timestamp: "2026-10-30T15:05:22",
    is_processed: true,
    metadata: {
      witness_name: "Eduardo Martinez",
      extraction_method: "DETERMINISTIC_EXTRACTION_FALLBACK",
      claims: [
        {
          claim_id: "CLM-01",
          claim_type: "SPEED_CLAIM",
          text_quote: "Vehicle 2 was speeding excessively at well over 100 km/h.",
          interpreted_value: "100 km/h"
        },
        {
          claim_id: "CLM-02",
          claim_type: "BRAKE_CLAIM",
          text_quote: "I never heard any tire screech or saw brake lights before impact.",
          interpreted_value: "Claimed no brake actuation"
        },
        {
          claim_id: "CLM-03",
          claim_type: "TIME_CLAIM",
          text_quote: "The crash happened right around 14:15.",
          interpreted_value: "14:15"
        }
      ]
    }
  }
];

export const DEMO_TIMELINE = {
  incident_id: "DEMO-CASE-01",
  total_events: 9,
  chronological_order_verified: true,
  classifications_breakdown: {
    "DIRECT_OBSERVATION": 5,
    "DERIVED_VALUE": 3,
    "AI_INFERENCE": 1,
    "MODEL_ASSUMPTION": 0
  },
  vehicle_ids: ["VEH_01", "VEH_02"],
  time_span: {
    start: "2026-10-30T14:22:10.000",
    end: "2026-10-30T14:22:18.500"
  },
  events: [
    {
      id: "EVT-001",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:10.000",
      vehicle_id: "VEH_01",
      event_type: "VEHICLE_APPROACH",
      description: "Vehicle 1 cruising in lane 2 at 52.4 km/h approaching exit 7 deceleration zone.",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [2],
      classification: "DIRECT_OBSERVATION",
      confidence: 1.0,
      raw_data: { speed_kmh: 52.4, throttle_pct: 18.0 }
    },
    {
      id: "EVT-002",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:11.200",
      vehicle_id: "VEH_02",
      event_type: "VEHICLE_APPROACH",
      description: "Vehicle 2 approaching rear sector of Vehicle 1 at recorded speed 76.1 km/h.",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [14],
      classification: "DIRECT_OBSERVATION",
      confidence: 1.0,
      raw_data: { speed_kmh: 76.1, throttle_pct: 35.0 }
    },
    {
      id: "EVT-003",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:12.400",
      vehicle_id: "VEH_01",
      event_type: "BRAKE_ACTIVATION",
      description: "Brake pedal switch engaged for Vehicle 1 (initial speed 50.8 km/h).",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [5],
      classification: "DIRECT_OBSERVATION",
      confidence: 1.0,
      raw_data: { brake_status: "ACTIVE", speed_kmh: 50.8 }
    },
    {
      id: "EVT-004",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:13.100",
      vehicle_id: "VEH_02",
      event_type: "BRAKE_ACTIVATION",
      description: "Emergency brake actuation logged for Vehicle 2 at 71.3 km/h.",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [18],
      classification: "DIRECT_OBSERVATION",
      confidence: 1.0,
      raw_data: { brake_status: "ACTIVE", speed_kmh: 71.3 }
    },
    {
      id: "EVT-005",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:13.800",
      vehicle_id: "VEH_02",
      event_type: "DECELERATION",
      description: "Severe deceleration threshold reached for Vehicle 2 (-7.40 m/s²).",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [20],
      classification: "DERIVED_VALUE",
      confidence: 0.98,
      raw_data: { acceleration_mps2: -7.4 }
    },
    {
      id: "EVT-006",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:14.900",
      vehicle_id: "VEH_02",
      event_type: "IMPACT_COLLISION",
      description: "Impact shock recorded: peak deceleration spike -9.40 m/s² with sudden pitch rate anomaly.",
      source_evidence_ids: ["EVD-TELEM-01", "EVD-VIDEO-01"],
      source_row_numbers: [22, 147],
      classification: "DERIVED_VALUE",
      confidence: 0.96,
      raw_data: { acceleration_mps2: -9.4, video_frame: 147 }
    },
    {
      id: "EVT-007",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:15.000",
      vehicle_id: null,
      event_type: "WITNESS_REPORTED",
      description: "[Witness Statement: E. Martinez] Witness observed collision near exit ramp.",
      source_evidence_ids: ["EVD-STMT-01"],
      source_row_numbers: [1],
      classification: "AI_INFERENCE",
      confidence: 0.75,
      raw_data: { witness: "E. Martinez" }
    },
    {
      id: "EVT-008",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:16.400",
      vehicle_id: "VEH_01",
      event_type: "VEHICLE_STOPPING",
      description: "Vehicle 1 came to a complete halt on right shoulder.",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [10],
      classification: "DIRECT_OBSERVATION",
      confidence: 1.0,
      raw_data: { speed_kmh: 0.0 }
    },
    {
      id: "EVT-009",
      incident_id: "DEMO-CASE-01",
      timestamp: "2026-10-30T14:22:17.200",
      vehicle_id: "VEH_02",
      event_type: "VEHICLE_STOPPING",
      description: "Vehicle 2 arrested in lane 2 following secondary yaw deflection.",
      source_evidence_ids: ["EVD-TELEM-01"],
      source_row_numbers: [25],
      classification: "DIRECT_OBSERVATION",
      confidence: 1.0,
      raw_data: { speed_kmh: 0.0 }
    }
  ]
};

export const DEMO_CONTRADICTIONS = {
  incident_id: "DEMO-CASE-01",
  total_contradictions: 2,
  categories_breakdown: {
    "SPEED_CONFLICT": 1,
    "MOVEMENT_CONFLICT": 1
  },
  investigative_summary: "Cross-examination identified 2 objective discrepancies between testimonial claims and physical kinematic recordings. Under forensic guidelines, sensor telemetry and optical tracking provide verifiable physical bounds, but human perception factors must be evaluated independently without premature presumption of falsehood.",
  ai_available: false,
  ai_explanation: "Deterministic Contradiction Summary: Discrepancy #1 demonstrates witness perceived speed (~100+ km/h) deviates by 23.9 km/h from recorded peak CAN bus telemetry (76.1 km/h). Discrepancy #2 shows witness observed no braking, whereas electronic switch logs active brake application 1.8 seconds prior to impact.",
  contradictions: [
    {
      contradiction_id: "DISC-SPD-A8102",
      category: "SPEED_CONFLICT",
      description: "Substantial variance between witness claimed speed (100.0 km/h) and recorded telemetry peak speed (76.1 km/h).",
      source_a: {
        evidence_id: "EVD-STMT-01",
        evidence_type: "WITNESS_STATEMENT",
        filename: "witness_statement_martinez.txt",
        claim: "Vehicle 2 was speeding excessively at well over 100 km/h.",
        interpreted_speed_kmh: 100.0
      },
      source_b: {
        evidence_id: ["EVD-TELEM-01"],
        evidence_type: "TELEMETRY_LOG",
        telemetry_max_speed_kmh: 76.1,
        source_rows: [14, 15, 16],
        claim: "Telemetry maximum recorded speed was 76.1 km/h."
      },
      discrepancy_details: "Discrepancy delta: 23.9 km/h variance.",
      investigative_guidance: "Investigative Neutrality: Neither source is automatically declared accurate. Witnesses frequently misjudge vehicular velocity due to auditory cues (engine noise/tire screech) or limited viewing angles. Verify vehicle speedometer calibration and CAN bus telemetry logs."
    },
    {
      contradiction_id: "DISC-BRK-B7419",
      category: "MOVEMENT_CONFLICT",
      description: "Witness stated vehicle never applied brakes, but vehicle telemetry records confirmed brake pedal actuation prior to collision.",
      source_a: {
        evidence_id: "EVD-STMT-01",
        evidence_type: "WITNESS_STATEMENT",
        filename: "witness_statement_martinez.txt",
        claim: "I never heard any tire screech or saw brake lights before impact."
      },
      source_b: {
        evidence_id: ["EVD-TELEM-01"],
        evidence_type: "TELEMETRY_LOG",
        timestamp: "2026-10-30T14:22:13.100",
        source_rows: [18, 19, 20],
        claim: "Brake switch logged ACTIVE at 2026-10-30 14:22:13.100 with deceleration onset."
      },
      discrepancy_details: "Physical CAN bus log demonstrates active hydraulic/electronic brake signal, conflicting with witness visual perception of non-braking.",
      investigative_guidance: "Investigative Neutrality: Do not infer intentional misrepresentation. Brake light circuit malfunction or late brake application behind sight obstructions can explain testimonial divergence. Inspect brake filament bulb condition."
    }
  ]
};

export const DEMO_TELEMETRY_POINTS = [
  { t: "14:22:10", veh1_speed: 52.4, veh2_speed: 76.1, veh1_accel: -0.2, veh2_accel: 0.1, veh1_brake: 0, veh2_brake: 0 },
  { t: "14:22:11", veh1_speed: 51.9, veh2_speed: 75.8, veh1_accel: -0.5, veh2_accel: -0.3, veh1_brake: 0, veh2_brake: 0 },
  { t: "14:22:12", veh1_speed: 50.8, veh2_speed: 74.2, veh1_accel: -1.2, veh2_accel: -1.0, veh1_brake: 1, veh2_brake: 0 },
  { t: "14:22:13", veh1_speed: 46.5, veh2_speed: 71.3, veh1_accel: -3.5, veh2_accel: -4.2, veh1_brake: 1, veh2_brake: 1 },
  { t: "14:22:14", veh1_speed: 38.0, veh2_speed: 52.0, veh1_accel: -5.8, veh2_accel: -7.4, veh1_brake: 1, veh2_brake: 1 },
  { t: "14:22:15", veh1_speed: 15.2, veh2_speed: 28.5, veh1_accel: -7.8, veh2_accel: -9.4, veh1_brake: 1, veh2_brake: 1 },
  { t: "14:22:16", veh1_speed: 2.1,  veh2_speed: 6.4,  veh1_accel: -4.0, veh2_accel: -5.1, veh1_brake: 1, veh2_brake: 1 },
  { t: "14:22:17", veh1_speed: 0.0,  veh2_speed: 0.8,  veh1_accel: -0.2, veh2_accel: -1.0, veh1_brake: 1, veh2_brake: 1 },
  { t: "14:22:18", veh1_speed: 0.0,  veh2_speed: 0.0,  veh1_accel: 0.0,  veh2_accel: 0.0,  veh1_brake: 0, veh2_brake: 0 },
];
