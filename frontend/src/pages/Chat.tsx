import { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import { Send, Bot, User } from 'lucide-react';

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI Financial Advisor. Ask me anything about your finances, budgets, or recent spending.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const res = await api.post('/chat', { message: userMsg });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error communicating with AI Advisor.' }]);
    }
    setIsLoading(false);
  };

  return (
    <div className="animate-slide-up" style={{ height: 'calc(100vh - 80px)', display: 'flex', flexDirection: 'column' }}>
      <h1>💬 AI Advisor Chat</h1>
      <p style={{ marginBottom: '24px' }}>Powered by Groq + LangGraph RAG Agent</p>

      <div className="glass-card stagger-1" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
        
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ 
              display: 'flex', 
              gap: '16px', 
              alignItems: 'flex-start',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
            }}>
              <div style={{ 
                width: '40px', height: '40px', borderRadius: '50%', 
                background: msg.role === 'user' ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                {msg.role === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="var(--primary)" />}
              </div>
              <div style={{ 
                background: msg.role === 'user' ? 'var(--primary-glow)' : 'rgba(255,255,255,0.05)',
                padding: '16px', borderRadius: '12px', maxWidth: '70%',
                border: msg.role === 'user' ? '1px solid var(--primary)' : '1px solid var(--surface-border)'
              }}>
                <p style={{ color: 'var(--text-main)', margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={20} color="var(--primary)" />
              </div>
              <div style={{ background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '12px', border: '1px solid var(--surface-border)' }}>
                <p style={{ color: 'var(--text-muted)', margin: 0 }}>Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ padding: '24px', borderTop: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.2)' }}>
          <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px' }}>
            <input 
              type="text" 
              className="input-field" 
              placeholder="Ask a question about your personal finances..."
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={isLoading}
              style={{ flex: 1 }}
            />
            <button type="submit" className="btn-primary" disabled={isLoading || !input.trim()}>
              <Send size={18} />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
