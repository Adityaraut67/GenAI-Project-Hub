import { useRef, useState } from 'react';
import { FileUp, LoaderCircle, RefreshCcw, Send, Trash2, UploadCloud } from 'lucide-react';
import { api } from '../services/api';

export default function ChatWithPDF({ language, text }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [sessionId, setSessionId] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sourcePassages, setSourcePassages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [extractedText, setExtractedText] = useState('');
  const [documentOverview, setDocumentOverview] = useState(null);
  const [documentMessage, setDocumentMessage] = useState('');

  const handleFileSelection = async (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError('');
    setUploading(true);

    try {
      const result = await api.uploadPdf(selectedFile);
      setSessionId(result.session_id);
      setExtractedText(result.passages?.slice(0, 3).map((part) => `Page ${part.page_number}: ${part.text}`).join('\n\n') || '');
      setDocumentMessage(result.message || '');
      setAnswer('');
      setSourcePassages([]);
      setDocumentOverview(result.document_overview || null);
    } catch (err) {
      setError(err.message || text.messages.defaultError);
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async () => {
    if (!sessionId) {
      setError('Please upload a PDF before asking a question.');
      return;
    }
    if (!question.trim()) {
      setError(text.messages.emptyInput);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.askPdf(sessionId, question, language);
      setAnswer(response.answer || 'No answer available.');
      setSourcePassages(response.source_passages || []);
    } catch (err) {
      setError(err.message || text.messages.defaultError);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (sessionId) {
      await api.clearPdfSession(sessionId).catch(() => undefined);
    }
    setFile(null);
    setSessionId('');
    setQuestion('');
    setAnswer('');
    setExtractedText('');
    setSourcePassages([]);
    setDocumentOverview(null);
    setDocumentMessage('');
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="container page-section narrow-page">
      <div className="section-head">
        <span className="eyebrow">PDF assistant</span>
        <h1>Chat with Government PDF</h1>
      </div>

      <div className="pdf-panel card-surface">
        <div className="upload-zone">
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            onChange={(event) => handleFileSelection(event.target.files?.[0])}
          />
          <div className="upload-content">
            <UploadCloud size={30} />
            <p>Drag and drop or browse a PDF</p>
            <button type="button" className="secondary-btn" onClick={() => inputRef.current?.click()}>
              <FileUp size={16} /> {text.buttons.uploadFile}
            </button>
          </div>
        </div>

        {uploading && <div className="loading-state"><LoaderCircle className="spin" size={18} /> Processing PDF…</div>}
        {file && <div className="file-meta">Selected file: {file.name}</div>}
        {error && <div className="inline-error">{error}</div>}
        {documentMessage && <div className={extractedText ? 'document-status' : 'document-status warning'}>{documentMessage}</div>}

        {extractedText && (
          <div className="pdf-preview-box">
            <h3>Extracted text preview</h3>
            <pre>{extractedText}</pre>
          </div>
        )}

        {documentOverview && (
          <div className="document-overview">
            <h3>What this document may be useful for</h3>
            <p>{documentOverview.notice}</p>
            <ul>
              {documentOverview.possible_uses.map((use) => <li key={use}>{use}</li>)}
            </ul>
            <h4>Try asking</h4>
            <div className="suggested-question-list">
              {documentOverview.suggested_questions?.map((suggestion) => (
                <button type="button" className="question-chip" key={suggestion} onClick={() => setQuestion(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="pdf-question-box">
          <textarea
            value={question}
            placeholder="Ask a question about the uploaded PDF…"
            rows={3}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="button-row">
            <button type="button" className="primary-btn" onClick={handleAsk} disabled={loading || !sessionId}>
              <Send size={16} /> {text.buttons.send}
            </button>
            <button type="button" className="secondary-btn" onClick={handleClear}>
              <Trash2 size={16} /> {text.buttons.clearPdf}
            </button>
          </div>
        </div>

        {loading && <div className="loading-state"><LoaderCircle className="spin" size={18} /> Searching document passages…</div>}

        {answer && (
          <div className="answer-card">
            <h3>Answer</h3>
            <p>{answer}</p>
          </div>
        )}

        {sourcePassages.length > 0 && (
          <div className="citation-box">
            <h3>Relevant source passages</h3>
            {sourcePassages.map((passage, index) => (
              <div key={`${passage.title}-${index}`} className="citation-item">
                <strong>Page {passage.metadata?.page_number || index + 1}</strong>
                <small>{passage.content}</small>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
