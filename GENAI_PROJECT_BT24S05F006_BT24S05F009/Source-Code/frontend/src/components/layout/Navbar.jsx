import { Globe, House, MessageSquareText, Search, FileText, Info } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'home', icon: House },
  { to: '/assistant', label: 'assistant', icon: MessageSquareText },
  { to: '/schemes', label: 'schemes', icon: Search },
  { to: '/chat-pdf', label: 'pdf', icon: FileText },
  { to: '/about', label: 'about', icon: Info },
];

export default function Navbar({ language, onLanguageChange, text }) {
  return (
    <header className="topbar">
      <div className="container nav-content">
        <NavLink to="/" className="brand" aria-label="CivicLens AI home">
          <span className="brand-mark">C</span>
          <div>
            <strong>{text.appName}</strong>
            <small>{text.tagline}</small>
          </div>
        </NavLink>

        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Icon size={16} />
              <span>{text.nav[label]}</span>
            </NavLink>
          ))}
        </nav>

        <label className="language-picker" aria-label="Select language">
          <Globe size={16} />
          <select value={language} onChange={(event) => onLanguageChange(event.target.value)}>
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="mr">मराठी</option>
          </select>
        </label>
      </div>
    </header>
  );
}
