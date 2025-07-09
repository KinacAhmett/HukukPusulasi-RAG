// src/pages/HomePage.jsx
import React from 'react';
import logo from '../logo.png';
import '../App.css';

function HomePage() {
  return (
    <div className="homepage-container">
      <img src={logo} alt="HukukPusulası Logo" className="homepage-logo" />
      <div className="homepage-content">
        <h2>HukukPusulası'na Hoş Geldiniz!</h2>
        <p>
          <b>HukukPusulası</b>, özellikle <b>Tüketici Hukuku</b> alanında hukuki metinlerle eğitilmiş bir yapay zeka asistanıdır. Amacımız, hukuki konularda ön bilgilendirme sağlayarak size yol göstermektir.
        </p>
        <p>
          <b>Gizliliğiniz bizim için çok önemli!</b> Paylaştığınız bilgiler gizli tutulur ve üçüncü şahıslarla paylaşılmaz.
        </p>
        <p>
          <b>Uyarı:</b> Bu uygulama bir avukatın yerini tutmaz. Sunulan bilgiler yalnızca ön bilgilendirme amaçlıdır. Kesin ve bağlayıcı hukuki görüş için bir avukata danışmalısınız.
        </p>
      </div>
    </div>
  );
}

export default HomePage;