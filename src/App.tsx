import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import NewInvestigation from './pages/NewInvestigation';
import InvestigationWorkspace from './pages/InvestigationWorkspace';
import './styles/global.css';
import './styles/components.css';

import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navbar />

        <div className="main-content">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/new-investigation" element={<NewInvestigation />} />
              <Route path="/investigation/:id/*" element={<InvestigationWorkspace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </div>

        {/* Global Minimal Footer */}
        <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>
              <strong>TRACE AI</strong> — AI-Powered Road Accident Investigation & Kinematic Reconstruction
            </div>
            <div className="text-[11px] text-slate-400">
              Deterministic kinematic analysis · Epistemic observation classification · Neutral cross-examination
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
