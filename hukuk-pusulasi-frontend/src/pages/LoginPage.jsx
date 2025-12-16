// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { API_ENDPOINTS } from '../config'; // ← YENİ: Config import
import '../App.css';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await axios.post(API_ENDPOINTS.LOGIN, { // ← DEĞİŞTİ
        email,
        password,
      });
      console.log('Giriş başarılı:', response.data);

      // Token'ı localStorage'a kaydet (eğer backend token gönderiyorsa)
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
      }

      navigate('/chat');

    } catch (error) {
      console.error('Giriş hatası:', error.response?.data || error.message);
      alert('Giriş başarısız. Lütfen bilgilerinizi kontrol edin.');
    }
  };

  const handleRegisterRedirect = () => {
    navigate('/register');
  };

  return (
    <div className="page-container">
      <Header />
      <div className="loginpage-container">
        <div className="login-form-box">
          <h2>Giriş Yap</h2>
          <form onSubmit={handleSubmit}>
            <label htmlFor="email">E-posta</label>
            <input
              type="email"
              id="email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="login-input"
              autoComplete="username"
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
              autoComplete="current-password"
            />
            <button type="submit" className="login-btn">Giriş Yap</button>
          </form>
          <div className="register-link-container">
            <span>Hesabınız yok mu? </span>
            <span className="register-link" onClick={handleRegisterRedirect} tabIndex={0} role="button">Kayıt olun</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
