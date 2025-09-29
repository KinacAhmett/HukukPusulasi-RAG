// src/components/Header.jsx
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import logo from '../logo.png';

const Header = () => {
  const [hoveredNav, setHoveredNav] = useState(null);
  const location = useLocation();

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
        </nav>
      </div>
    </header>
  );
};

export default Header;