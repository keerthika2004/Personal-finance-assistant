import React, { useState } from 'react';
import { api } from '../api';
import toast from 'react-hot-toast';
import { Lock, Mail, User, ShieldCheck, Zap, X } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: any, token: string) => void;
}

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login';
      const payload = isRegister ? { email, password, name } : { email, password };
      const res = await api.post(endpoint, payload);
      
      const { access_token, user } = res.data;
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('auth_user', JSON.stringify(user));
      
      toast.success(isRegister ? 'Account created successfully!' : `Welcome back, ${user.name}!`);
      onSuccess(user, access_token);
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Authentication failed. Please check credentials.';
      toast.error(msg);
    }
    setLoading(false);
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    try {
      const res = await api.post('/auth/demo');
      const { access_token, user } = res.data;
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('auth_user', JSON.stringify(user));
      
      toast.success('Logged in as Demo Portfolio Evaluator!');
      onSuccess(user, access_token);
      onClose();
    } catch (err) {
      toast.error('Demo login failed.');
    }
    setLoading(false);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-card animate-scale-up" style={{
        maxWidth: '440px',
        width: '100%',
        position: 'relative',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)'
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <X size={20} />
        </button>

        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '12px'
          }}>
            <ShieldCheck size={32} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.5rem', margin: 0 }}>
            {isRegister ? 'Create Your Account' : 'Welcome to FinAI'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '6px' }}>
            {isRegister ? 'Sign up to start tracking your finances securely' : 'Sign in to access your personal finance dashboard'}
          </p>
        </div>

        {/* 1-Click Instant Demo Login Banner */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '12px',
          padding: '12px 16px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <div>
            <div style={{ fontWeight: '600', fontSize: '0.85rem', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={14} /> Quick Recruiter Demo
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Skip signup and test the full dashboard in 1 click</div>
          </div>
          <button
            type="button"
            onClick={handleDemoLogin}
            className="btn-primary"
            style={{ padding: '6px 14px', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
            disabled={loading}
          >
            Demo Login
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', margin: '16px 0', gap: '12px' }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--surface-border)' }} />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>OR SIGN IN WITH EMAIL</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--surface-border)' }} />
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {isRegister && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Full Name</label>
              <div style={{ position: 'relative' }}>
                <User size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '14px' }} />
                <input
                  type="text"
                  className="input-field"
                  placeholder="John Doe"
                  required
                  value={name}
                  onChange={e => setName(e.target.value)}
                  style={{ paddingLeft: '38px' }}
                />
              </div>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '14px' }} />
              <input
                type="email"
                className="input-field"
                placeholder="you@example.com"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                style={{ paddingLeft: '38px' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '14px' }} />
              <input
                type="password"
                className="input-field"
                placeholder="••••••••"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ paddingLeft: '38px' }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ justifyContent: 'center', padding: '12px', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? 'Processing...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          </span>
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            style={{ background: 'transparent', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: '600' }}
          >
            {isRegister ? 'Sign In' : 'Sign Up'}
          </button>
        </div>
      </div>
    </div>
  );
}
