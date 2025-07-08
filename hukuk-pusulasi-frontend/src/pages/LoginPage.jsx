// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; // useNavigate hook'unu import ettik


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
  return (
    <div>
      <h1>Giriş Yap</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="email">E-posta:</label>
        <input
          type="email"
          id="email"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <br />
        <label htmlFor="password">Şifre:</label>
        <input
          type="password"
          id="password"
          name="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <br />
        <button type="submit">Giriş Yap</button>
      </form>
    </div>
  );
}

export default LoginPage;

