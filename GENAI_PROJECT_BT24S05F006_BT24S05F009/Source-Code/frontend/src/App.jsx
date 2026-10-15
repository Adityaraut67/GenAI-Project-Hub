import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import { uiText } from './data/translations';
import Home from './pages/Home';
import Assistant from './pages/Assistant';
import Schemes from './pages/Schemes';
import SchemeDetails from './pages/SchemeDetails';
import ChatWithPDF from './pages/ChatWithPDF';
import About from './pages/About';
import NotFound from './pages/NotFound';

function App() {
  const [language, setLanguage] = useState(() => localStorage.getItem('civiclens-language') || 'en');

  useEffect(() => {
    localStorage.setItem('civiclens-language', language);
  }, [language]);

  const text = useMemo(() => uiText[language] || uiText.en, [language]);

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Navbar language={language} onLanguageChange={setLanguage} text={text} />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Home text={text} />} />
            <Route path="/assistant" element={<Assistant language={language} text={text} />} />
            <Route path="/schemes" element={<Schemes language={language} text={text} />} />
            <Route path="/schemes/:id" element={<SchemeDetails />} />
            <Route path="/chat-pdf" element={<ChatWithPDF language={language} text={text} />} />
            <Route path="/about" element={<About text={text} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer text={text} />
      </div>
    </BrowserRouter>
  );
}

export default App;
