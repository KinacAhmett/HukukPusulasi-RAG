// src/App.js
import './App.css'; // Mevcut CSS dosyanız
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage'; // Bu dosyayı src/pages/HomePage.jsx olarak oluşturmanız gerekmektedir.
import ChatPage from './pages/ChatPage'; // ChatPage bileşenini import ettik
import logo from './logo.svg'; // Eğer logonuzu hala kullanmak isterseniz bu satırı koruyabilirsiniz

function App() {
  return (
    <Router>
      <div className="App">
        {/* Navigasyon çubuğu */}
        <nav className="App-nav">
          <ul>
            <li>
              <Link to="/">Ana Sayfa</Link>
            </li>
            <li>
              <Link to="/login">Giriş Yap</Link>
            </li>
            <li>
              <Link to="/chat">Chatbot</Link> {/* Chat sayfasına link ekledik */}
            </li>
            {/* Diğer linkler buraya eklenebilir, örneğin Kayıt Ol, Profil vb. */}
          </ul>
        </nav>

        {/* Sayfa İçerikleri - Rotaya göre bileşen render edilecek */}
        <div className="App-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/chat" element={<ChatPage />} /> {/* Yeni chat sayfası rotası */}
            {/* Buraya diğer rotaları ekleyebilirsiniz, örneğin: */}
            {/* <Route path="/register" element={<RegisterPage />} /> */}
            {/* <Route path="/dashboard" element={<DashboardPage />} /> */}
          </Routes>
        </div>

        {/* Eğer bir footer eklemek isterseniz buraya ekleyebilirsiniz */}
        {/* <footer className="App-footer">
          <p>&copy; {new Date().getFullYear()} HukukPusulası. Tüm Hakları Saklıdır.</p>
        </footer> */}
      </div>
    </Router>
  );
}

export default App;