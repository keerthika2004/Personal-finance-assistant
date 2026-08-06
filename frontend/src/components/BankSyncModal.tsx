import { useState } from 'react';
import { initiateBankSync, verifyBankSyncOTP, triggerBankSync } from '../api';
import toast from 'react-hot-toast';
import { Landmark, ShieldCheck, KeyRound, CheckCircle2, ArrowRight, Loader2, X } from 'lucide-react';

interface BankSyncModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const SUPPORTED_BANKS = [
  { id: 'hdfc', name: 'HDFC Bank', color: '#004c8f', logo: '🏦' },
  { id: 'sbi', name: 'State Bank of India', color: '#00a3e0', logo: '🏛️' },
  { id: 'icici', name: 'ICICI Bank', color: '#f37021', logo: '💳' },
  { id: 'axis', name: 'Axis Bank', color: '#97144d', logo: '💎' },
];

export default function BankSyncModal({ isOpen, onClose, onSuccess }: BankSyncModalProps) {
  const [step, setStep] = useState<'bank_select' | 'otp_verify' | 'syncing' | 'complete'>('bank_select');
  const [selectedBank, setSelectedBank] = useState(SUPPORTED_BANKS[0]);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [syncSummary, setSyncSummary] = useState<{ bankName: string; autoApproved: number; reviewQueue: number } | null>(null);

  if (!isOpen) return null;

  const handleInitiate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (phoneNumber.length < 10) {
      toast.error('Please enter a valid 10-digit mobile number.');
      return;
    }
    setIsLoading(true);
    try {
      const res = await initiateBankSync(selectedBank.id, selectedBank.name, phoneNumber);
      setSessionId(res.session_id);
      setStep('otp_verify');
      toast.success(`OTP sent via Account Aggregator! (Sandbox OTP: ${res.preview_otp})`, { duration: 6000 });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to initiate bank sync.');
    }
    setIsLoading(false);
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) {
      toast.error('Please enter the 6-digit OTP.');
      return;
    }
    setIsLoading(true);
    try {
      await verifyBankSyncOTP(sessionId, otp);
      setStep('syncing');
      
      // Trigger data sync
      const syncRes = await triggerBankSync(sessionId);
      setSyncSummary({
        bankName: syncRes.bank_name,
        autoApproved: syncRes.auto_approved_count,
        reviewQueue: syncRes.review_queue_count
      });
      setStep('complete');
      onSuccess();
      toast.success(`Connected to ${selectedBank.name}!`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid OTP. Try 123456.');
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStep('bank_select');
    setPhoneNumber('');
    setOtp('');
    setSessionId('');
    setIsLoading(false);
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-card animate-slide-up" style={{
        width: '100%',
        maxWidth: '520px',
        position: 'relative',
        border: '1px solid var(--surface-border)',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        padding: '32px'
      }}>
        <button 
          onClick={handleReset} 
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <X size={20} />
        </button>

        {step === 'bank_select' && (
          <form onSubmit={handleInitiate}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <Landmark color="var(--primary)" size={28} />
              <h2 style={{ margin: 0 }}>Connect Bank Account</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
              RBI Account Aggregator Framework • End-to-End Encrypted
            </p>

            <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: '500' }}>
              Select Bank
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
              {SUPPORTED_BANKS.map((b) => (
                <div
                  key={b.id}
                  onClick={() => setSelectedBank(b)}
                  style={{
                    padding: '14px',
                    borderRadius: '12px',
                    border: selectedBank.id === b.id ? '2px solid var(--primary)' : '1px solid var(--surface-border)',
                    background: selectedBank.id === b.id ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <span style={{ fontSize: '1.4rem' }}>{b.logo}</span>
                  <span style={{ fontWeight: '500', fontSize: '0.95rem' }}>{b.name}</span>
                </div>
              ))}
            </div>

            <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: '500' }}>
              Registered Mobile Number
            </label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
              <span style={{
                padding: '12px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--surface-border)',
                borderRadius: '8px',
                color: 'var(--text-muted)'
              }}>+91</span>
              <input
                type="tel"
                className="input-field"
                placeholder="Enter 10-digit mobile number"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                maxLength={10}
                required
              />
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={isLoading}>
              {isLoading ? <Loader2 className="animate-spin" size={18} /> : <>Initiate AA Consent <ArrowRight size={18} /></>}
            </button>
          </form>
        )}

        {step === 'otp_verify' && (
          <form onSubmit={handleVerifyOTP}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <ShieldCheck color="var(--primary)" size={28} />
              <h2 style={{ margin: 0 }}>Authorize Consent</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>
              Enter the 6-digit OTP sent to <b>+91 {phoneNumber}</b> to grant read-only statement access for <b>{selectedBank.name}</b>.
            </p>

            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid var(--primary)',
              borderRadius: '8px',
              padding: '12px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '0.85rem'
            }}>
              <KeyRound size={18} color="var(--primary)" />
              <span>Sandbox Mode: Use OTP shown in toast notification or <b>123456</b></span>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)', fontWeight: '500' }}>
                6-Digit OTP Code
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. 123456"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                style={{ textAlign: 'center', fontSize: '1.2rem', letterSpacing: '4px' }}
                required
              />
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={isLoading}>
              {isLoading ? <Loader2 className="animate-spin" size={18} /> : 'Verify & Approve Consent'}
            </button>
          </form>
        )}

        {step === 'syncing' && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <Loader2 className="animate-spin" size={48} color="var(--primary)" style={{ margin: '0 auto 16px auto' }} />
            <h3>Syncing Live Statements...</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Fetching encrypted payloads from {selectedBank.name} via Account Aggregator & running ML PII scrubbers...
            </p>
          </div>
        )}

        {step === 'complete' && syncSummary && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <CheckCircle2 size={56} color="var(--primary)" style={{ margin: '0 auto 16px auto' }} />
            <h2>Successfully Connected!</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
              Real-time transaction feed from <b>{syncSummary.bankName}</b> has been synchronized with your Personal Finance Assistant.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '16px',
              borderRadius: '12px',
              marginBottom: '24px'
            }}>
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--primary)' }}>{syncSummary.autoApproved}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Auto-Categorized</div>
              </div>
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f59e0b' }}>{syncSummary.reviewQueue}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sent to Review Queue</div>
              </div>
            </div>

            <button onClick={handleReset} className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
              Done & Return to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
