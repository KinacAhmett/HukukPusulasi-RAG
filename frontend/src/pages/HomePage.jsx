// src/pages/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import '../App.css';

function HomePage() {
  return (
    <div className="modern-homepage">
      <Header />

      {/* Main Content */}
      <main className="modern-main">
        <div className="hero-section">
          <div className="hero-label">Tüketici Hukuku</div>
          <h1 className="hero-title">
            En Hassas Konularınız İçin
            <br />
            Güvenilir Hukuki Rehber
          </h1>
          <p className="hero-description">
            Hukuk Pusulası, tüketici haklarınızı korur ve 
            dünya standartlarında hukuki bilgi ve gizlilik önlemleri sunar.
          </p>
          <div className="hero-buttons">
            <Link to="/chat" className="btn-primary">
              Chatbot'u Deneyin
            </Link>
            <Link to="/register" className="btn-secondary">
              Hesap Oluşturun →
            </Link>
          </div>
        </div>
      </main>

      {/* Secondary Section */}
      <section className="secondary-section">
        <div className="section-container">
          <h2 className="section-title">
            Kurumsal Düzeyde
            <br />
            Hukuki Koruma
          </h2>
          <p className="section-description">
            Tüketici haklarınızı öğrenin, hukuki süreçleri anlayın ve 
            haklarınızı en etkili şekilde kullanın.
          </p>
        </div>
      </section>
    </div>
  );
}

export default HomePage;