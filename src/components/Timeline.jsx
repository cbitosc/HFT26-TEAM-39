import React, { useState } from 'react';
import { Clock, Filter, FileText, CheckCircle2 } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Timeline({ events = [], vehicleIds = [] }) {
  const [selectedVehicle, setSelectedVehicle] = useState('ALL');
  const [selectedClassification, setSelectedClassification] = useState('ALL');

  // Filter events
  const filteredEvents = events.filter((e) => {
    if (selectedVehicle !== 'ALL' && e.vehicle_id !== selectedVehicle) return false;
    if (selectedClassification !== 'ALL' && e.classification !== selectedClassification) return false;
    return true;
  });

  const formatTimestamp = (ts) => {
    if (!ts) return 'Unknown Time';
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) +
      '.' + String(d.getMilliseconds()).padStart(3, '0');
  };

  return (
    <div>
      {/* Filters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-md mb-4 text-xs">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-semibold text-slate-700">Filters:</span>

          {/* Vehicle filter */}
          <select
            value={selectedVehicle}
            onChange={(e) => setSelectedVehicle(e.target.value)}
            className="form-select py-1 px-2 text-xs w-auto bg-white"
          >
            <option value="ALL">All Vehicles ({events.length})</option>
            {vehicleIds.map((v) => (
              <option key={v} value={v}>Vehicle {v}</option>
            ))}
          </select>

          {/* Classification filter */}
          <select
            value={selectedClassification}
            onChange={(e) => setSelectedClassification(e.target.value)}
            className="form-select py-1 px-2 text-xs w-auto bg-white"
          >
            <option value="ALL">All Classifications</option>
            <option value="DIRECT_OBSERVATION">Direct Observation</option>
            <option value="DERIVED_VALUE">Derived Value</option>
            <option value="AI_INFERENCE">AI Inference</option>
            <option value="MODEL_ASSUMPTION">Model Assumption</option>
          </select>
        </div>

        <div className="text-slate-500">
          Showing <strong>{filteredEvents.length}</strong> of <strong>{events.length}</strong> reconstructed events
        </div>
      </div>

      {/* Events List */}
      {filteredEvents.length === 0 ? (
        <div className="empty-state border border-slate-200 rounded-md bg-white">
          <Clock className="w-8 h-8 text-slate-300 mx-auto" />
          <h4>No Timeline Events Match Filters</h4>
          <p className="text-xs text-slate-500">Adjust the filters above or upload telemetry/video evidence to generate events.</p>
        </div>
      ) : (
        <div className="relative pl-6 border-l-2 border-slate-200 ml-4 space-y-6 my-4">
          {filteredEvents.map((evt, idx) => (
            <div key={evt.id || idx} className="relative group">
              {/* Dot */}
              <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white bg-[#0b2545] shadow-xs" />

              <div className="bg-white border border-slate-200 rounded-md p-3.5 shadow-2xs hover:border-slate-300 transition-colors">
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      {formatTimestamp(evt.timestamp)}
                    </span>
                    {evt.vehicle_id ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-900 border border-blue-200">
                        {evt.vehicle_id}
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">No vehicle isolated</span>
                    )}
                    <span className="text-xs font-mono text-slate-400">
                      {evt.event_type}
                    </span>
                  </div>

                  <StatusBadge status={evt.classification} type="classification" />
                </div>

                {/* Event Description */}
                <p className="text-xs text-slate-800 leading-relaxed font-normal m-0">
                  {evt.description}
                </p>

                {/* Evidence & Row citations */}
                <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between text-[11px] text-slate-500 gap-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span>Evidence Citation:</span>
                    {evt.source_evidence_ids && evt.source_evidence_ids.length > 0 ? (
                      evt.source_evidence_ids.map((eid) => (
                        <code key={eid} className="font-mono px-1.5 py-0.5 bg-slate-100 rounded text-slate-700 text-[10px]">
                          {eid}
                        </code>
                      ))
                    ) : (
                      <span className="italic text-slate-400">Direct log</span>
                    )}

                    {evt.source_row_numbers && evt.source_row_numbers.length > 0 && (
                      <span className="text-slate-500">
                        (Row #{evt.source_row_numbers.join(', ')})
                      </span>
                    )}
                  </div>

                  {evt.confidence !== null && evt.confidence !== undefined && (
                    <div className="text-[10px] text-slate-500 font-medium">
                      Confidence: {Math.round(evt.confidence * 100)}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
