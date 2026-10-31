import React, { useEffect, useState } from 'react';
import { useParams, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { Info, AlertTriangle, ShieldCheck, ArrowRight, Plus } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import WorkspaceOverview from './WorkspaceOverview';
import EvidencePage from './EvidencePage';
import TimelinePage from './TimelinePage';
import ReconstructionPage from './ReconstructionPage';
import AnalysisPage from './AnalysisPage';
import ReportsPage from './ReportsPage';
import { 
  getInvestigationCase, 
  isDemoId, 
  addEvidenceToCase 
} from '../services/investigationStore';
import { api } from '../services/api';
import ErrorBoundary from '../components/ErrorBoundary';

export default function InvestigationWorkspace() {
  const { id } = useParams();
  const location = useLocation();

  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);

  const isDemo = isDemoId(id);

  const loadCase = async () => {
    setLoading(true);

    // 1. Load authoritative case from investigationStore (demo vs user isolation)
    const storedCase = getInvestigationCase(id);

    // 2. If it's a user case and backend is online, attempt to fetch fresh backend evidence/timeline
    if (!isDemo) {
      try {
        const [incRes, evRes] = await Promise.allSettled([
          api.getIncident(id),
          api.getIncidentEvidence(id),
        ]);

        if (incRes.status === 'fulfilled' && incRes.value) {
          storedCase.incident = { ...storedCase.incident, ...incRes.value };
        }
        if (evRes.status === 'fulfilled' && Array.isArray(evRes.value)) {
          // Merge with any freshly uploaded evidence
          storedCase.evidence = evRes.value;
          storedCase.incident.evidence_count = evRes.value.length;
        }
      } catch (err) {
        // Backend offline, keep local user case state
      }
    }

    setCaseData(storedCase);
    setLoading(false);
  };

  useEffect(() => {
    loadCase();
  }, [id]);

  const handleEvidenceUploaded = (newEvidence) => {
    addEvidenceToCase(id, newEvidence);
    loadCase();
  };

  if (loading && !caseData) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 text-slate-500 text-xs">
        Loading investigation workspace data...
      </div>
    );
  }

  const { incident, evidence, timeline, contradictions, telemetryPoints, vehicles } = caseData || {};

  return (
    <div className="flex-1 flex flex-col">
      {/* Prominent Demo Investigation Read-Only Banner */}
      {isDemo && (
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 text-xs text-amber-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 z-20">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <strong className="font-semibold uppercase tracking-wide">
              Demo Investigation (Read-Only)
            </strong>
            <span className="text-amber-700 hidden sm:inline">
              — State Route 85 collision reference dataset. User-created investigations are strictly isolated.
            </span>
          </div>

          <Link
            to="/new-investigation"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-[#0b2545] text-white font-medium text-[11px] hover:bg-[#134074] transition-colors"
          >
            <Plus className="w-3 h-3" />
            <span>Create User Investigation</span>
          </Link>
        </div>
      )}

      {/* Workspace Body */}
      <div className="flex-1 flex flex-col md:flex-row bg-slate-100/50">
        <Sidebar incident={incident} />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl">
          <ErrorBoundary>
            <Routes>
              <Route
                index
                element={
                  <WorkspaceOverview
                    incident={incident}
                    evidence={evidence}
                    timeline={timeline}
                    contradictions={contradictions}
                    vehicles={vehicles}
                  />
                }
              />
              <Route
                path="evidence"
                element={
                  <EvidencePage
                    incidentId={id}
                    evidence={evidence}
                    isDemo={isDemo}
                    onRefresh={loadCase}
                  />
                }
              />
              <Route
                path="timeline"
                element={
                  <TimelinePage
                    timeline={timeline}
                    vehicles={vehicles}
                  />
                }
              />
              <Route
                path="reconstruction"
                element={
                  <ReconstructionPage
                    incident={incident}
                    timeline={timeline}
                    evidence={evidence}
                    telemetryPoints={telemetryPoints}
                    vehicles={vehicles}
                    isDemo={isDemo}
                  />
                }
              />
              <Route
                path="analysis"
                element={
                  <AnalysisPage
                    incident={incident}
                    contradictions={contradictions}
                    evidence={evidence}
                    telemetryPoints={telemetryPoints}
                    vehicles={vehicles}
                    isDemo={isDemo}
                  />
                }
              />
              <Route
                path="reports"
                element={
                  <ReportsPage
                    incident={incident}
                    evidence={evidence}
                    timeline={timeline}
                    contradictions={contradictions}
                    vehicles={vehicles}
                    isDemo={isDemo}
                  />
                }
              />
              <Route path="*" element={<Navigate to={`/investigation/${id}`} replace />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
