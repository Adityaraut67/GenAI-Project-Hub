import { useState } from 'react';
import { Copy, RefreshCcw, Send, Sparkles, Trash2 } from 'lucide-react';
import { api } from '../services/api';

const defaultSuggestions = [
  'What are government scholarships?',
  'How can I find Maharashtra government schemes?',
  'What documents are commonly required for scholarship applications?',
  'Explain this scheme in simple Marathi.',
];

export default function Assistant({ language, text }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const sendMessage = async (questionOverride) => {
    const currentQuestion = (questionOverride ?? input).trim();
    if (!currentQuestion) {
      setError(text.messages.emptyInput);
      return;
    }

    setError('');
    setMessages((previous) => [...previous, { type: 'user', text: currentQuestion }]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.askAssistant(currentQuestion, language);
      const answer = response.answer || 'No answer available.';
      const citations = response.citations || [];
      setMessages((previous) => [...previous, { type: 'assistant', text: answer, citations, llmAvailable: response.llm_available }]);
    } catch (err) {
      setMessages((previous) => [...previous, { type: 'assistant', text: err.message || text.messages.defaultError, citations: [] }]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (textContent) => {
    try {
      await navigator.clipboard.writeText(textContent);
    } catch {
      // fallback intentionally ignored
    }
  };

  return (
    <div className="container page-section narrow-page">
      <div className="section-head">
        <span className="eyebrow">{text.appName}</span>
        <h1>AI Assistant</h1>
      </div>

      <div className="chat-shell card-surface">
        <div className="chat-header">
          <div>
            <strong>{text.appName}</strong>
            <small>Source-aware civic guidance</small>
          </div>
          <button className="clear-button" type="button" onClick={() => setMessages([])}>
            <Trash2 size={16} /> {text.buttons.clear}
          </button>
        </div>

        <div className="chat-thread">
          {messages.length === 0 && (
            <div className="empty-chat">
              <Sparkles size={24} />
              <p>Ask a question about schemes, benefits, or public information.</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={`${message.type}-${index}`} className={`message-row ${message.type}`}>
              <div className="message-bubble">
                <p>{message.text}</p>
                {message.citations && message.citations.length > 0 && (
                  <div className="citation-box">
                    <strong>{text.labels.sourcePassages}</strong>
                    {message.citations.map((citation, idx) => (
                      <div key={`${citation.title}-${idx}`} className="citation-item">
                        <span>{citation.title}</span>
                        {citation.url && <a href={citation.url} target="_blank" rel="noreferrer">Official link</a>}
                        <small>{citation.content}</small>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {message.type === 'assistant' && (
                <div className="message-actions">
                  <button type="button" onClick={() => handleCopy(message.text)}><Copy size={14} /></button>
                  <button type="button" onClick={() => sendMessage(message.text)}><RefreshCcw size={14} /></button>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble loading-box">Thinking through the available evidence…</div>
            </div>
          )}
        </div>

        {error && <div className="inline-error">{error}</div>}

        <div className="suggestion-row">
          {defaultSuggestions.map((suggestion) => (
            <button key={suggestion} type="button" className="suggestion-chip" onClick={() => sendMessage(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>

        <div className="composer">
          <textarea
            value={input}
            rows={3}
            placeholder="Ask about scholarships, eligibility, or public scheme information..."
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
              }
            }}
          />
          <button className="primary-btn send-btn" type="button" onClick={() => sendMessage()} disabled={loading}>
            <Send size={16} /> {text.buttons.send}
          </button>
        </div>
      </div>
    </div>
  );
}
