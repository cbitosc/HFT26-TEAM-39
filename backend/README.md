# TRACE AI — Road Accident Investigation & Reconstruction Backend

Complete Python FastAPI backend for **TRACE AI**, an AI-powered road accident investigation and kinematic reconstruction prototype.

## 1. Technology Stack

- **Python 3.11+**
- **FastAPI**: Asynchronous high-performance REST framework
- **Uvicorn**: ASGI web server
- **SQLite & SQLAlchemy 2.0**: Relational case storage and ACID transactions
- **Pydantic v2**: Strict schema validation and data serialization
- **Pandas & NumPy**: Telemetry validation, numerical bounds checking, and kinematic derivation
- **OpenCV (opencv-python-headless)**: Computer vision module for frame extraction and optical flow motion tracking
- **Featherless AI**: Secure server-side LLM integration for testimonial extraction and contradiction explanation
- **PyTest**: Automated test suite

## 2. Directory Structure

```
backend/
  app/
    main.py                       # FastAPI entry point, CORS, database lifecycle
    config.py                     # Environment settings (Featherless, SQLite, Uploads)
    database.py                   # SQLAlchemy engine, session maker, get_db dependency
    models/
      incident.py                 # Incident ORM model with cascade safeguards
      evidence.py                 # Evidence ORM model with SHA-256 integrity hash
      event.py                    # Event ORM model with epistemic classification
      vehicle.py                  # Vehicle identification model
    schemas/
      incident.py                 # Incident request/response schemas
      evidence.py                 # Evidence metadata and upload schemas
      timeline.py                 # Reconstructed timeline schemas
      analysis.py                 # Telemetry, video, witness, contradiction schemas
    routes/
      incidents.py                # CRUD /api/incidents endpoints
      evidence.py                 # Upload and retrieval /api/evidence endpoints
      timeline.py                 # Chronological sequence /api/incidents/{id}/timeline
      video.py                    # Computer vision /api/incidents/{id}/video/process
      analysis.py                 # Telemetry, contradictions, witness NLP, reports
    services/
      evidence_service.py         # File vault, byte-stream preservation, SHA-256
      telemetry_service.py        # CSV header & range validation, kinematics engine
      timeline_service.py         # Deterministic chronological event sequencer
      contradiction_service.py    # Neutral discrepancy cross-examination matrix
      featherless_service.py      # Secure Featherless AI client with offline fallback
      video_service.py            # Dedicated ComputerVisionService interface
    utils/
      file_validation.py          # Extension, MIME, size check, SHA-256
      timestamp.py                # ISO 8601, SQL, and Unix epoch parser
  uploads/                        # Isolated case evidence directory
  tests/
    test_api.py                   # PyTest automated test suite
  .env.example
  requirements.txt
  README.md
```

## 3. Setup and Execution

### Step 1: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env` with your settings:
```env
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./trace_ai.db
UPLOAD_DIR=./uploads
FEATHERLESS_API_KEY=your_featherless_api_key_here
FEATHERLESS_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
```

### Step 3: Run the FastAPI Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at: `http://localhost:8000/docs`.

### Step 4: Run Automated Tests
```bash
cd backend
pytest tests/ -v
```

## 4. Key Working API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, database connection, and CV status |
| `GET` | `/api/ai/status` | Featherless AI connection status and configuration |
| `POST` | `/api/incidents` | Create a new accident investigation file |
| `GET` | `/api/incidents` | List all recorded investigations |
| `GET` | `/api/incidents/{id}` | Retrieve incident details with evidence/event counts |
| `PUT` | `/api/incidents/{id}` | Update incident metadata or status |
| `DELETE`| `/api/incidents/{id}` | Safeguarded deletion (requires `?confirm=true`) |
| `POST` | `/api/incidents/{id}/evidence` | Upload evidence (MP4, MOV, AVI, TXT, PDF, CSV) |
| `GET` | `/api/incidents/{id}/evidence` | List all evidence items for an incident |
| `GET` | `/api/evidence/{id}` | Inspect evidence details and SHA-256 hash |
| `DELETE`| `/api/evidence/{id}` | Safely remove evidence record and disk file |
| `POST` | `/api/incidents/{id}/telemetry/process` | Validate CSV telemetry & derive kinematic events |
| `POST` | `/api/incidents/{id}/video/process` | Run OpenCV optical flow and tracking |
| `GET` | `/api/incidents/{id}/timeline` | Retrieve chronological timeline with filters |
| `GET` | `/api/incidents/{id}/contradictions` | Generate neutral contradiction matrix |
| `POST` | `/api/incidents/{id}/analyze-witness` | Extract claims from TXT/PDF statements |
| `POST` | `/api/incidents/{id}/ai-summary` | Generate executive investigation summary |
| `GET` | `/api/incidents/{id}/report` | Generate full publication-grade report |

## 5. Epistemic Classifications & Integrity Guarantee

1. **SHA-256 Verification Purpose**: The computed SHA-256 digest guarantees that files stored on disk have not undergone post-upload alteration or bit corruption. It verifies technical file integrity, not origin authenticity or legal chain of custody.
2. **Epistemic Classifications**:
   - `DIRECT_OBSERVATION`: Raw sensor readouts, logged brake flags, video frames.
   - `DERIVED_VALUE`: Calculated metrics ($a = \frac{dv}{dt}$, optical flow magnitudes).
   - `AI_INFERENCE`: Extracted testimonial claims and natural language parameters.
   - `MODEL_ASSUMPTION`: Extrapolations or baseline environmental coefficients.
3. **Investigative Neutrality**: The contradiction analysis engine catalogs divergences between witness accounts and physical sensor logs without automatically presuming either party is correct.
