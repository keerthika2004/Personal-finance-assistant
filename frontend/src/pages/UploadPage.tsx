import { useState } from 'react';
import { api, uploadStatement } from '../api';
import toast from 'react-hot-toast';
import { UploadCloud, CheckCircle, Landmark, ArrowRight, ShieldCheck } from 'lucide-react';
import BankSyncModal from '../components/BankSyncModal';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [manualTx, setManualTx] = useState({ date: '', description: '', amount: '', type: 'expense', category: 'auto' });
  const [isBankModalOpen, setIsBankModalOpen] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      await uploadStatement(file);
      toast.success('Statement processed successfully!');
      setFile(null);
    } catch (err) {
      toast.error('Error processing statement');
    }
    setIsUploading(false);
  };

  const handleManualAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const finalAmount = manualTx.type === 'expense' ? -Math.abs(Number(manualTx.amount)) : Math.abs(Number(manualTx.amount));
      await api.post('/upload/manual', {
        date: new Date(manualTx.date).toISOString().slice(0, 19).replace('T', ' '),
        description: manualTx.description,
        amount: finalAmount,
        category: manualTx.category === 'auto' ? null : manualTx.category
      });
      toast.success('Manual transaction added!');
      setManualTx({ date: '', description: '', amount: '', type: 'expense', category: 'auto' });
    } catch (err) {
      toast.error('Error adding transaction');
    }
  };

  return (
    <div className="animate-slide-up">
      <h1>📄 Bank Connections & Statement Imports</h1>
      <p style={{ marginBottom: '32px' }}>
        Sync live transactions via RBI Account Aggregator, upload statements (PDF, CSV, Receipt Image), or enter transactions manually.
      </p>

      {/* Featured Account Aggregator Banner */}
      <div 
        className="glass-card stagger-1" 
        style={{ 
          marginBottom: '32px', 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%)',
          border: '1px solid var(--primary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
          padding: '28px'
        }}
      >
        <div style={{ maxWidth: '600px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <ShieldCheck color="var(--primary)" size={20} />
            <span style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
              RBI Regulated Account Aggregator (AA)
            </span>
          </div>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '1.6rem' }}>Connect Your Indian Bank Account</h2>
          <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.95rem' }}>
            Securely link HDFC, SBI, ICICI, or Axis Bank to automatically sync live balance & daily transactions without downloading statements.
          </p>
        </div>
        <button 
          onClick={() => setIsBankModalOpen(true)} 
          className="btn-primary" 
          style={{ padding: '14px 28px', fontSize: '1rem' }}
        >
          <Landmark size={20} /> Connect Live Bank <ArrowRight size={20} />
        </button>
      </div>

      <div className="dashboard-grid">
        {/* File Upload Card */}
        <div className="glass-card stagger-2" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '320px', border: '2px dashed var(--surface-border)' }}>
          <UploadCloud size={56} color="var(--primary)" style={{ marginBottom: '16px' }} />
          <h3>Drag & Drop File Upload</h3>
          <p style={{ margin: '8px 0 24px 0', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Supports PDF, CSV, PNG, JPG</p>
          
          <input 
            type="file" 
            id="file-upload" 
            style={{ display: 'none' }} 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <label htmlFor="file-upload" className="btn-primary" style={{ cursor: 'pointer' }}>
            Choose Statement File
          </label>
          
          {file && (
            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-main)', fontWeight: '500' }}><CheckCircle size={16} style={{ display: 'inline', verticalAlign: 'text-bottom' }} /> {file.name}</p>
              <button 
                onClick={handleUpload} 
                className="btn-primary" 
                style={{ marginTop: '12px', width: '100%', justifyContent: 'center' }}
                disabled={isUploading}
              >
                {isUploading ? 'Processing Engine...' : 'Process Statement'}
              </button>
            </div>
          )}
        </div>

        {/* Manual Entry Card */}
        <div className="glass-card stagger-3">
          <h2>✍️ Manual Transaction Entry</h2>
          <form onSubmit={handleManualAdd} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Date</label>
              <input type="date" className="input-field" required value={manualTx.date} onChange={e => setManualTx({...manualTx, date: e.target.value})} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Description / Merchant</label>
              <input type="text" className="input-field" placeholder="e.g. Starbucks, Salary, Cash Auto" required value={manualTx.description} onChange={e => setManualTx({...manualTx, description: e.target.value})} />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Category</label>
              <select className="input-field" value={manualTx.category} onChange={e => setManualTx({...manualTx, category: e.target.value})}>
                <option value="auto">✨ Auto-Detect (AI / ML Categorizer)</option>
                <option value="Dining">Dining & Restaurants</option>
                <option value="Groceries">Groceries & Supermarket</option>
                <option value="Online Shopping">Online Shopping</option>
                <option value="Shopping">Shopping & Apparel</option>
                <option value="Transportation">Transportation & Fuel</option>
                <option value="Utilities">Utilities & Bills</option>
                <option value="Subscriptions">Subscriptions & Fitness</option>
                <option value="Income">Income & Salary</option>
                <option value="Transfer">Transfer / P2P</option>
                <option value="Housing">Housing & Rent</option>
                <option value="Healthcare">Healthcare & Pharmacy</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Type</label>
                <select className="input-field" value={manualTx.type} onChange={e => setManualTx({...manualTx, type: e.target.value})}>
                  <option value="expense">Expense (Debit)</option>
                  <option value="income">Income (Credit)</option>
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Amount (₹)</label>
                <input type="number" step="0.01" className="input-field" required value={manualTx.amount} onChange={e => setManualTx({...manualTx, amount: e.target.value})} />
              </div>
            </div>
            <button type="submit" className="btn-primary" style={{ justifyContent: 'center', marginTop: '8px' }}>
              Add Transaction
            </button>
          </form>
        </div>
      </div>

      {/* Account Aggregator Sync Modal */}
      <BankSyncModal
        isOpen={isBankModalOpen}
        onClose={() => setIsBankModalOpen(false)}
        onSuccess={() => setIsBankModalOpen(false)}
      />
    </div>
  );
}
