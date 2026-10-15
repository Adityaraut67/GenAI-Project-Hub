import { useEffect, useState } from 'react';
import { ArrowLeft, BadgeCheck, ExternalLink, FileText } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../services/api';

export default function SchemeDetails() {
  const { id } = useParams();
  const [scheme, setScheme] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getScheme(id);
        setScheme(data);
      } catch (err) {
        setError(err.message || 'Scheme could not be loaded.');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id]);

  if (loading) return <div className="container page-section loading-state">Loading scheme details…</div>;
  if (error) return <div className="container page-section inline-error">{error}</div>;
  if (!scheme) return null;

  return (
    <div className="container page-section narrow-page">
      <Link to="/schemes" className="back-link">
        <ArrowLeft size={16} /> Back to schemes
      </Link>

      <article className="scheme-detail card-surface">
        <div className="scheme-card-header detail-header">
          <span className="pill-category">{scheme.category}</span>
          <span className={`verification-badge ${scheme.verification_status === 'VERIFIED' ? 'verified' : 'unverified'}`}>
            <BadgeCheck size={14} /> {scheme.verification_status}
          </span>
        </div>

        <h1>{scheme.name}</h1>
        <p className="lead-text">{scheme.description}</p>

        <div className="details-grid">
          <div>
            <h3>Beneficiaries</h3>
            <p>{scheme.beneficiaries || 'Not specified'}</p>
          </div>
          <div>
            <h3>Eligibility summary</h3>
            <p>{scheme.eligibility_summary || 'Not verified'}</p>
          </div>
          <div>
            <h3>Required documents</h3>
            <p>{scheme.required_documents || 'Not verified'}</p>
          </div>
          {scheme.source_url && (
            <div>
              <h3>Official source</h3>
              <a href={scheme.source_url} target="_blank" rel="noreferrer">
                <ExternalLink size={16} /> {scheme.source_url}
              </a>
            </div>
          )}
        </div>

        <div className="detail-note">
          <FileText size={18} />
          <span>{scheme.verify_note || 'This record is informational and should be checked against the relevant official source before making important decisions.'}</span>
        </div>
      </article>
    </div>
  );
}
