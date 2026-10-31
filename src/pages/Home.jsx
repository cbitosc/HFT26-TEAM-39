import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Activity, Cpu, GitFork, FileText, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const workflowSteps = [
    {
      step: '01',
      title: 'Multimodal Ingestion',
      description: 'Upload dashcam/CCTV footage, CAN bus telemetry CSV logs, and witness statements. Each file receives a SHA-256 cryptographic digest to verify integrity.',
      icon: Activity,
    },
    {
      step: '02',
      title: 'Deterministic Kinematics',
      description: 'Validate sensor readings across multiple vehicles. Detect approach velocity, brake pedal engagement, deceleration spikes, and vehicle stop states without data interpolation.',
      icon: Cpu,
    },
    {
      step: '03',
      title: 'Timeline Reconstruction',
      description: 'Order chronological events with sub-second precision. Every event is strictly tagged as Direct Observation, Derived Value, AI Inference, or Model Assumption.',
      icon: GitFork,
    },
    {
      step: '04',
      title: 'Neutral Contradiction Analysis',
      description: 'Cross-examine witness perceptions against physical telemetry and video optical flow. Discrepancies are highlighted with source citations under strict investigative neutrality.',
      icon: FileText,
    },
  ];

  return (
    <div className="main-content">
      {/* Hero Section */}
      <section className="bg-slate-50 border-b border-slate-200 py-16 sm:py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-slate-200 text-xs font-semibold text-[#0b2545] mb-6 shadow-2xs">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Forensic Accident Investigation & Kinematic Reconstruction</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-slate-900 mb-6 leading-tight">
            Understand What Happened.
          </h1>

          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto mb-8 font-normal leading-relaxed">
            TRACE AI bridges physical vehicle telemetry, surveillance video optical flow, and testimonial statements into a verified, deterministic reconstruction timeline.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/new-investigation"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded bg-[#0b2545] text-white font-medium text-sm hover:bg-[#134074] transition-colors shadow-xs"
            >
              <span>Start Investigation</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/investigation/DEMO-CASE-01"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded bg-white border border-slate-300 text-slate-800 font-medium text-sm hover:bg-slate-100 transition-colors"
            >
              <span>View Demo</span>
            </Link>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-200/60 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Deterministic Kinematics
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> SHA-256 File Integrity
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Epistemic Event Categorization
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Impartial Discrepancy Auditing
            </span>
          </div>
        </div>
      </section>

      {/* Workflow Explanation Section */}
      <section className="py-16 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">
              Forensic Investigation Workflow
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              A scientific, reproducible methodology separating verified physical sensor data from uncorroborated testimonial claims.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {workflowSteps.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="p-5 border border-slate-200 rounded-md bg-white hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold text-[#0b2545] bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      STEP {item.step}
                    </span>
                    <Icon className="w-4 h-4 text-slate-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed m-0">
                    {item.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Quick Start Callout */}
          <div className="mt-12 p-6 bg-slate-50 border border-slate-200 rounded-md flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-semibold text-slate-900 m-0">Ready to examine collision evidence?</h4>
              <p className="text-xs text-slate-500 m-0 mt-0.5">
                Create a case file, upload crash files, and generate an audited reconstruction report.
              </p>
            </div>
            <Link
              to="/new-investigation"
              className="btn btn-primary whitespace-nowrap"
            >
              Start New Investigation
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
