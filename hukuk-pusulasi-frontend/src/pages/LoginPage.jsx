// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; // useNavigate hook'unu import ettik
import '../App.css';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate(); // useNavigate hook'unu kullandık
  
  const handleSubmit = async (event) => {
    event.preventDefault(); // Formun varsayılan gönderimini engelle

    try {
      // Backend API adresinizi buraya yazın.
      // Örn: 'http://localhost:5000/api/login'
      const response = await axios.post('http://your-backend-api.com/api/login', { // Backend API adresinizi buraya yazın
        email,
        password,
      });
      console.log('Giriş başarılı:', response.data);
      // Başarılı girişten sonra kullanıcıyı '/chat' sayfasına yönlendir
      navigate('/chat');

    } catch (error) {
      console.error('Giriş hatası:', error.response.data);
      // Hata mesajını kullanıcıya gösterin
      alert('Giriş başarısız. Lütfen bilgilerinizi kontrol edin.');
    }
  };

  const handleRegisterRedirect = () => {
    navigate('/register');
  };

  return (
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
  );
}

export default LoginPage;

