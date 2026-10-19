export default function Footer({ text }) {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <h3>{text.appName}</h3>
          <p>{text.tagline}</p>
        </div>
        <div>
          <h4>Explore</h4>
          <ul>
            <li><a href="/assistant">AI Assistant</a></li>
            <li><a href="/schemes">Scheme Explorer</a></li>
            <li><a href="/chat-pdf">Chat with PDF</a></li>
          </ul>
        </div>
        <div>
          <h4>About</h4>
          <p>{text.legal.disclaimer}</p>
        </div>
      </div>
    </footer>
  );
}
