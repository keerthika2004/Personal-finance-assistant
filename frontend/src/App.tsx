import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, List, Upload, MessageSquare, Activity, LogIn, LogOut, User as UserIcon } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import { api } from './api';
import AuthModal from './components/AuthModal';

import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import ReviewQueue from './pages/ReviewQueue';
import UploadPage from './pages/UploadPage';
import Chat from './pages/Chat';

interface AppProps {
  user: any;
  onOpenAuth: () => void;
  onLogout: () => void;
}

function Sidebar({ user, onOpenAuth, onLogout }: AppProps) {
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
  }, [user]);

  return (
    <div className="sidebar animate-slide-up">
      <div className="sidebar-header">
        <h2 style={{ color: 'white', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
          <span style={{ fontSize: '28px' }}>💰</span> FinAI Assistant
        </h2>
      </div>

      {/* User Account Status */}
      <div className="glass-card" style={{ padding: '12px 16px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>
                {user.name ? user.name[0].toUpperCase() : 'U'}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-main)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{user.name || 'User'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{user.email || 'Free Tier'}</div>
              </div>
            </div>
            <button onClick={onLogout} title="Sign Out" style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}>
              <LogOut size={18} />
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <UserIcon size={16} /> Guest Mode
            </div>
            <button onClick={onOpenAuth} className="btn-primary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
              <LogIn size={14} /> Sign In
            </button>
          </div>
        )}
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
        <p style={{ fontSize: '0.85rem', marginBottom: '4px' }}>Powered by</p>
        <p style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.9rem', margin: 0 }}>FastAPI + React + LangGraph</p>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState<any>(() => {
    const saved = localStorage.getItem('auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  useEffect(() => {
    if (!user) {
      setIsAuthOpen(true);
    }
  }, [user]);

  const handleAuthSuccess = (userData: any, token?: string) => {
    if (token) {
      localStorage.setItem('auth_token', token);
    }
    localStorage.setItem('auth_user', JSON.stringify(userData));
    setUser(userData);
    setIsAuthOpen(false);
    window.location.reload();
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setUser(null);
    window.location.reload();
  };

  return (
    <Router>
      <div className="app-container">
        <Sidebar user={user} onOpenAuth={() => setIsAuthOpen(true)} onLogout={handleLogout} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/review" element={<ReviewQueue />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </main>
        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onSuccess={handleAuthSuccess}
        />
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
