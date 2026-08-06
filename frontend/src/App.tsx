import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, List, Upload, MessageSquare, Activity } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import { api } from './api';

import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import ReviewQueue from './pages/ReviewQueue';
import UploadPage from './pages/UploadPage';
import Chat from './pages/Chat';

function Sidebar() {
  const location = useLocation();
  const path = location.pathname;
  const [healthScore, setHealthScore] = useState<number | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await api.get('/analytics/summary');
        setHealthScore(res.data.health_score);
      } catch (err) {
        console.error(err);
      }
    };
    fetchHealth();
  }, []);

  return (
    <div className="sidebar animate-slide-up">
      <div className="sidebar-header">
        <h2 style={{ color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '28px' }}>💰</span> FinAI Assistant
        </h2>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
        <Link to="/" className={`nav-link ${path === '/' ? 'active' : ''}`}>
          <LayoutDashboard size={20} /> Dashboard
        </Link>
        <Link to="/transactions" className={`nav-link ${path === '/transactions' ? 'active' : ''}`}>
          <List size={20} /> Transaction History
        </Link>
        <Link to="/review" className={`nav-link ${path === '/review' ? 'active' : ''}`}>
          <FileText size={20} /> Review Queue (HITL)
        </Link>
        <Link to="/upload" className={`nav-link ${path === '/upload' ? 'active' : ''}`}>
          <Upload size={20} /> Upload Statements
        </Link>
        <Link to="/chat" className={`nav-link ${path === '/chat' ? 'active' : ''}`}>
          <MessageSquare size={20} /> AI Advisor Chat
        </Link>
      </nav>

      {healthScore !== null && (
        <div className="glass-card" style={{ padding: '16px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '0.9rem' }}>Health Score</h3>
            <Activity size={16} color="#f59e0b" />
          </div>
          <div style={{ marginTop: '8px' }}>
            <h2 style={{ margin: 0, color: '#f59e0b', fontSize: '2rem' }}>
              {healthScore}<span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/100</span>
            </h2>
            <div style={{ width: '100%', height: '6px', background: 'var(--surface-border)', borderRadius: '3px', marginTop: '8px', overflow: 'hidden' }}>
              <div style={{ width: `${healthScore}%`, height: '100%', background: '#f59e0b', transition: 'width 1s ease' }}></div>
            </div>
          </div>
        </div>
      )}

      <div className="glass-card" style={{ padding: '16px', textAlign: 'center' }}>
        <p style={{ fontSize: '0.85rem', marginBottom: '8px' }}>Powered by</p>
        <p style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.9rem' }}>FastAPI + React + LangGraph</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/review" element={<ReviewQueue />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </main>
        <Toaster position="bottom-right" toastOptions={{
          style: {
            background: 'var(--surface-hover)',
            color: 'var(--text-main)',
            backdropFilter: 'blur(10px)',
            border: '1px solid var(--surface-border)'
          }
        }}/>
      </div>
    </Router>
  );
}

export default App;
