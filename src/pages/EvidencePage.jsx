import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Files, Filter, RefreshCw } from 'lucide-react';
import UploadBox from '../components/UploadBox';
import EvidenceCard from '../components/EvidenceCard';

export default function EvidencePage({ incidentId, evidence = [], onRefresh }) {
  const [filterType, setFilterType] = useState('ALL');

  const filteredEvidence = evidence.filter((item) => {
    if (filterType === 'ALL') return true;
    return item.file_type === filterType;
  });

  return (
    <div className="space-y-6">
      {/* Upload Component */}
      <UploadBox
        incidentId={incidentId}
        onUploadSuccess={() => {
          if (onRefresh) onRefresh();
        }}
      />

      {/* Evidence Inventory Header & Filter */}
      <div className="panel bg-white p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 m-0">Evidence Vault & Integrity Records</h2>
            <p className="text-xs text-slate-500 m-0 mt-0.5">
              All files are stored byte-for-byte unmodified with verifiable SHA-256 checksums.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="form-select py-1 px-2 text-xs w-auto bg-white"
            >
              <option value="ALL">All Evidence Types ({evidence.length})</option>
              <option value="VIDEO">Videos (MP4/MOV/AVI)</option>
              <option value="TELEMETRY">Telemetry (CSV)</option>
              <option value="WITNESS_STATEMENT">Witness Statements (TXT/PDF)</option>
            </select>

            <button
              type="button"
              onClick={onRefresh}
              className="btn btn-secondary btn-sm"
              title="Refresh evidence list"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Evidence List */}
        <div className="p-4">
          {filteredEvidence.length === 0 ? (
            <div className="empty-state">
              <Files className="w-8 h-8 text-slate-300 mx-auto" />
              <h4>No Evidence Items</h4>
              <p className="text-xs text-slate-500">
                Use the upload box above to add dashcam video, CAN bus CSV logs, or witness statements.
              </p>
            </div>
          ) : (
            filteredEvidence.map((ev) => (
              <EvidenceCard
                key={ev.id}
                evidence={ev}
                onActionComplete={onRefresh}
                onDeleteSuccess={onRefresh}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
