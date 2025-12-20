// src/App.js
import './App.css'; // Mevcut CSS dosyanız
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage'; // Bu dosyayı src/pages/HomePage.jsx olarak oluşturmanız gerekmektedir.
import ChatPage from './pages/ChatPage'; // ChatPage bileşenini import ettik
import RegisterPage from './pages/RegisterPage'; // RegisterPage bileşenini import ettik

function App() {
  return (
    <Router>
      <div className="App">
        {/* Sayfa İçerikleri - Rotaya göre bileşen render edilecek */}
        <Routes>
          {/* Ana sayfa ve diğer sayfalar için rotalar */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/chat" element={<ChatPage />} /> 
          <Route path="/register" element={<RegisterPage />} />
          {/* Buraya diğer rotaları ekleyebilirsiniz, örneğin: */}
          {/* <Route path="/dashboard" element={<DashboardPage />} /> */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;