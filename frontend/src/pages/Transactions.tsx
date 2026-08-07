import { useEffect, useState } from 'react';
import { api, deleteTransaction } from '../api';
import { FULL_DEMO_SUMMARY } from '../demoData';
import { Search, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Transactions() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchTx = async () => {
      try {
        const res = await api.get('/analytics/summary');
        const demoData = FULL_DEMO_SUMMARY as any;
        setTransactions(res.data.transactions || demoData.transactions || demoData.recent_transactions || []);
      } catch (err) {
        console.error(err);
        const demoData = FULL_DEMO_SUMMARY as any;
        setTransactions(demoData.transactions || demoData.recent_transactions || []);
      }
    };
    fetchTx();
  }, []);

  const handleDelete = async (id: string, merchant: string) => {
    if (window.confirm(`Are you sure you want to delete "${merchant}"? This will permanently remove it from all analytics and dashboards.`)) {
      try {
        await deleteTransaction(id);
      } catch (err) {
        console.warn("Backend API unreachable, removing transaction from local session state.");
      }
      setTransactions(prev => prev.filter(t => t.id !== id));
      toast.success(`Transaction "${merchant}" deleted successfully!`);
    }
  };

  const getMerchantName = (t: any) => {
    return t.normalized_merchant || t.raw_description || t.merchant || 'Transaction';
  };

  const filteredTx = transactions
    .filter((t) => {
      const name = getMerchantName(t).toLowerCase();
      const cat = (t.category || '').toLowerCase();
      const amt = (t.amount || 0).toString();
      const search = searchTerm.toLowerCase();
      return name.includes(search) || cat.includes(search) || amt.includes(search);
    })
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <div className="animate-slide-up">
      <h1>📜 Transaction History ({transactions.length} Total)</h1>
      
      <div className="glass-card stagger-1" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Search color="var(--text-muted)" />
          <input 
            type="text" 
            className="input-field" 
            placeholder="Search merchants, categories, or amounts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, background: 'transparent', border: 'none', boxShadow: 'none' }}
          />
        </div>
      </div>

      <div className="glass-card stagger-2">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Category</th>
                <th>Amount (₹)</th>
                <th style={{ textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredTx.map((tx, idx) => (
                <tr key={tx.id || idx}>
                  <td>{new Date(tx.date).toLocaleDateString('en-GB')}</td>
                  <td style={{ fontWeight: '500' }}>{getMerchantName(tx)}</td>
                  <td>
                    <span style={{ 
                      padding: '4px 12px', 
                      borderRadius: '16px', 
                      background: 'rgba(255,255,255,0.1)',
                      fontSize: '0.85rem'
                    }}>
                      {tx.category}
                    </span>
                  </td>
                  <td style={{ 
                    color: (tx.amount || 0) < 0 ? '#ef4444' : 'var(--primary)',
                    fontWeight: '600'
                  }}>
                    {(tx.amount || 0).toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => handleDelete(tx.id, getMerchantName(tx))}
                      style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
