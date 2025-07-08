// src/App.js
import './App.css'; // Mevcut CSS dosyanız
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage'; // Bu dosyayı src/pages/HomePage.jsx olarak oluşturmanız gerekmektedir.
import ChatPage from './pages/ChatPage'; // ChatPage bileşenini import ettik
import logo from './logo.png'; // Eğer logonuzu hala kullanmak isterseniz bu satırı koruyabilirsiniz

function App() {
  return (
    <Router>
      <div className="App">
        {/* Navigasyon çubuğu */}
        <nav className="App-nav">
          <ul>
            <img src={logo} alt="HukukPusulası Logo" className="App-logo" style={{ height: '100px', width: '125px' }} />
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
            {/* Ana sayfa ve diğer sayfalar için rotalar */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/chat" element={<ChatPage />} /> 
            {/* Buraya diğer rotaları ekleyebilirsiniz, örneğin: */}
            {/* <Route path="/register" element={<RegisterPage />} /> */}
            {/* <Route path="/dashboard" element={<DashboardPage />} /> */}
          </Routes>
        </div>

        {/* Footer */}
        {<footer className="App-footer">
          <p>&copy; {new Date().getFullYear()} HukukPusulası. Tüm Hakları Saklıdır.</p>
        </footer> }
      </div>
    </Router>
  );
}

export default App;