import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import '../App.css';

function RegisterPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    // Burada backend'e kayıt isteği gönderilebilir
    alert('Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz.');
    navigate('/login');
  };

  const handleLoginRedirect = () => {
    navigate('/login');
  };

  return (
    <div className="page-container">
      <Header />
      <div className="loginpage-container">
      <div className="login-form-box">
        <h2>Kayıt Ol</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="firstName">Ad</label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
            className="login-input"
            autoComplete="given-name"
          />
          <label htmlFor="lastName">Soyad</label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
            className="login-input"
            autoComplete="family-name"
          />
          <label htmlFor="email">E-posta</label>
          <input
            type="email"
            id="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="login-input"
            autoComplete="email"
          />
          <label htmlFor="password">Şifre</label>
          <input
            type="password"
            id="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
            autoComplete="new-password"
          />
          <button type="submit" className="login-btn">Kayıt Ol</button>
        </form>
        <div className="register-link-container">
          <span>Zaten hesabınız var mı? </span>
          <span className="register-link" onClick={handleLoginRedirect} tabIndex={0} role="button">Giriş yap</span>
        </div>
      </div>
    </div>
    </div>
  );
}

export default RegisterPage;
