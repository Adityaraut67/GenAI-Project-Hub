import { useEffect, useMemo, useState } from 'react';
import { Search, Filter, ArrowRight, ShieldCheck, UserRoundSearch } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { schemeCategories } from '../data/translations';

export default function Schemes({ language, text }) {
  const [schemes, setSchemes] = useState([]);
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState({
    education: '',
    social_category: '',
    goal: '',
    occupation: '',
    age_group: '',
    state: 'Maharashtra',
  });
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationNote, setRecommendationNote] = useState('');
  const [recommendationLoading, setRecommendationLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await api.listSchemes(query, selectedCategory);
        setSchemes(data || []);
        setError('');
      } catch (err) {
        setError(err.message || 'Could not load schemes.');
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(load, 200);
    return () => clearTimeout(timer);
  }, [query, selectedCategory]);

  const categoryOptions = useMemo(() => ['All', ...schemeCategories], []);

  const updateProfile = (event) => {
    setProfile((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const findMatches = async (event) => {
    event.preventDefault();
    setRecommendationLoading(true);
    setError('');
    try {
      const result = await api.recommendSchemes(profile);
      setRecommendations(result.recommendations || []);
      setRecommendationNote(result.disclaimer || '');
    } catch (err) {
      setError(err.message || 'Could not find relevant schemes.');
    } finally {
      setRecommendationLoading(false);
    }
  };

  return (
    <div className="container page-section">
      <div className="section-head">
        <span className="eyebrow">Government scheme directory</span>
        <h1>Scheme Explorer</h1>
      </div>

      <div className="scheme-toolbar card-surface">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            value={query}
            placeholder={text.labels.searchSchemes}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <div className="filter-box">
          <Filter size={18} />
          <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)}>
            {categoryOptions.map((category) => (
              <option key={category} value={category === 'All' ? '' : category}>
                {category === 'All' ? 'All categories' : category}
              </option>
            ))}
          </select>
        </div>
      </div>

      <section className="eligibility-finder card-surface">
        <div className="finder-heading">
          <div className="icon-wrap"><UserRoundSearch size={22} /></div>
          <div>
            <span className="eyebrow">Guided discovery</span>
            <h2>Find schemes relevant to your profile</h2>
            <p>Answer a few optional questions. CivicLens AI will suggest potential matches, not make an official eligibility decision.</p>
          </div>
        </div>
        <form className="finder-form" onSubmit={findMatches}>
          <label>Education level or course
            <select name="education" value={profile.education} onChange={updateProfile}>
              <option value="">Any education level</option>
              <option value="school">School</option>
              <option value="higher">Higher education</option>
              <option value="technical">Technical or professional</option>
              <option value="vocational">Vocational training</option>
            </select>
          </label>
          <label>Social category
            <select name="social_category" value={profile.social_category} onChange={updateProfile}>
              <option value="">Prefer not to say</option>
              <option value="sc">SC</option>
              <option value="st">ST</option>
              <option value="obc">OBC</option>
              <option value="vjnt">VJNT</option>
              <option value="sbc">SBC</option>
              <option value="minority">Minority community</option>
              <option value="disability">Person with disability</option>
            </select>
          </label>
          <label>Your main goal
            <select name="goal" value={profile.goal} onChange={updateProfile}>
              <option value="">Select a goal</option>
              <option value="education">Education or scholarship</option>
              <option value="employment">Employment or skills</option>
              <option value="agriculture">Agriculture or farming</option>
              <option value="health">Health support</option>
              <option value="housing">Housing</option>
              <option value="business">Small business</option>
              <option value="social welfare">Social welfare</option>
            </select>
          </label>
          <label>Occupation
            <select name="occupation" value={profile.occupation} onChange={updateProfile}>
              <option value="">Not specified</option>
              <option value="student">Student</option>
              <option value="farmer">Farmer</option>
              <option value="worker">Worker</option>
              <option value="entrepreneur">Entrepreneur</option>
              <option value="senior citizen">Senior citizen</option>
            </select>
          </label>
          <button className="primary-btn finder-submit" type="submit" disabled={recommendationLoading}>
            <UserRoundSearch size={16} /> {recommendationLoading ? 'Finding matches…' : 'Find potential matches'}
          </button>
        </form>
        {recommendationNote && <div className="finder-note">{recommendationNote}</div>}
        {recommendations.length > 0 && (
          <div className="recommendation-grid">
            {recommendations.map((scheme) => (
              <article key={scheme.id} className="recommendation-card">
                <div className="scheme-card-header">
                  <span className="pill-category">{scheme.category}</span>
                  <span className={`verification-badge ${scheme.verification_status === 'VERIFIED' ? 'verified' : 'unverified'}`}>
                    {scheme.verification_status}
                  </span>
                </div>
                <h3>{scheme.name}</h3>
                <ul>
                  {scheme.match_reasons.map((reason) => <li key={reason}>{reason}</li>)}
                </ul>
                <Link to={`/schemes/${scheme.id}`} className="scheme-link">Review scheme details <ArrowRight size={15} /></Link>
              </article>
            ))}
          </div>
        )}
      </section>

      {error && <div className="inline-error">{error}</div>}

      {loading ? (
        <div className="loading-state">Loading schemes…</div>
      ) : schemes.length === 0 ? (
        <div className="empty-state">{text.messages.noSchemes}</div>
      ) : (
        <div className="scheme-grid">
          {schemes.map((scheme) => (
            <article key={scheme.id} className="scheme-card card-surface">
              <div className="scheme-card-header">
                <span className="pill-category">{scheme.category}</span>
                <span className={`verification-badge ${scheme.verification_status === 'VERIFIED' ? 'verified' : 'unverified'}`}>
                  <ShieldCheck size={14} /> {scheme.verification_status}
                </span>
              </div>
              <h3>{scheme.name}</h3>
              <p>{scheme.description}</p>
              <div className="meta-row">
                <strong>Beneficiaries:</strong>
                <span>{scheme.beneficiaries}</span>
              </div>
              <div className="meta-row">
                <strong>Eligibility:</strong>
                <span>{scheme.eligibility_summary || 'Not verified'}</span>
              </div>
              <div className="meta-row">
                <strong>Documents:</strong>
                <span>{scheme.required_documents || 'Not verified'}</span>
              </div>
              {scheme.source_url && (
                <a className="scheme-link" href={scheme.source_url} target="_blank" rel="noreferrer">
                  Official source
                </a>
              )}
              <Link to={`/schemes/${scheme.id}`} className="secondary-btn details-btn">
                View details <ArrowRight size={16} />
              </Link>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
