import { useEffect, useState } from 'react';
import { api } from '../api';
import toast from 'react-hot-toast';
import { AlertTriangle, Check, X } from 'lucide-react';

export default function ReviewQueue() {
  const [flagged, setFlagged] = useState<any[]>([]);

  const fetchFlagged = async () => {
    try {
      const res = await api.get('/reconcile/pending');
      setFlagged(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchFlagged();
  }, []);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      await api.post(`/reconcile/decision`, { transaction_id: id, action: action.toUpperCase() });
      toast.success(`Transaction ${action}d successfully`);
      fetchFlagged();
    } catch (err) {
      toast.error(`Failed to ${action} transaction`);
    }
  };

  return (
    <div className="animate-slide-up">
      <h1>🚨 Review Queue (HITL)</h1>
      <p style={{ marginBottom: '32px' }}>Review transactions flagged by the LangGraph engine as suspicious or duplicate.</p>

      {flagged.length === 0 ? (
        <div className="glass-card stagger-1" style={{ textAlign: 'center', padding: '64px 32px' }}>
          <Check size={48} color="var(--primary)" style={{ marginBottom: '16px' }} />
          <h2>All Clear!</h2>
          <p>You have no pending transactions to review.</p>
        </div>
      ) : (
        <div className="dashboard-grid stagger-1">
          {flagged.map((tx) => (
            <div key={tx.id} className="glass-card" style={{ borderLeft: '4px solid #ef4444' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <AlertTriangle color="#ef4444" size={20} />
                <h3 style={{ color: '#ef4444', margin: 0 }}>Flagged Review</h3>
              </div>
              <h2 style={{ marginBottom: '8px' }}>{tx.raw_description}</h2>
              <p style={{ color: 'var(--text-main)', fontSize: '1.2rem', fontWeight: '600', marginBottom: '8px' }}>₹{tx.amount.toFixed(2)}</p>
              <p style={{ marginBottom: '24px' }}>Date: {new Date(tx.date).toLocaleDateString('en-GB')}</p>
              
              <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', marginBottom: '24px' }}>
                <p style={{ margin: 0, color: '#fca5a5', fontSize: '0.9rem' }}>{tx.anomaly_reason || 'Anomaly detected'}</p>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button className="btn-primary" onClick={() => handleAction(tx.id, 'approve')} style={{ flex: 1, justifyContent: 'center' }}>
                  <Check size={18} /> Approve
                </button>
                <button className="btn-primary" onClick={() => handleAction(tx.id, 'reject')} style={{ flex: 1, justifyContent: 'center', background: 'rgba(255,255,255,0.1)', color: 'var(--text-main)' }}>
                  <X size={18} /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
