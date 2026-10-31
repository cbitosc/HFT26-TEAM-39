import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { Files, Clock, Layers, GitFork, FileText, ArrowRight, ShieldCheck, MapPin, Calendar } from 'lucide-react';
import VehicleCard from '../components/VehicleCard';
import StatusBadge from '../components/StatusBadge';

export default function WorkspaceOverview({ incident, evidence = [], timeline, contradictions, vehicles = [] }) {
  const { id } = useParams();
  const incidentId = id || incident?.id;

  const vehicleList = (vehicles && vehicles.length > 0)
    ? vehicles
    : (incident?.vehicles && incident.vehicles.length > 0)
    ? incident.vehicles
    : (timeline?.vehicle_ids || []).map((vId) => ({
        vehicle_id: vId,
        role: 'Identified Vehicle',
        max_speed_kmh: 0,
        avg_speed_kmh: 0,
        max_deceleration_mps2: 0,
        brake_activations_count: 0,
      }));

  return (
    <div className="space-y-6">
      {/* Header Overview Banner */}
      <div className="panel bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold text-slate-500">{incidentId}</span>
              <StatusBadge status={incident?.status || 'UNDER_INVESTIGATION'} />
            </div>
            <h1 className="text-xl font-bold text-slate-900 m-0">{incident?.title}</h1>
          </div>

          <Link
            to={`/investigation/${incidentId}/reports`}
            className="btn btn-secondary btn-sm self-start sm:self-center"
          >
            <FileText className="w-3.5 h-3.5 text-slate-600" />
            <span>Generate Report</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
            <span><strong>Location:</strong> {incident?.location}</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
            <span>
              <strong>Date & Time:</strong> {new Date(incident?.incident_date || Date.now()).toLocaleString([], { dateStyle: 'full', timeStyle: 'medium' })}
            </span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-700 leading-relaxed">
          <strong>Narrative:</strong> {incident?.description}
        </div>
      </div>

      {/* Investigation Metrics Quick Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Link
          to={`/investigation/${incidentId}/evidence`}
          className="panel p-4 mb-0 bg-white hover:border-[#0b2545] transition-colors group"
        >
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-semibold uppercase">Evidence Files</span>
            <Files className="w-4 h-4 text-slate-400 group-hover:text-[#0b2545]" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900">
            {evidence.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <span>Manage files</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Link>

        <Link
          to={`/investigation/${incidentId}/timeline`}
          className="panel p-4 mb-0 bg-white hover:border-[#0b2545] transition-colors group"
        >
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-semibold uppercase">Timeline Events</span>
            <Clock className="w-4 h-4 text-slate-400 group-hover:text-[#0b2545]" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900">
            {timeline?.total_events || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <span>Chronology</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Link>

        <Link
          to={`/investigation/${incidentId}/reconstruction`}
          className="panel p-4 mb-0 bg-white hover:border-[#0b2545] transition-colors group"
        >
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-semibold uppercase">Kinematics</span>
            <Layers className="w-4 h-4 text-slate-400 group-hover:text-[#0b2545]" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900">
            {vehicleList.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <span>3D & Video</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Link>

        <Link
          to={`/investigation/${incidentId}/analysis`}
          className="panel p-4 mb-0 bg-white hover:border-[#0b2545] transition-colors group"
        >
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-semibold uppercase">Discrepancies</span>
            <GitFork className="w-4 h-4 text-slate-400 group-hover:text-[#0b2545]" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-700">
            {contradictions?.total_contradictions || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <span>Cross-examine</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Link>
      </div>

      {/* Tracked Vehicles Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-900 m-0">Participating Vehicles & Kinematic Intake</h2>
          <span className="text-xs text-slate-500">{vehicleList.length} vehicle(s) tracked</span>
        </div>

        {vehicleList.length === 0 ? (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded text-xs text-slate-500 text-center">
            No vehicle profiles currently defined. Upload telemetry CSV or edit case intake.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {vehicleList.map((v) => (
              <VehicleCard
                key={v.vehicle_id || v.id}
                vehicle={v}
                summary={{
                  vehicle_id: v.vehicle_id,
                  max_speed_kmh: v.max_speed_kmh,
                  avg_speed_kmh: v.avg_speed_kmh,
                  max_deceleration_mps2: v.max_deceleration_mps2,
                  brake_activations_count: v.brake_activations_count,
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Forensic Integrity Notice */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-600 flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">TRACE AI Epistemic Rule: </span>
          Direct observations (sensor readings, video frames) are strictly separated from derived kinematic values (accelerations, optical flow) and AI inferences. Neither testimonial claims nor sensor streams are prematurely assumed correct without multi-factor verification.
        </div>
      </div>
    </div>
  );
}
