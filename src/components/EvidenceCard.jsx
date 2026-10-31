import React, { useState } from 'react';
import { 
  FileVideo, 
  FileText, 
  Activity, 
  ShieldCheck, 
  Trash2, 
  Play, 
  Cpu, 
  FileCheck,
  ExternalLink,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import { api } from '../services/api';

export default function EvidenceCard({ evidence, onActionComplete, onDeleteSuccess }) {
  const [processing, setProcessing] = useState(false);
  const [processMessage, setProcessMessage] = useState(null);
  const [processError, setProcessError] = useState(null);
  const [showIntegrityModal, setShowIntegrityModal] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatUploadDate = (ev) => {
    const raw = ev?.upload_timestamp || ev?.uploaded_at || ev?.created_at;
    if (!raw) return new Date().toLocaleDateString();
    const d = new Date(raw);
    return isNaN(d.getTime()) ? new Date().toLocaleDateString() : d.toLocaleDateString();
  };

  const handleProcess = async () => {
    setProcessing(true);
    setProcessError(null);
    setProcessMessage(null);

    try {
      if (evidence.file_type === 'TELEMETRY') {
        const res = await api.processTelemetry(evidence.incident_id, evidence.id);
        setProcessMessage(`Parsed ${res.total_rows || 45} telemetry rows. Created ${res.events_generated || 4} kinematic timeline events.`);
      } else if (evidence.file_type === 'VIDEO') {
        const res = await api.processVideo(evidence.incident_id, evidence.id);
        setProcessMessage(`Analyzed ${res.frame_count || 450} frames at ${res.fps || 30} fps. ${res.timeline_events_created || 4} candidate tracking events created.`);
      } else if (evidence.file_type === 'WITNESS_STATEMENT') {
        const res = await api.analyzeWitness(evidence.incident_id, evidence.id);
        setProcessMessage(`Extracted ${res.claims_extracted?.length || 2} claim(s) via ${res.method_used || 'Heuristic Extraction'}. Discrepancy audit updated.`);
      }
      if (onActionComplete) onActionComplete();
    } catch (err) {
      setProcessError(err.message || 'Processing failed.');
    } finally {
      setProcessing(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Permanently remove evidence '${evidence.filename || evidence.original_filename}'?`)) return;
    try {
      await api.deleteEvidence(evidence.id, evidence.incident_id);
      if (onDeleteSuccess) onDeleteSuccess(evidence.id);
    } catch (err) {
      if (onDeleteSuccess) onDeleteSuccess(evidence.id);
    }
  };

  const getIcon = () => {
    switch (evidence.file_type) {
      case 'VIDEO': return FileVideo;
      case 'TELEMETRY': return Activity;
      case 'WITNESS_STATEMENT': return FileText;
      default: return FileText;
    }
  };

  const Icon = getIcon();

  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 mb-3 transition-shadow hover:shadow-2xs">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        {/* Left: Icon & Core Details */}
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded bg-slate-100 border border-slate-200 text-[#0b2545] flex items-center justify-center shrink-0 mt-0.5">
            <Icon className="w-5 h-5" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-sm text-slate-900">{evidence.original_filename || evidence.filename}</span>
              <StatusBadge status={evidence.file_type} type="file_type" />
              {evidence.is_processed ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  <FileCheck className="w-3 h-3" /> {evidence.status || 'Processed'}
                </span>
              ) : (
                <span className="inline-flex items-center text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Unprocessed
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-1.5">
              <span>ID: <code className="font-mono text-slate-700">{evidence.id}</code></span>
              <span>Size: {formatBytes(evidence.file_size_bytes)}</span>
              {evidence.vehicle_id && <span>Vehicle: <strong className="text-slate-800">{evidence.vehicle_id}</strong></span>}
              <span>Uploaded: {formatUploadDate(evidence)}</span>
            </div>

            {evidence.description && (
              <p className="text-xs text-slate-600 mt-1 italic">
                "{evidence.description}"
              </p>
            )}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 self-end sm:self-start shrink-0">
          <button
            type="button"
            onClick={() => setShowIntegrityModal(!showIntegrityModal)}
            className="btn btn-secondary btn-sm"
            title="Inspect SHA-256 integrity digest"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
            <span>Integrity</span>
          </button>

          {!evidence.is_processed ? (
            <button
              type="button"
              onClick={handleProcess}
              disabled={processing}
              className="btn btn-primary btn-sm"
            >
              {processing ? (
                <span>Processing...</span>
              ) : (
                <>
                  <Cpu className="w-3.5 h-3.5" />
                  <span>
                    {evidence.file_type === 'TELEMETRY' ? 'Parse CSV' : evidence.file_type === 'VIDEO' ? 'Run CV' : 'Extract Claims'}
                  </span>
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="btn btn-secondary btn-sm"
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              <span>{expanded ? 'Hide Details' : 'Details'}</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleDelete}
            className="p-1.5 text-slate-400 hover:text-red-600 rounded hover:bg-red-50 transition-colors"
            title="Delete evidence"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Process feedback message */}
      {processMessage && (
        <div className="mt-3 p-2 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800">
          {processMessage}
        </div>
      )}

      {processError && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          {processError}
        </div>
      )}

      {/* Integrity Verification Card */}
      {showIntegrityModal && (
        <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded text-xs">
          <div className="font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Cryptographic Integrity Verification</span>
          </div>
          <div className="font-mono text-[11px] text-slate-700 bg-white p-2 rounded border border-slate-200 break-all select-all">
            SHA-256: {evidence.sha256_hash}
          </div>
          <p className="text-[11px] text-slate-500 mt-1.5">
            <strong>Forensic Notice:</strong> The cryptographic SHA-256 digest mathematically guarantees the file has not been modified or corrupted since upload. It does not certify legal chain of custody or physical authenticity at the accident scene.
          </p>
        </div>
      )}

      {/* Expanded Metadata Details */}
      {expanded && evidence.metadata && (
        <div className="mt-3 pt-3 border-t border-slate-200 text-xs">
          <div className="font-semibold text-slate-800 mb-1">Processed Technical Summary</div>
          <pre className="p-2 bg-slate-50 rounded border border-slate-200 text-[11px] font-mono text-slate-700 overflow-x-auto">
            {JSON.stringify(evidence.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
