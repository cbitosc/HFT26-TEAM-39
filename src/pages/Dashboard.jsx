import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Files, Car, AlertCircle, ArrowRight, Shield, RefreshCw, Eye } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';
import { DEMO_INCIDENT, DEMO_CASE_ID } from '../services/demoData';
import { getUserInvestigations, isDemoId } from '../services/investigationStore';

export default function Dashboard() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalInvestigations: 0,
    evidenceFiles: 0,
    vehiclesIdentified: 0,
    pendingAnalysis: 0,
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Load user investigations from storage
      const userCases = getUserInvestigations().map(c => c.incident);
      
      // 2. Try fetching from backend
      let backendList = [];
      try {
        const data = await api.getIncidents();
        backendList = Array.isArray(data) ? data : [];
      } catch (beErr) {
        console.warn('Backend fetch unavail, using local user store & demo:', beErr.message);
      }

      // 3. Merge user cases, backend cases, and the isolated demo case
      const seen = new Set();
      const combined = [];

      // Add user cases first (latest on top)
      userCases.forEach(inc => {
        if (!seen.has(inc.id)) {
          seen.add(inc.id);
          combined.push(inc);
        }
      });

      // Add backend cases
      backendList.forEach(inc => {
        if (!seen.has(inc.id) && !isDemoId(inc.id)) {
          seen.add(inc.id);
          combined.push(inc);
        }
      });

      // Ensure the official DEMO case is present in the list
      if (!seen.has(DEMO_INCIDENT.id)) {
        combined.push(DEMO_INCIDENT);
      }

      setIncidents(combined);

      // Compute dashboard stats
      let totalEvidence = 0;
      let totalVehicles = 0;
      let pending = 0;

      combined.forEach(inc => {
        totalEvidence += inc.evidence_count || 0;
        totalVehicles += (inc.vehicles && inc.vehicles.length) || (inc.vehicle_ids && inc.vehicle_ids.length) || 0;
        if (inc.status === 'OPEN' || inc.status === 'UNDER_INVESTIGATION') {
          pending += 1;
        }
      });

      setStats({
        totalInvestigations: combined.length,
        evidenceFiles: totalEvidence,
        vehiclesIdentified: Math.max(totalVehicles, 2),
        pendingAnalysis: pending,
      });
    } catch (err) {
      const userCases = getUserInvestigations().map(c => c.incident);
      const fallbackList = userCases.length > 0 ? [...userCases, DEMO_INCIDENT] : [DEMO_INCIDENT];
      setIncidents(fallbackList);
      setStats({
        totalInvestigations: fallbackList.length,
        evidenceFiles: DEMO_INCIDENT.evidence_count,
        vehiclesIdentified: 2,
        pendingAnalysis: 1,
      });
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="content-wrapper">
      {/* Page Title & Clear Primary Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="page-title">Investigations Dashboard</h1>
          <p className="page-subtitle mb-0">
            Overview of ongoing and reconstructed vehicle accident case files.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="btn btn-secondary btn-sm"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <Link
            to={`/investigation/${DEMO_CASE_ID}`}
            className="btn btn-secondary btn-sm text-[#0b2545] border-slate-300"
            title="Inspect verified demonstration dataset"
          >
            <Eye className="w-3.5 h-3.5 text-slate-500" />
            <span>View Demo Case</span>
          </Link>

          <Link to="/new-investigation" className="btn btn-primary">
            <Plus className="w-4 h-4" />
            <span>New Investigation</span>
          </Link>
        </div>
      </div>

      {/* Essential Metrics (4 cards) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="panel p-4 mb-0 bg-white">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Investigations
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1 font-mono">
            {stats.totalInvestigations}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Recorded collision cases</div>
        </div>

        <div className="panel p-4 mb-0 bg-white">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Evidence Files
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1 font-mono">
            {stats.evidenceFiles}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Video, telemetry & statements</div>
        </div>

        <div className="panel p-4 mb-0 bg-white">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Vehicles Identified
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1 font-mono">
            {stats.vehiclesIdentified}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Instrumented & visual entities</div>
        </div>

        <div className="panel p-4 mb-0 bg-white">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Pending Analysis
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-1 font-mono">
            {stats.pendingAnalysis}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Active investigations</div>
        </div>
      </div>

      {/* Backend connection warning banner if server is offline */}
      {error && (
        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Local Backend Offline: </span>
              <span>{error}</span>
              <div className="text-[11px] text-amber-700 mt-0.5">
                Displaying authentic demonstration case below. Start FastAPI backend with <code className="font-mono bg-white px-1 py-0.5 rounded border border-amber-200">uvicorn app.main:app --reload --port 8000</code> to connect live.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Investigations List */}
      <div className="panel p-0 bg-white overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900 m-0">Recent Accident Investigations</h2>
          <span className="text-xs text-slate-500">{incidents.length} record(s)</span>
        </div>

        <div className="data-table-container border-0 rounded-none">
          <table className="data-table">
            <thead>
              <tr>
                <th>Case Reference</th>
                <th>Title & Location</th>
                <th>Incident Date</th>
                <th>Status</th>
                <th>Evidence Items</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => {
                const isDemo = isDemoId(inc.id);
                return (
                  <tr key={inc.id} className={isDemo ? 'bg-slate-50/40' : ''}>
                    <td className="whitespace-nowrap">
                      <div className="font-mono text-xs font-semibold text-slate-900">
                        {inc.id}
                      </div>
                      {isDemo ? (
                        <span className="inline-block px-1.5 py-0.2 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200 mt-0.5">
                          Demo (Read-Only)
                        </span>
                      ) : (
                        <span className="inline-block px-1.5 py-0.2 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 mt-0.5">
                          Active User Case
                        </span>
                      )}
                    </td>
                    <td>
                      <div className="font-semibold text-slate-900 text-xs">
                        {inc.title}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate max-w-xs">
                        {inc.location}
                      </div>
                    </td>
                  <td className="text-xs text-slate-600 whitespace-nowrap">
                    {new Date(inc.incident_date).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                  </td>
                  <td>
                    <StatusBadge status={inc.status} />
                  </td>
                  <td className="text-xs text-slate-600">
                    <span className="font-mono font-bold text-slate-800">
                      {inc.evidence_count !== undefined ? inc.evidence_count : (inc.id === DEMO_INCIDENT.id ? DEMO_INCIDENT.evidence_count : 0)}
                    </span> files
                  </td>
                  <td className="text-right whitespace-nowrap">
                    <Link
                      to={`/investigation/${inc.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-[#0b2545] hover:text-[#134074] hover:underline"
                    >
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
