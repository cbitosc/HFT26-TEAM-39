import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Plus, 
  Trash2, 
  Car, 
  FileText, 
  Activity, 
  ShieldAlert, 
  CheckCircle2,
  Sparkles,
  Info
} from 'lucide-react';
import { createInvestigationRecord } from '../services/investigationStore';
import { api } from '../services/api';

export default function NewInvestigation() {
  const navigate = useNavigate();

  // 1. Basic Metadata State
  const [title, setTitle] = useState('');
  const [location, setLocation] = useState('');
  const [incidentDate, setIncidentDate] = useState(() => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  });
  const [description, setDescription] = useState('');

  // 2. Dynamic Vehicle Profiles & Kinematic Intake State
  const [vehicles, setVehicles] = useState([
    {
      vehicle_id: 'VEH_01',
      role: 'Lead Vehicle (Sedan)',
      make_model: 'Sedan',
      color: 'Silver',
      max_speed_kmh: '55.0',
      avg_speed_kmh: '42.0',
      max_deceleration_mps2: '6.8',
      brake_activations_count: '1',
    },
    {
      vehicle_id: 'VEH_02',
      role: 'Approaching Vehicle (Van)',
      make_model: 'Utility Van',
      color: 'White',
      max_speed_kmh: '78.5',
      avg_speed_kmh: '65.0',
      max_deceleration_mps2: '9.2',
      brake_activations_count: '1',
    }
  ]);

  // 3. Initial Testimonial & Observational Claims State
  const [witnessClaims, setWitnessClaims] = useState([
    {
      witness_name: 'Eyewitness A. Carter',
      target_vehicle_id: 'VEH_02',
      claimed_speed_kmh: '100.0',
      statement_text: 'Vehicle 2 was traveling fast, easily over 100 km/h, and appeared not to brake before impact.',
    }
  ]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Dynamic Vehicle Handlers
  const handleAddVehicle = () => {
    const nextNum = vehicles.length + 1;
    setVehicles([
      ...vehicles,
      {
        vehicle_id: `VEH_${nextNum < 10 ? '0' + nextNum : nextNum}`,
        role: nextNum === 1 ? 'Lead Vehicle' : nextNum === 2 ? 'Following Vehicle' : 'Involved Vehicle',
        make_model: '',
        color: '',
        max_speed_kmh: '50.0',
        avg_speed_kmh: '40.0',
        max_deceleration_mps2: '5.0',
        brake_activations_count: '1',
      }
    ]);
  };

  const handleRemoveVehicle = (index) => {
    if (vehicles.length <= 1) {
      alert('An investigation requires at least one participating vehicle.');
      return;
    }
    setVehicles(vehicles.filter((_, i) => i !== index));
  };

  const handleVehicleChange = (index, field, value) => {
    const updated = [...vehicles];
    updated[index][field] = value;
    setVehicles(updated);
  };

  // Dynamic Witness Handlers
  const handleAddWitness = () => {
    setWitnessClaims([
      ...witnessClaims,
      {
        witness_name: '',
        target_vehicle_id: vehicles[0]?.vehicle_id || 'VEH_01',
        claimed_speed_kmh: '',
        statement_text: '',
      }
    ]);
  };

  const handleRemoveWitness = (index) => {
    setWitnessClaims(witnessClaims.filter((_, i) => i !== index));
  };

  const handleWitnessChange = (index, field, value) => {
    const updated = [...witnessClaims];
    updated[index][field] = value;
    setWitnessClaims(updated);
  };

  // Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !location.trim() || !incidentDate || !description.trim()) {
      setError('Please fill in all required basic incident fields.');
      return;
    }

    if (vehicles.length === 0) {
      setError('Please define at least one vehicle involved in the collision.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      // 1. Create full investigation record in local user store with auto-derived kinematics
      const createdCase = createInvestigationRecord({
        title: title.trim(),
        location: location.trim(),
        incident_date: new Date(incidentDate).toISOString(),
        description: description.trim(),
        vehicles: vehicles,
        witness_claims: witnessClaims.filter(w => w.witness_name.trim() || w.statement_text.trim()),
      });

      // 2. Redirect immediately to the new investigation workspace!
      navigate(`/investigation/${createdCase.incident.id}`);
    } catch (err) {
      setError(`Failed to create investigation: ${err.message}`);
      setSubmitting(false);
    }
  };

  return (
    <div className="content-wrapper max-w-4xl py-6">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-4 transition-colors font-medium"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Dashboard</span>
      </Link>

      <div className="panel bg-white p-6">
        <div className="panel-header mb-6">
          <div>
            <h1 className="page-title text-xl">Comprehensive Accident Investigation Intake</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter incident scene parameters, vehicle kinematic baselines, and testimonial statements.
              TRACE AI computes initial deterministic timelines and discrepancy metrics immediately.
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* SECTION A: Basic Incident Metadata */}
          <div>
            <div className="flex items-center gap-2 pb-2 mb-4 border-b border-slate-200">
              <span className="w-5 h-5 rounded-full bg-[#0b2545] text-white text-[10px] font-bold flex items-center justify-center">
                1
              </span>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Basic Incident Metadata
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div className="sm:col-span-2">
                <label className="form-label text-xs">
                  Incident Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. US-101 Northbound & University Ave Collision"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="form-input text-xs"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="form-label text-xs">
                  Geographic Location <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Highway 101 MP 42.5, Palo Alto, CA"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="form-input text-xs"
                  disabled={submitting}
                />
              </div>

              <div>
                <label className="form-label text-xs">
                  Date & Time of Occurrence <span className="text-red-500">*</span>
                </label>
                <input
                  type="datetime-local"
                  required
                  value={incidentDate}
                  onChange={(e) => setIncidentDate(e.target.value)}
                  className="form-input font-mono text-xs"
                  disabled={submitting}
                />
              </div>

              <div className="sm:col-span-2">
                <label className="form-label text-xs">
                  Preliminary Narrative & Scene Conditions <span className="text-red-500">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Summarize initial roadway conditions (dry/wet), visibility, lane obstruction, and dispatch summary..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="form-textarea text-xs"
                  disabled={submitting}
                />
              </div>
            </div>
          </div>

          {/* SECTION B: Vehicle Profile & Kinematic Intake */}
          <div>
            <div className="flex items-center justify-between pb-2 mb-4 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#0b2545] text-white text-[10px] font-bold flex items-center justify-center">
                  2
                </span>
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                  Vehicle Profile & Kinematic Intake ({vehicles.length})
                </h2>
              </div>

              <button
                type="button"
                onClick={handleAddVehicle}
                className="btn btn-secondary btn-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Vehicle</span>
              </button>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Define the participating vehicles and their initial or reported kinematic baselines.
              These populate the 3D Reconstruction trajectories, velocity curves, and vehicle cards immediately.
            </p>

            <div className="space-y-4">
              {vehicles.map((veh, idx) => (
                <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-md relative">
                  <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-200/80">
                    <div className="flex items-center gap-2">
                      <Car className="w-4 h-4 text-[#0b2545]" />
                      <span className="font-mono text-xs font-bold text-slate-900">
                        {veh.vehicle_id || `Vehicle #${idx + 1}`}
                      </span>
                      <span className="text-[11px] text-slate-500">({veh.role || 'Involved'})</span>
                    </div>

                    {vehicles.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveVehicle(idx)}
                        className="text-slate-400 hover:text-red-600 text-xs p-1"
                        title="Remove vehicle"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <label className="form-label text-[11px]">Vehicle ID</label>
                      <input
                        type="text"
                        value={veh.vehicle_id}
                        onChange={(e) => handleVehicleChange(idx, 'vehicle_id', e.target.value)}
                        placeholder="e.g. VEH_01"
                        className="form-input text-xs font-mono"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Vehicle Role</label>
                      <input
                        type="text"
                        value={veh.role}
                        onChange={(e) => handleVehicleChange(idx, 'role', e.target.value)}
                        placeholder="e.g. Lead Sedan"
                        className="form-input text-xs"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Make / Model</label>
                      <input
                        type="text"
                        value={veh.make_model}
                        onChange={(e) => handleVehicleChange(idx, 'make_model', e.target.value)}
                        placeholder="e.g. Honda Accord"
                        className="form-input text-xs"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Color</label>
                      <input
                        type="text"
                        value={veh.color}
                        onChange={(e) => handleVehicleChange(idx, 'color', e.target.value)}
                        placeholder="e.g. Blue"
                        className="form-input text-xs"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Max Speed (km/h)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="300"
                        value={veh.max_speed_kmh}
                        onChange={(e) => handleVehicleChange(idx, 'max_speed_kmh', e.target.value)}
                        className="form-input text-xs font-mono"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Avg Speed (km/h)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="300"
                        value={veh.avg_speed_kmh}
                        onChange={(e) => handleVehicleChange(idx, 'avg_speed_kmh', e.target.value)}
                        className="form-input text-xs font-mono"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Max Decel (m/s²)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="30"
                        value={veh.max_deceleration_mps2}
                        onChange={(e) => handleVehicleChange(idx, 'max_deceleration_mps2', e.target.value)}
                        className="form-input text-xs font-mono text-amber-800"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Brake Activations</label>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        value={veh.brake_activations_count}
                        onChange={(e) => handleVehicleChange(idx, 'brake_activations_count', e.target.value)}
                        className="form-input text-xs font-mono"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION C: Initial Testimonial & Observational Claims */}
          <div>
            <div className="flex items-center justify-between pb-2 mb-4 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#0b2545] text-white text-[10px] font-bold flex items-center justify-center">
                  3
                </span>
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                  Initial Witness Claims & Depositions ({witnessClaims.length})
                </h2>
              </div>

              <button
                type="button"
                onClick={handleAddWitness}
                className="btn btn-secondary btn-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Witness Claim</span>
              </button>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Enter initial driver or bystander statements. TRACE AI will cross-examine claimed speeds against vehicle baselines to identify contradictions under forensic neutrality.
            </p>

            <div className="space-y-4">
              {witnessClaims.map((wit, idx) => (
                <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-md relative">
                  <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-200/80">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-purple-700" />
                      <span className="font-semibold text-xs text-slate-900">
                        {wit.witness_name || `Witness Statement #${idx + 1}`}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleRemoveWitness(idx)}
                      className="text-slate-400 hover:text-red-600 text-xs p-1"
                      title="Remove witness"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs mb-3">
                    <div>
                      <label className="form-label text-[11px]">Witness / Driver Name</label>
                      <input
                        type="text"
                        value={wit.witness_name}
                        onChange={(e) => handleWitnessChange(idx, 'witness_name', e.target.value)}
                        placeholder="e.g. Officer Miller / Driver B"
                        className="form-input text-xs"
                      />
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Target Vehicle Observed</label>
                      <select
                        value={wit.target_vehicle_id}
                        onChange={(e) => handleWitnessChange(idx, 'target_vehicle_id', e.target.value)}
                        className="form-select text-xs bg-white"
                      >
                        {vehicles.map((v) => (
                          <option key={v.vehicle_id} value={v.vehicle_id}>
                            {v.vehicle_id} ({v.role || 'Vehicle'})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="form-label text-[11px]">Claimed Speed (km/h)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={wit.claimed_speed_kmh}
                        onChange={(e) => handleWitnessChange(idx, 'claimed_speed_kmh', e.target.value)}
                        placeholder="e.g. 100"
                        className="form-input text-xs font-mono"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="form-label text-[11px]">Observed Action / Statement Text</label>
                    <textarea
                      rows={2}
                      value={wit.statement_text}
                      onChange={(e) => handleWitnessChange(idx, 'statement_text', e.target.value)}
                      placeholder="e.g. 'Vehicle was speeding excessively and made sudden swerve without braking...'"
                      className="form-textarea text-xs"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Form Submit Footer */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
            <Link
              to="/dashboard"
              className="btn btn-secondary"
            >
              Cancel
            </Link>

            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary"
            >
              {submitting ? 'Creating Case & Deriving Kinematics...' : 'Create & Open Investigation Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
