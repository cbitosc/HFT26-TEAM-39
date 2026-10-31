import React from 'react';
import { Clock, Info } from 'lucide-react';
import Timeline from '../components/Timeline';

export default function TimelinePage({ timeline }) {
  const events = timeline?.events || [];
  const vehicleIds = timeline?.vehicle_ids || [];
  const breakdown = timeline?.classifications_breakdown || {};

  return (
    <div className="space-y-6">
      {/* Title & Explanatory Summary */}
      <div className="panel bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h1 className="page-title text-lg">Reconstructed Chronological Timeline</h1>
            <p className="page-subtitle text-xs mb-0">
              Deterministic sequence of approach, braking, kinematic deceleration, and impact points.
            </p>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Total Events: <strong className="text-slate-900">{events.length}</strong></span>
          </div>
        </div>

        {/* Epistemic Classifications Legend */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-xs">
          <div className="p-2.5 rounded bg-emerald-50/70 border border-emerald-200">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-900">
              <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
              <span>Direct Observation ({breakdown.DIRECT_OBSERVATION || 0})</span>
            </div>
            <div className="text-[11px] text-emerald-800 mt-1">Raw CAN sensor readings, recorded brake flags, video frames.</div>
          </div>

          <div className="p-2.5 rounded bg-sky-50/70 border border-sky-200">
            <div className="flex items-center gap-1.5 font-semibold text-sky-900">
              <span className="w-2 h-2 rounded-full bg-sky-600"></span>
              <span>Derived Value ({breakdown.DERIVED_VALUE || 0})</span>
            </div>
            <div className="text-[11px] text-sky-800 mt-1">Deceleration math (dv/dt), optical flow vectors, energy calculations.</div>
          </div>

          <div className="p-2.5 rounded bg-purple-50/70 border border-purple-200">
            <div className="flex items-center gap-1.5 font-semibold text-purple-900">
              <span className="w-2 h-2 rounded-full bg-purple-600"></span>
              <span>AI Inference ({breakdown.AI_INFERENCE || 0})</span>
            </div>
            <div className="text-[11px] text-purple-800 mt-1">Witness statement entity extraction and temporal positioning.</div>
          </div>

          <div className="p-2.5 rounded bg-amber-50/70 border border-amber-200">
            <div className="flex items-center gap-1.5 font-semibold text-amber-900">
              <span className="w-2 h-2 rounded-full bg-amber-600"></span>
              <span>Model Assumption ({breakdown.MODEL_ASSUMPTION || 0})</span>
            </div>
            <div className="text-[11px] text-amber-800 mt-1">Hypothesized friction coefficients and road grade baseline.</div>
          </div>
        </div>
      </div>

      {/* Main Chronological List */}
      <div className="panel bg-white">
        <Timeline events={events} vehicleIds={vehicleIds} />
      </div>
    </div>
  );
}
