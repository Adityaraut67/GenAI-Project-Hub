export default function About({ text }) {
  return (
    <div className="container page-section narrow-page">
      <div className="section-head">
        <span className="eyebrow">About CivicLens AI</span>
        <h1>Purpose and limitations</h1>
      </div>
      <div className="card-surface info-card">
        <p>
          CivicLens AI is a college-level information assistant designed to help citizens understand public schemes,
          government information, and document content more clearly using simple retrieval and AI-assisted explanations.
        </p>
        <p>
          The project is intentionally educational and lightweight. It does not claim to be an official government portal,
          does not submit applications, and should not be treated as a final decision-maker for eligibility or benefit approval.
        </p>
        <p>
          {text.legal.privacy}
        </p>
      </div>
    </div>
  );
}
