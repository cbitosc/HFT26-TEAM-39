import React from 'react';
import { Car, Activity, ShieldAlert } from 'lucide-react';

export default function VehicleCard({ vehicle, summary }) {
  const vehId = vehicle?.vehicle_id || summary?.vehicle_id || 'UNKNOWN';

  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 shadow-2xs hover:border-slate-300 transition-colors">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-slate-100 border border-slate-200 text-[#0b2545] flex items-center justify-center font-bold text-xs">
            <Car className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900 m-0">{vehId}</h4>
            <div className="text-[11px] text-slate-500">
              {vehicle?.make_model ? `${vehicle.make_model} (${vehicle.color || 'Unknown color'})` : 'Tracked Telemetry Entity'}
            </div>
          </div>
        </div>

        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold border border-slate-200">
          {vehicle?.role || 'TARGET_VEHICLE'}
        </span>
      </div>

      {summary ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="p-2 bg-slate-50 rounded border border-slate-100">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Max Speed</div>
            <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">
              {summary.max_speed_kmh !== null ? `${summary.max_speed_kmh} km/h` : 'N/A'}
            </div>
          </div>

          <div className="p-2 bg-slate-50 rounded border border-slate-100">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Avg Speed</div>
            <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">
              {summary.avg_speed_kmh !== null ? `${summary.avg_speed_kmh} km/h` : 'N/A'}
            </div>
          </div>

          <div className="p-2 bg-slate-50 rounded border border-slate-100">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Max Decel</div>
            <div className="font-mono font-bold text-slate-900 text-sm mt-0.5 text-amber-700">
              {summary.max_deceleration_mps2 ? `${summary.max_deceleration_mps2} m/s²` : '0 m/s²'}
            </div>
          </div>

          <div className="p-2 bg-slate-50 rounded border border-slate-100">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Brakes Logged</div>
            <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">
              {summary.brake_activations_count || 0} event(s)
            </div>
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-500 italic py-2">
          Telemetry data stream active. Kinematic summary awaiting CSV batch run.
        </div>
      )}
    </div>
  );
}
