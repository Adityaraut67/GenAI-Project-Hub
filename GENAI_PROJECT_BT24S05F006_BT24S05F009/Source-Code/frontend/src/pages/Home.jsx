import { ArrowRight, BookOpenCheck, FileSearch, Languages, Search, ShieldCheck, Sparkles, Stethoscope, UserRoundSearch } from 'lucide-react';
import { Link } from 'react-router-dom';

const featureCards = [
  { icon: Sparkles, title: 'AI Government Assistant', description: 'Ask questions about schemes and government information in plain language.' },
  { icon: Search, title: 'Government Scheme Explorer', description: 'Browse verified and unverified scheme details in one place.' },
  { icon: FileSearch, title: 'Chat with PDF', description: 'Upload municipal or government PDFs and ask targeted questions.' },
  { icon: BookOpenCheck, title: 'Source-Based Answers', description: 'See evidence-backed answers and supporting passages.' },
  { icon: Languages, title: 'Multilingual Support', description: 'Switch easily between English, Hindi, and Marathi.' },
];

const categories = ['Education and Scholarships', 'Employment and Skill Development', 'Agriculture', 'Women and Child Welfare', 'Health', 'Housing'];

const steps = [
  'Choose a question or browse schemes.',
  'Retrieve relevant government information.',
  'Review context and understand source limits.',
];

const suggestions = [
  'What are government scholarships?',
  'How can I find Maharashtra government schemes?',
  'What documents are commonly required for scholarship applications?',
];

export default function Home({ text }) {
  return (
    <div className="page-section">
      <section className="hero-panel">
        <div className="container hero-grid">
          <div>
            <span className="eyebrow">{text.tagline}</span>
            <h1>{text.home.heading}</h1>
            <p className="hero-subtitle">{text.home.subtitle}</p>
            <div className="button-row">
              <Link to="/assistant" className="primary-btn">{text.buttons.askAssistant}<ArrowRight size={18} /></Link>
              <Link to="/schemes" className="secondary-btn">{text.buttons.exploreSchemes}</Link>
            </div>
            <div className="mini-badges">
              <span><ShieldCheck size={16} />Trusted overview</span>
              <span><UserRoundSearch size={16} />Source-aware</span>
            </div>
          </div>
          <div className="hero-visual card-surface">
            <div className="mini-card blue">
              <span>AI guidance</span>
              <strong>Simple answers</strong>
            </div>
            <div className="mini-card saffron">
              <span>Scheme insights</span>
              <strong>Eligibility + docs</strong>
            </div>
            <div className="mini-card green">
              <span>PDF support</span>
              <strong>Document Q&A</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="container trust-strip card-surface" aria-label="Platform highlights">
        <div><strong>80+</strong><span>scheme records</span></div>
        <div><strong>3</strong><span>interface languages</span></div>
        <div><strong>PDF</strong><span>page-aware answers</span></div>
        <div><strong>100%</strong><span>informational focus</span></div>
      </section>

      <section className="container section-block">
        <div className="section-head">
          <span className="eyebrow">Core Features</span>
          <h2>Designed for civic awareness</h2>
        </div>
        <div className="feature-grid">
          {featureCards.map(({ icon: Icon, title, description }) => (
            <div key={title} className="feature-card card-surface">
              <div className="icon-wrap"><Icon size={22} /></div>
              <h3>{title}</h3>
              <p>{description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container section-block">
        <div className="section-head">
          <span className="eyebrow">How it works</span>
          <h2>Clear steps, useful answers</h2>
        </div>
        <div className="steps-grid">
          {steps.map((step, index) => (
            <div key={step} className="step-card card-surface">
              <span className="step-number">0{index + 1}</span>
              <p>{step}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container section-block">
        <div className="section-head">
          <span className="eyebrow">Ask examples</span>
          <h2>Sample questions</h2>
        </div>
        <div className="suggestion-grid">
          {suggestions.map((item) => (
            <Link key={item} to="/assistant" className="suggestion-pill">{item}</Link>
          ))}
        </div>
      </section>

      <section className="container section-block">
        <div className="section-head">
          <span className="eyebrow">Explore categories</span>
          <h2>Government areas</h2>
        </div>
        <div className="category-grid">
          {categories.map((category) => (
            <div key={category} className="category-badge">{category}</div>
          ))}
        </div>
      </section>

      <section className="container section-block">
        <div className="pdf-preview card-surface">
          <div>
            <span className="eyebrow">PDF Assistant</span>
            <h2>Ask questions about uploaded government documents</h2>
            <p>Upload scheme notices, PDFs, or public documents and get targeted insights with page-aware evidence and source limits.</p>
            <Link to="/chat-pdf" className="primary-btn">Use PDF assistant <ArrowRight size={18} /></Link>
          </div>
          <div className="pdf-preview-panel">
            <div className="pdf-file">Document.pdf</div>
            <div className="pdf-line" />
            <div className="pdf-line short" />
            <div className="pdf-line medium" />
          </div>
        </div>
      </section>

      <section className="container section-block">
        <div className="section-head">
          <span className="eyebrow">Multilingual</span>
          <h2>Support for English, Hindi, and Marathi</h2>
        </div>
        <div className="language-strip card-surface">
          <div><strong>English</strong><span>Clear civic overviews</span></div>
          <div><strong>हिन्दी</strong><span>सरकारी जानकारी सरल भाषा में</span></div>
          <div><strong>मराठी</strong><span>सरकारी माहिती समजण्याजोगी</span></div>
        </div>
      </section>

      <section className="container section-block privacy-block">
        <div className="section-head">
          <span className="eyebrow">Responsible usage</span>
          <h2>Privacy and safe guidance</h2>
        </div>
        <div className="privacy-grid">
          <div className="privacy-card card-surface">
            <ShieldCheck size={20} />
            <h3>Privacy-first</h3>
            <p>Uploaded PDFs are processed temporarily and are not exposed as public documents.</p>
          </div>
          <div className="privacy-card card-surface">
            <Stethoscope size={20} />
            <h3>Informational only</h3>
            <p>{text.legal.disclaimer}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
