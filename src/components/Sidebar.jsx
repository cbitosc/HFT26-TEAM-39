import React from 'react';
import { NavLink, useParams } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Files, 
  Clock, 
  Layers, 
  GitFork, 
  FileText,
  ChevronLeft
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Sidebar({ incident }) {
  const { id } = useParams();
  const incidentId = id || incident?.id || 'INC-20261030-DEMO1';

  const navItems = [
    { to: `/investigation/${incidentId}`, label: 'Overview', icon: LayoutDashboard, end: true },
    { to: `/investigation/${incidentId}/evidence`, label: 'Evidence', icon: Files },
    { to: `/investigation/${incidentId}/timeline`, label: 'Timeline', icon: Clock },
    { to: `/investigation/${incidentId}/reconstruction`, label: 'Reconstruction', icon: Layers },
    { to: `/investigation/${incidentId}/analysis`, label: 'Analysis & Discrepancies', icon: GitFork },
    { to: `/investigation/${incidentId}/reports`, label: 'Report & Export', icon: FileText },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-slate-50 shrink-0 min-h-[calc(100vh-64px)] flex flex-col justify-between">
      <div className="p-4">
        {/* Back Link */}
        <NavLink 
          to="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-4 transition-colors font-medium"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
          <span>All Investigations</span>
        </NavLink>

        {/* Current Investigation Meta */}
        <div className="mb-6 p-3 bg-white rounded border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-mono text-slate-500 font-medium truncate max-w-[140px]" title={incidentId}>
              {incidentId}
            </span>
            <StatusBadge status={incident?.status || 'UNDER_INVESTIGATION'} />
          </div>
          <h2 className="text-xs font-semibold text-slate-900 leading-snug line-clamp-2" title={incident?.title}>
            {incident?.title || 'Investigation Workspace'}
          </h2>
          <div className="text-[11px] text-slate-500 mt-1 truncate">
            {incident?.location || 'Location Pending'}
          </div>
        </div>

        {/* Workspace Navigation */}
        <div className="space-y-1">
          <div className="px-2 pb-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded transition-colors ${
                    isActive
                      ? 'bg-[#0b2545] text-white shadow-2xs'
                      : 'text-slate-700 hover:text-slate-900 hover:bg-slate-200/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0 opacity-90" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Forensic Disclaimer Footer */}
      <div className="p-4 border-t border-slate-200 text-[11px] text-slate-500 bg-white/50">
        <div className="font-semibold text-slate-700 mb-0.5">Forensic Standard</div>
        <div>Observations, telemetry logs, and witness claims are cross-examined neutrally.</div>
      </div>
    </aside>
  );
}
