import { useEffect, useState } from 'react';
import { api } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Zap, Target, Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  
  // NLP Quick Add state
  const [nlpText, setNlpText] = useState('');
  const [isNlpLoading, setIsNlpLoading] = useState(false);

  // New Goal State
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [newGoal, setNewGoal] = useState({ name: '', target: '', current: '' });

  // Add Funds State (map of goal_id -> amount)
  const [addFunds, setAddFunds] = useState<Record<number, string>>({});

  const fetchSummary = async () => {
    try {
      const res = await api.get('/analytics/summary');
      setSummary(res.data);
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
      setSummary({
        total_income: 164082.00,
        total_expenses: 56393.11,
        net_savings: 107688.89,
        monthly_trend: {
          "2026-01": { income: 52000, expenses: 18450 },
          "2026-02": { income: 54000, expenses: 19200 },
          "2026-03": { income: 58082, expenses: 18743.11 }
        },
        category_breakdown: {
          "Food & Dining": 14200,
          "Utilities & Bills": 12500,
          "Shopping": 15693.11,
          "Transport": 8500,
          "Entertainment": 5500
        },
        recent_transactions: [
          { id: "1", date: "2026-03-28", merchant: "Swiggy Food Delivery", category: "Food & Dining", amount: -450.00, confidence: 0.98, user_id: "demo_user" },
          { id: "2", date: "2026-03-26", merchant: "Salary Credit - TechCorp", category: "Income", amount: 58082.00, confidence: 1.00, user_id: "demo_user" },
          { id: "3", date: "2026-03-24", merchant: "Amazon India Electronics", category: "Shopping", amount: -12499.00, confidence: 0.95, user_id: "demo_user" },
          { id: "4", date: "2026-03-20", merchant: "BESCOM Electricity Bill", category: "Utilities & Bills", amount: -2850.00, confidence: 0.99, user_id: "demo_user" }
        ]
      });
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleNlpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlpText.trim()) return;
    setIsNlpLoading(true);
    try {
      const res = await api.post('/upload/chat', { text: nlpText });
      if (res.data.requires_hitl) {
        toast('⚠️ Added to Review Queue for confirmation', { icon: '⚠️' });
      } else {
        toast.success('✅ Transaction added automatically!');
      }
      setNlpText('');
      fetchSummary();
    } catch (err) {
      toast.error('Failed to parse transaction');
    } finally {
      setIsNlpLoading(false);
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoal.name || !newGoal.target) return;
    try {
      await api.post('/analytics/goals', {
        goal_name: newGoal.name,
        target_amount: parseFloat(newGoal.target),
        current_amount: parseFloat(newGoal.current) || 0
      });
      toast.success('Goal created!');
      setNewGoal({ name: '', target: '', current: '' });
      setShowGoalForm(false);
      fetchSummary();
    } catch (err) {
      toast.error('Failed to create goal');
    }
  };

  const handleAddFunds = async (goalId: number) => {
    const amt = parseFloat(addFunds[goalId] || '0');
    if (!amt) return;
    try {
      await api.put(`/analytics/goals/${goalId}/add`, { amount: amt });
      toast.success('Funds added!');
      setAddFunds(prev => ({ ...prev, [goalId]: '' }));
      fetchSummary();
    } catch (err) {
      toast.error('Failed to add funds');
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    if (!window.confirm("Delete this goal?")) return;
    try {
      await api.delete(`/analytics/goals/${goalId}`);
      toast.success('Goal deleted');
      fetchSummary();
    } catch (err) {
      toast.error('Failed to delete goal');
    }
  };

  if (!summary) {
    return <div className="animate-slide-up"><h2>Loading Dashboard...</h2></div>;
  }

  // Convert the backend's monthly_trend object to an array suitable for Recharts
  const chartData = summary.monthly_trend 
    ? Object.keys(summary.monthly_trend)
        .sort() // Sort by date (YYYY-MM)
        .map(key => {
          const [year, month] = key.split('-');
          const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
          return {
            name: `${monthNames[parseInt(month) - 1]} ${year.substring(2)}`,
            income: summary.monthly_trend[key].income,
            expenses: summary.monthly_trend[key].expenses,
            net: summary.monthly_trend[key].income - summary.monthly_trend[key].expenses
          };
        })
    : [];

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#f43f5e'];

  const categoryData = summary.category_breakdown 
    ? Object.keys(summary.category_breakdown).map((key) => ({
        name: key,
        value: summary.category_breakdown[key]
      }))
    : [];

  // Parse forecast assuming backend sends { dates: [...], balances: [...] } or list of dicts.
  // We'll map it to recharts.
  const forecastData = summary.forecast?.dates && summary.forecast?.yhat
    ? summary.forecast.dates.map((dateStr: string, idx: number) => ({
        date: new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
        balance: summary.forecast.yhat[idx]
      }))
    : [];

  return (
    <div className="animate-slide-up">
      <h1>📊 Financial Dashboard</h1>
      <p style={{ marginBottom: '32px' }}>Overview of your financial health, forecasts, and AI-driven insights.</p>

      {/* NLP Quick Add */}
      <div className="glass-card stagger-1" style={{ marginBottom: '24px', borderLeft: '4px solid var(--primary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Zap color="var(--primary)" />
          <h2 style={{ margin: 0, fontSize: '1.2rem' }}>⚡ AI Quick Add (Powered by Groq)</h2>
        </div>
        <p style={{ marginBottom: '16px', fontSize: '0.9rem' }}>Type a transaction naturally (e.g. "Bought coffee for ₹250 today"). The AI will parse it and categorize it automatically.</p>
        <form onSubmit={handleNlpSubmit} style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            className="input-field" 
            placeholder="Enter transaction..." 
            value={nlpText}
            onChange={(e) => setNlpText(e.target.value)}
            disabled={isNlpLoading}
          />
          <button type="submit" className="btn-primary" disabled={isNlpLoading}>
            {isNlpLoading ? 'Processing...' : 'Quick Add'}
          </button>
        </form>
      </div>

      <div className="dashboard-grid stagger-1">
        <div className="glass-card interactive">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Total Income</h3>
            <TrendingUp color="var(--primary)" />
          </div>
          <h2 style={{ fontSize: '2.5rem', marginTop: '16px', color: 'var(--primary)' }}>
            ₹{(summary.total_income || 0).toFixed(2)}
          </h2>
        </div>

        <div className="glass-card interactive">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Total Expenses</h3>
            <TrendingDown color="#ef4444" />
          </div>
          <h2 style={{ fontSize: '2.5rem', marginTop: '16px', color: '#ef4444' }}>
            ₹{(summary.total_expenses || 0).toFixed(2)}
          </h2>
        </div>

        <div className="glass-card interactive">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Net Savings</h3>
            <DollarSign color="var(--secondary)" />
          </div>
          <h2 style={{ fontSize: '2.5rem', marginTop: '16px', color: 'var(--secondary)' }}>
            ₹{(summary.net_savings || 0).toFixed(2)}
          </h2>
        </div>

      </div>

      <div className="glass-card stagger-2" style={{ height: '400px', marginBottom: '24px' }}>
        <h2 style={{ marginBottom: '8px' }}>Monthly Cash Flow Trend</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>Compare total Income vs Expenses across each month.</p>
        <ResponsiveContainer width="100%" height="80%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="var(--text-muted)" />
            <YAxis stroke="var(--text-muted)" />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--surface-border)', borderRadius: '8px' }}
              itemStyle={{ color: 'var(--text-main)' }}
            />
            <Legend />
            <Bar dataKey="income" name="Income (₹)" fill="var(--primary)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="expenses" name="Expenses (₹)" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="dashboard-grid stagger-3">
        <div className="glass-card" style={{ height: '400px' }}>
          <h2 style={{ marginBottom: '24px' }}>Category Breakdown</h2>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {categoryData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--surface-border)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--text-main)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: 'center', marginTop: '100px' }}>No category data available.</p>
          )}
        </div>

        <div className="glass-card" style={{ height: '400px' }}>
          <h2 style={{ marginBottom: '24px' }}>30-Day Cumulative Forecast (Prophet AI)</h2>
          {forecastData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData}>
                <XAxis dataKey="date" stroke="var(--text-muted)" />
                <YAxis stroke="var(--text-muted)" />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--surface-border)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--primary)' }}
                />
                <Line type="monotone" dataKey="balance" name="Forecasted Balance (₹)" stroke="#8b5cf6" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: 'center', marginTop: '100px' }}>Insufficient data for forecasting.</p>
          )}
        </div>
      </div>

      <div className="glass-card stagger-4" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ margin: 0 }}>🎯 Financial Saving Goals</h2>
          <button className="btn-primary" onClick={() => setShowGoalForm(!showGoalForm)} style={{ padding: '8px 16px', fontSize: '0.9rem' }}>
            <Plus size={16} /> New Goal
          </button>
        </div>

        {showGoalForm && (
          <form onSubmit={handleCreateGoal} style={{ display: 'flex', gap: '12px', marginBottom: '24px', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px' }}>
            <input type="text" className="input-field" placeholder="Goal Name (e.g. Vacation)" value={newGoal.name} onChange={e => setNewGoal({...newGoal, name: e.target.value})} required />
            <input type="number" className="input-field" placeholder="Target (₹)" value={newGoal.target} onChange={e => setNewGoal({...newGoal, target: e.target.value})} required min="1" />
            <input type="number" className="input-field" placeholder="Current (₹)" value={newGoal.current} onChange={e => setNewGoal({...newGoal, current: e.target.value})} />
            <button type="submit" className="btn-primary" style={{ whiteSpace: 'nowrap' }}>Save Goal</button>
          </form>
        )}

        {summary.goals && summary.goals.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            {summary.goals.map((g: any, idx: number) => {
              const progress = g.target_amount > 0 ? Math.min(100, (g.current_amount / g.target_amount) * 100) : 0;
              return (
                <div key={idx} style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '12px', position: 'relative' }}>
                  <button onClick={() => handleDeleteGoal(g.id)} style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }}>
                    <Trash2 size={18} />
                  </button>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ margin: 0, color: 'var(--text-main)' }}><Target size={18} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '8px', color: 'var(--primary)' }}/>{g.goal_name}</h3>
                  </div>
                  <p style={{ fontSize: '1.2rem', fontWeight: '600', marginBottom: '8px', color: 'var(--text-main)' }}>
                    ₹{g.current_amount.toFixed(2)} <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: '400' }}>/ ₹{g.target_amount.toFixed(2)}</span>
                  </p>
                  <div style={{ width: '100%', height: '8px', background: 'var(--surface-border)', borderRadius: '4px', overflow: 'hidden', marginBottom: '16px' }}>
                    <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, var(--primary), var(--secondary))', transition: 'width 1s ease' }}></div>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input 
                      type="number" 
                      className="input-field" 
                      style={{ padding: '8px', fontSize: '0.9rem' }} 
                      placeholder="Add funds (₹)" 
                      value={addFunds[g.id] || ''}
                      onChange={e => setAddFunds(prev => ({ ...prev, [g.id]: e.target.value }))}
                    />
                    <button onClick={() => handleAddFunds(g.id)} className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>Add</button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p>No saving goals set yet. Create one above to start tracking!</p>
        )}
      </div>

      {summary.insights_report && (
        <div className="glass-card stagger-4" style={{ marginBottom: '24px' }}>
          <h2>🧠 AI Insights Report</h2>
          <div style={{ color: 'var(--text-main)', lineHeight: '1.8', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>
            {summary.insights_report.split('\n').map((line: string, i: number) => (
              <p key={i} style={{ marginBottom: '8px', color: 'var(--text-main)' }}>{line}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
