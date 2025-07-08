// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios'; // Chatbot API çağrıları için

function ChatPage() {
  const [messages, setMessages] = useState([]); // Mesajları tutacak dizi
  const [inputMessage, setInputMessage] = useState(''); // Kullanıcının yazdığı mesaj
  const messagesEndRef = useRef(null); // Mesajların otomatik aşağı kayması için

  // Mesajlar her güncellendiğinde en aşağı kaydırma
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Sayfa yüklendiğinde chatbot'tan hoş geldin mesajı
  useEffect(() => {
    setMessages([
      { text: "Merhaba! Hukuki konularda size nasıl yardımcı olabilirim?", sender: "bot" }
    ]);
  }, []);

  const handleSendMessage = async (event) => {
    event.preventDefault();
    if (inputMessage.trim() === '') return; // Boş mesaj göndermeyi engelle

    const userMessage = { text: inputMessage, sender: "user" };
    setMessages((prevMessages) => [...prevMessages, userMessage]); // Kullanıcı mesajını ekle
    setInputMessage(''); // Mesaj kutusunu temizle

    try {
      // BURADA CHATBOT API'NİZİ ÇAĞIRACAKSINIZ
      // Örn: 'http://localhost:5000/api/chatbot'
      const response = await axios.post('http://your-backend-api.com/api/chatbot', {
        message: inputMessage,
        // Eğer oturum bilgisi göndermeniz gerekiyorsa buraya ekleyin
        // userId: 'currentUserId'
      });

      const botMessage = { text: response.data.reply, sender: "bot" }; // API'den gelen cevabı kullanın
      setMessages((prevMessages) => [...prevMessages, botMessage]); // Chatbot cevabını ekle

    } catch (error) {
      console.error('Chatbot API hatası:', error.response ? error.response.data : error.message);
      setMessages((prevMessages) => [...prevMessages, { text: "Üzgünüm, bir sorun oluştu. Lütfen tekrar deneyin.", sender: "bot" }]);
    }
  };

  return (
    <div style={chatPageStyle}>
      <h2>Chatbot</h2>
      <div style={messagesContainerStyle}>
        {messages.map((msg, index) => (
          <div key={index} style={msg.sender === 'user' ? userMessageStyle : botMessageStyle}>
            {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} /> {/* Mesajların sonuna otomatik kaydırmak için */}
      </div>
      <form onSubmit={handleSendMessage} style={inputFormStyle}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Mesajınızı buraya yazın..."
          style={inputFieldStyle}
        />
        <button type="submit" style={sendButtonStyle}>Gönder</button>
      </form>
    </div>
  );
}

// Temel stil tanımları (Dilerseniz bunları App.css'e taşıyabilirsiniz)
const chatPageStyle = {
  display: 'flex',
  flexDirection: 'column',
  height: '80vh', // Ekran yüksekliğinin %80'i
  width: '80%',
  margin: '20px auto',
  border: '1px solid #ccc',
  borderRadius: '8px',
  overflow: 'hidden',
};

const messagesContainerStyle = {
  flexGrow: 1,
  padding: '10px',
  overflowY: 'auto',
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
  backgroundColor: '#f9f9f9',
};

const messageBaseStyle = {
  padding: '8px 12px',
  borderRadius: '15px',
  maxWidth: '70%',
};

const userMessageStyle = {
  ...messageBaseStyle,
  alignSelf: 'flex-end',
  backgroundColor: '#007bff',
  color: 'white',
  borderBottomRightRadius: '0',
};

const botMessageStyle = {
  ...messageBaseStyle,
  alignSelf: 'flex-start',
  backgroundColor: '#e2e6ea',
  color: '#333',
  borderBottomLeftRadius: '0',
};

const inputFormStyle = {
  display: 'flex',
  padding: '10px',
  borderTop: '1px solid #ccc',
  backgroundColor: '#fff',
};

const inputFieldStyle = {
  flexGrow: 1,
  padding: '10px',
  border: '1px solid #ddd',
  borderRadius: '20px',
  marginRight: '10px',
};

const sendButtonStyle = {
  padding: '10px 20px',
  backgroundColor: '#28a745',
  color: 'white',
  border: 'none',
  borderRadius: '20px',
  cursor: 'pointer',
};

export default ChatPage;