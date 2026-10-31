import React from 'react';

export default function StatusBadge({ status, type = 'status' }) {
  if (!status) return null;

  // Format label: snake_case / CONSTANT to Title Case
  const formatLabel = (str) => {
    return str
      .toLowerCase()
      .split('_')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  if (type === 'classification') {
    switch (status) {
      case 'DIRECT_OBSERVATION':
        return (
          <span className="badge badge-direct" title="Direct raw sensor readout or unmodified video frame">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            Direct Observation
          </span>
        );
      case 'DERIVED_VALUE':
        return (
          <span className="badge badge-derived" title="Mathematically calculated from sensor deltas (e.g., optical flow, acceleration)">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-600"></span>
            Derived Value
          </span>
        );
      case 'AI_INFERENCE':
        return (
          <span className="badge badge-ai" title="Extracted or synthesized via natural language processing model">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-600"></span>
            AI Inference
          </span>
        );
      case 'MODEL_ASSUMPTION':
        return (
          <span className="badge badge-assumption" title="Extrapolated or hypothesized parameter requiring validation">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
            Model Assumption
          </span>
        );
      default:
        return <span className="badge badge-closed">{formatLabel(status)}</span>;
    }
  }

  if (type === 'file_type') {
    switch (status) {
      case 'VIDEO':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
            Video (MP4/MOV)
          </span>
        );
      case 'TELEMETRY':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            Telemetry (CSV)
          </span>
        );
      case 'WITNESS_STATEMENT':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
            Statement (TXT/PDF)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            {formatLabel(status)}
          </span>
        );
    }
  }

  // Incident status
  switch (status) {
    case 'OPEN':
      return <span className="badge badge-open">Open</span>;
    case 'UNDER_INVESTIGATION':
      return <span className="badge badge-investigating">Under Investigation</span>;
    case 'RECONSTRUCTED':
      return <span className="badge badge-reconstructed">Reconstructed</span>;
    case 'CLOSED':
      return <span className="badge badge-closed">Closed</span>;
    default:
      return <span className="badge badge-closed">{formatLabel(status)}</span>;
  }
}
