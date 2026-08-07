import { useEffect, useState } from 'react';
import { api, deleteTransaction } from '../api';
import { Search, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Transactions() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchTx = async () => {
      try {
        const res = await api.get('/analytics/summary');
        setTransactions(res.data.transactions || []);
      } catch (err) {
        console.error(err);
        setTransactions([
          { id: "e4d36ee6", date: "2026-08-07", normalized_merchant: "Samosa party", category: "Dining", amount: -10000.00, confidence: 0.98, user_id: "demo_user" },
          { id: "73d1573e", date: "2026-08-06", normalized_merchant: "cashback from amazon", category: "Online Shopping", amount: 100.00, confidence: 1.00, user_id: "demo_user" },
          { id: "4ff6d8d2", date: "2026-08-06", normalized_merchant: "from my friend", category: "Transfer", amount: 50.00, confidence: 0.95, user_id: "demo_user" },
          { id: "a434a517", date: "2026-08-06", normalized_merchant: "candy", category: "Groceries", amount: -10.00, confidence: 0.99, user_id: "demo_user" },
          { id: "040e1a87", date: "2026-08-06", normalized_merchant: "Starbucks", category: "Dining", amount: 15000.00, confidence: 0.95, user_id: "demo_user" },
          { id: "97b99053", date: "2026-08-06", normalized_merchant: "nykaa serum", category: "Shopping", amount: -1000.00, confidence: 0.97, user_id: "demo_user" },
          { id: "25676a8a", date: "2026-08-06", normalized_merchant: "chips from zepto", category: "Groceries", amount: -200.00, confidence: 0.99, user_id: "demo_user" },
          { id: "a0179865", date: "2026-08-06", normalized_merchant: "Burger from McDonalds", category: "Dining", amount: -350.00, confidence: 0.98, user_id: "demo_user" },
          { id: "fc5158b0", date: "2026-08-06", normalized_merchant: "chicken popcorn", category: "Dining", amount: -110.00, confidence: 0.96, user_id: "demo_user" },
          { id: "22186e64", date: "2026-08-06", normalized_merchant: "AXIS BANK CREDIT CARD REWARD CASHBACK", category: "Income", amount: 1200.00, confidence: 1.00, user_id: "demo_user" },
          { id: "bd16d36a", date: "2026-08-06", normalized_merchant: "rent", category: "Housing", amount: -2000.00, confidence: 0.99, user_id: "demo_user" },
          { id: "9425595d", date: "2026-08-06", normalized_merchant: "biscuits", category: "Groceries", amount: -15.00, confidence: 0.99, user_id: "demo_user" }
        ]);
      }
    };
    fetchTx();
  }, []);

  const handleDelete = async (id: string, merchant: string) => {
    if (window.confirm(`Are you sure you want to delete "${merchant}"? This will permanently remove it from all analytics and dashboards.`)) {
      try {
        await deleteTransaction(id);
        setTransactions(prev => prev.filter(t => t.id !== id));
        toast.success(`Transaction "${merchant}" deleted successfully!`);
      } catch (err) {
        console.error(err);
        toast.error('Failed to delete transaction.');
      }
    }
  };

  const filteredTx = transactions
    .filter((t) => 
      t.normalized_merchant?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.amount.toString().includes(searchTerm)
    )
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <div className="animate-slide-up">
      <h1>📜 Transaction History</h1>
      
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
                  <td style={{ fontWeight: '500' }}>{tx.normalized_merchant}</td>
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
                    color: tx.amount < 0 ? '#ef4444' : 'var(--primary)',
                    fontWeight: '600'
                  }}>
                    {tx.amount.toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => handleDelete(tx.id, tx.normalized_merchant || 'Transaction')}
                      title="Delete Transaction"
                      style={{
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        color: '#ef4444',
                        padding: '6px 10px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.3)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)'}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredTx.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '32px' }}>No transactions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
