import { useState } from 'react';
import { api, uploadStatement } from '../api';
import toast from 'react-hot-toast';
import { UploadCloud, CheckCircle } from 'lucide-react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [manualTx, setManualTx] = useState({ date: '', description: '', amount: '', type: 'expense' });

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      const res = await uploadStatement(file);
      toast.success('Statement processed successfully!');
      console.log(res);
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
        amount: finalAmount
      });
      toast.success('Manual transaction added!');
      setManualTx({ date: '', description: '', amount: '', type: 'expense' });
    } catch (err) {
      toast.error('Error adding transaction');
    }
  };

  return (
    <div className="animate-slide-up">
      <h1>📄 Upload Bank Statements</h1>
      <p style={{ marginBottom: '32px' }}>Upload your bank statement PDF, CSV, or Image (PNG/JPG) file.</p>

      <div className="dashboard-grid">
        <div className="glass-card stagger-1" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px', border: '2px dashed var(--surface-border)' }}>
          <UploadCloud size={64} color="var(--primary)" style={{ marginBottom: '16px' }} />
          <h3>Drag & Drop your file here</h3>
          <p style={{ margin: '8px 0 24px 0', fontSize: '0.9rem' }}>Supports PDF, CSV, PNG, JPG</p>
          
          <input 
            type="file" 
            id="file-upload" 
            style={{ display: 'none' }} 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <label htmlFor="file-upload" className="btn-primary" style={{ cursor: 'pointer' }}>
            Choose File
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
                {isUploading ? 'Processing Engine...' : '🚀 Process Statement'}
              </button>
            </div>
          )}
        </div>

        <div className="glass-card stagger-2">
          <h2>✍️ Manual Entry</h2>
          <form onSubmit={handleManualAdd} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Date</label>
              <input type="date" className="input-field" required value={manualTx.date} onChange={e => setManualTx({...manualTx, date: e.target.value})} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Description / Merchant</label>
              <input type="text" className="input-field" placeholder="e.g. Starbucks, Salary" required value={manualTx.description} onChange={e => setManualTx({...manualTx, description: e.target.value})} />
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
    </div>
  );
}
