# TRACE AI — Frontend

The frontend interface for **TRACE AI**, an AI-powered road accident investigation and kinematic reconstruction platform.

## Design Philosophy

- **Modern Investigative Software**: Minimal, clean, and professional enterprise aesthetic.
- **Palette**: White backgrounds, light-grey sectioning (`#F8FAFC`), deep navy primary (`#0B2545`), and subtle borders (`#E2E8F0`).
- **Zero AI-Slop**: Free from distracting dark themes, neon accents, glowing outlines, or decorative cards.
- **Epistemic Discipline**: Explicit distinction between Direct Observations, Derived Values, AI Inferences, and Model Assumptions.

## Project Structure

```
frontend/
  src/
    components/
      Navbar.jsx          # Branding, primary navigation, backend status indicator
      Sidebar.jsx         # Case workspace navigation (Overview, Evidence, Timeline, etc.)
      UploadBox.jsx       # Categorized upload (Video, Statements, CSV Telemetry)
      EvidenceCard.jsx    # Evidence card with SHA-256 integrity inspection & actions
      Timeline.jsx        # Sub-second chronological timeline with filters & citations
      VehicleCard.jsx     # Vehicle kinematic profile cards (max speed, decel, brakes)
      StatusBadge.jsx     # Clean badges for status, file types, and classifications
    pages/
      Home.jsx            # Minimal landing page with workflow explanation
      Dashboard.jsx       # Essential case metrics & recent investigations table
      NewInvestigation.jsx# Form to create new case records with immediate workspace navigation
      WorkspaceOverview.jsx# Overview hub for the selected incident
      EvidencePage.jsx    # Evidence upload, verification, and file management
      TimelinePage.jsx    # Epistemic event sequence table & classification statistics
      ReconstructionPage.jsx # 3D Three.js spatial trajectory & annotated video scrubbers
      AnalysisPage.jsx    # Contradiction matrix, telemetry curves (Recharts), witness quotes
      ReportsPage.jsx     # Printable formal engineering report & JSON export
    services/
      api.js              # Centralized Axios API client with base URL configuration
      demoData.js         # Verified demonstration case for immediate exploration
    styles/
      global.css          # Design tokens, variables, and typography
      components.css      # Enterprise styles for panels, tables, badges, and buttons
    App.jsx               # Application route definitions
    main.jsx              # React 19 entry point
  package.json
  README.md
```

## Running the Frontend

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Configuration
Create `.env` in the project root:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Launch Development Server
```bash
npm run dev
```
The application will be accessible at `http://localhost:3000` (or the configured Vite port).

### 4. Build for Production
```bash
npm run build
```

## Key Capabilities

1. **Deterministic Kinematic Scrubber**: Synchronizes vehicle CAN bus telemetry with video frames and 3D spatial positioning.
2. **Photogrammetric Accuracy Guard**: Strictly prevents converting monocular video pixels into Euclidean distances without camera calibration.
3. **Impartial Contradiction Engine**: Catalogs discrepancies between human perception and electronic sensor logs without premature presumption of truth or falsity.
4. **Verifiable Data Integrity**: Real-time SHA-256 checksums verify that uploaded files have not been corrupted or tampered with.
