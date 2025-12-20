// src/components/Header.jsx
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import logo from '../logo.png';

const Header = () => {
  const [hoveredNav, setHoveredNav] = useState(null);
  const location = useLocation();

  // Tema state'i - localStorage'dan yükle veya varsayılan 'dark'
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('appTheme');
    return savedTheme || 'dark';
  });

  // Tema değiştiğinde uygula
  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    } else {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    }
    localStorage.setItem('appTheme', theme);
  }, [theme]);

  // İlk yüklemede tema uygula
  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    } else {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    }
  }, []);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header className="common-header">
      <div className="header-container">
        <div className="logo-section">
          <Link to="/" className="logo-link">
            <img src={logo} alt="Hukuk Pusulası Logo" className="header-logo" />
            <h1 className="logo-text">Hukuk Pusulası</h1>
          </Link>
        </div>
        <nav className="modern-nav">
          <Link
            to="/"
            className={`nav-item ${location.pathname === '/' ? 'active' : ''} ${hoveredNav && hoveredNav !== 'home' ? 'dimmed' : ''}`}
            onMouseEnter={() => setHoveredNav('home')}
            onMouseLeave={() => setHoveredNav(null)}
          >
            Ana Sayfa
          </Link>
          <Link
            to="/chat"
            className={`nav-item ${location.pathname === '/chat' ? 'active' : ''} ${hoveredNav && hoveredNav !== 'chat' ? 'dimmed' : ''}`}
            onMouseEnter={() => setHoveredNav('chat')}
            onMouseLeave={() => setHoveredNav(null)}
          >
            Chatbot
          </Link>
          <Link
            to="/login"
            className={`nav-item ${location.pathname === '/login' ? 'active' : ''} ${hoveredNav && hoveredNav !== 'login' ? 'dimmed' : ''}`}
            onMouseEnter={() => setHoveredNav('login')}
            onMouseLeave={() => setHoveredNav(null)}
          >
            Giriş Yap
          </Link>
          <button
            onClick={toggleTheme}
            className="theme-toggle"
            aria-label={theme === 'dark' ? 'Açık temaya geç' : 'Koyu temaya geç'}
            title={theme === 'dark' ? 'Açık Tema' : 'Koyu Tema'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </nav>
      </div>
    </header>
  );
};

export default Header;
