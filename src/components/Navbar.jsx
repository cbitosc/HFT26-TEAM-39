import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Activity, Plus, Sparkles, Key, CheckCircle2, AlertCircle, X } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar() {
  const location = useLocation();
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [aiStatus, setAiStatus] = useState({ is_available: false, model: 'mistralai/Mistral-7B-Instruct-v0.2', message: 'Checking...' });
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [modelInput, setModelInput] = useState('mistralai/Mistral-7B-Instruct-v0.2');
  const [submitting, setSubmitting] = useState(false);
  const [configFeedback, setConfigFeedback] = useState(null);

  const checkStatus = () => {
    api.getHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));

    api.getAIStatus()
      .then((data) => setAiStatus(data))
      .catch(() => setAiStatus({ is_available: false, model: 'meta-llama/Meta-Llama-3.1-8B-Instruct', message: 'Backend unreachable' }));
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const handleSaveApiKey = async (e) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) return;

    setSubmitting(true);
    setConfigFeedback(null);

    try {
      const res = await api.configureAI(apiKeyInput.trim(), modelInput.trim());
      setAiStatus(res);
      if (res.is_available) {
        setConfigFeedback({ type: 'success', text: 'Featherless AI key validated and connected successfully!' });
        setTimeout(() => {
          setShowConfigModal(false);
          setConfigFeedback(null);
          setApiKeyInput('');
        }, 1800);
      } else {
        setConfigFeedback({ type: 'warning', text: res.message || 'Key saved, but service returned verification issue.' });
      }
    } catch (err) {
      setConfigFeedback({ type: 'error', text: err.message || 'Failed to configure Featherless API key.' });
    } finally {
      setSubmitting(false);
    }
  };

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <>
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2.5 text-slate-900 group">
              <div className="w-8 h-8 rounded bg-[#0b2545] text-white flex items-center justify-center font-bold tracking-wider text-sm shadow-xs">
                TR
              </div>
              <div>
                <div className="font-semibold text-base leading-tight tracking-tight text-slate-900 flex items-center gap-1.5">
                  TRACE AI
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 uppercase font-semibold">
                    v1.0
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 font-normal">Accident Investigation & Reconstruction</div>
              </div>
            </Link>

            {/* Primary Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/"
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  isActive('/') ? 'text-[#0b2545] bg-slate-100' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                Home
              </Link>
              <Link
                to="/dashboard"
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  isActive('/dashboard') ? 'text-[#0b2545] bg-slate-100' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                Investigations
              </Link>
              <Link
                to="/investigation/INC-20261030-DEMO1"
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  location.pathname.includes('DEMO1') ? 'text-[#0b2545] bg-slate-100 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                Demo Case
              </Link>
            </nav>
          </div>

          {/* Right Action & Status */}
          <div className="flex items-center gap-3">
            {/* Featherless AI Pill */}
            <button
              type="button"
              onClick={() => setShowConfigModal(true)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border transition-colors cursor-pointer"
              style={{
                backgroundColor: aiStatus.is_available ? '#faf5ff' : '#f8fafc',
                borderColor: aiStatus.is_available ? '#e9d5ff' : '#e2e8f0',
                color: aiStatus.is_available ? '#6b21a8' : '#475569',
              }}
              title="Featherless AI status — Click to configure API key"
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span className="font-medium">
                {aiStatus.is_available ? 'Featherless AI Ready' : 'Featherless AI Setup'}
              </span>
            </button>

            {/* Backend Health Pill */}
            <div
              className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border"
              style={{
                backgroundColor: backendStatus === 'online' ? '#f0fdf4' : '#f8fafc',
                borderColor: backendStatus === 'online' ? '#bbf7d0' : '#e2e8f0',
                color: backendStatus === 'online' ? '#166534' : '#64748b',
              }}
              title={backendStatus === 'online' ? 'FastAPI Backend connected' : 'Backend offline or running locally (Demo standby active)'}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: backendStatus === 'online' ? '#22c55e' : '#94a3b8',
                }}
              />
              <span className="font-medium">
                {backendStatus === 'online' ? 'API Online' : 'Standby / Demo Ready'}
              </span>
            </div>

            <Link
              to="/new-investigation"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-medium text-white bg-[#0b2545] hover:bg-[#134074] rounded transition-colors shadow-xs"
            >
              <Plus className="w-4 h-4" />
              <span>New Investigation</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Featherless AI Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg border border-slate-200 shadow-xl max-w-md w-full p-6 relative">
            <button
              type="button"
              onClick={() => setShowConfigModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
                <Sparkles className="w-4 h-4" />
              </div>
              <h2 className="text-base font-semibold text-slate-900">Featherless AI Integration</h2>
            </div>

            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Connect your Featherless AI API key for server-side witness statement entity extraction, contradiction synthesis, and forensic summaries.
            </p>

            <div className="mb-4 p-3 bg-slate-50 rounded border border-slate-200 text-xs">
              <div className="flex justify-between items-center mb-1">
                <span className="text-slate-500">Service Status:</span>
                <span className={`font-semibold ${aiStatus.is_available ? 'text-emerald-700' : 'text-slate-700'}`}>
                  {aiStatus.is_available ? 'Connected' : 'Not Configured (Deterministic Fallback Active)'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Current Model:</span>
                <span className="font-mono text-[11px] text-slate-800">{aiStatus.model}</span>
              </div>
            </div>

            {configFeedback && (
              <div
                className={`mb-4 p-3 rounded text-xs flex items-start gap-2 border ${
                  configFeedback.type === 'success'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : configFeedback.type === 'warning'
                    ? 'bg-amber-50 border-amber-200 text-amber-800'
                    : 'bg-red-50 border-red-200 text-red-800'
                }`}
              >
                {configFeedback.type === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                )}
                <div>{configFeedback.text}</div>
              </div>
            )}

            <form onSubmit={handleSaveApiKey} className="space-y-3">
              <div>
                <label className="form-label text-xs">Featherless API Key</label>
                <input
                  type="password"
                  placeholder="featherless-..."
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  className="form-input text-xs font-mono"
                  required
                  disabled={submitting}
                />
                <div className="text-[11px] text-slate-400 mt-1">
                  Stored securely on the backend server only. Never exposed in browser code.
                </div>
              </div>

              <div>
                <label className="form-label text-xs">Model Identifier</label>
                <input
                  type="text"
                  value={modelInput}
                  onChange={(e) => setModelInput(e.target.value)}
                  className="form-input text-xs font-mono"
                  disabled={submitting}
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowConfigModal(false)}
                  className="btn btn-secondary btn-sm"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !apiKeyInput.trim()}
                  className="btn btn-primary btn-sm"
                >
                  {submitting ? 'Validating...' : 'Connect Featherless AI'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
