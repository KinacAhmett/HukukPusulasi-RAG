// src/pages/RegisterPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Header from '../components/Header';
import { API_ENDPOINTS } from '../config'; // ← YENİ: Config import
import '../App.css';

function RegisterPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(API_ENDPOINTS.REGISTER, { // ← DEĞİŞTİ
        firstName,
        lastName,
        email,
        password,
      });

      console.log('Kayıt başarılı:', response.data);
      alert('Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz.');
      navigate('/login');

    } catch (error) {
      console.error('Kayıt hatası:', error.response?.data || error.message);

      let errorMessage = 'Kayıt sırasında bir hata oluştu.';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      }

      alert(errorMessage);
    } finally {
      setLoading(false);
    }
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
              minLength="6"
            />
            <button
              type="submit"
              className="login-btn"
              disabled={loading}
            >
              {loading ? 'Kayıt Yapılıyor...' : 'Kayıt Ol'}
            </button>
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
