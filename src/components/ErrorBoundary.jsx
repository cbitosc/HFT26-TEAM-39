import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Link } from 'react-router-dom';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('TRACE AI Error Boundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-2xl mx-auto my-12 bg-white border border-red-200 rounded-lg shadow-xs">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-red-100 border border-red-200 text-red-700 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-slate-900 m-0">
                Workspace Display Notice
              </h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                An unexpected interface rendering issue occurred while loading this view:
              </p>
              <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs font-mono text-red-600 my-3 break-all">
                {this.state.error?.message || 'Component failed to render'}
              </div>
              <div className="flex items-center gap-2 mt-4">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="btn btn-primary btn-sm"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry View</span>
                </button>
                <Link to="/dashboard" className="btn btn-secondary btn-sm">
                  <Home className="w-3.5 h-3.5" />
                  <span>Return to Dashboard</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
