// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Header from '../components/Header';
import logo from '../logo.png';

function ChatPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [isTemporaryChat, setIsTemporaryChat] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setMessages([
      { 
        text: "Merhaba! Ben Tüketici Hukuku Pusulanızım. Tüketici haklarınız konusunda size nasıl yardımcı olabilirim?", 
        sender: "bot",
        timestamp: new Date()
      }
    ]);
  }, []);

  const handleSendMessage = async (event) => {
    event.preventDefault();
    if (inputMessage.trim() === '' && !selectedFile) return; // Boş mesaj ve dosya kontrolü

    let messageText = inputMessage;
    if (selectedFile) {
      messageText = inputMessage.trim() 
        ? `${inputMessage}\n\n📎 Ek: ${selectedFile.name}` 
        : `📎 PDF Dosyası: ${selectedFile.name}`;
    }

    const userMessage = { 
      text: messageText, 
      sender: "user",
      timestamp: new Date(),
      hasFile: !!selectedFile
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]); // Kullanıcı mesajını ekle
    
    const currentMessage = inputMessage;
    const currentFile = selectedFile;
    setInputMessage(''); // Mesaj kutusunu temizle
    setSelectedFile(null); // Dosyayı temizle
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    try {
      // BURADA CHATBOT API'NİZİ ÇAĞIRACAKSINIZ
      // Örn: 'http://localhost:5000/api/chatbot'
      const response = await axios.post('http://your-backend-api.com/api/chatbot', {
        message: currentMessage,
        // Eğer oturum bilgisi göndermeniz gerekiyorsa buraya ekleyin
        // userId: 'currentUserId'
      });

      const botMessage = { 
        text: response.data.reply, 
        sender: "bot",
        timestamp: new Date()
      }; // API'den gelen cevabı kullanın
      setMessages((prevMessages) => [...prevMessages, botMessage]); // Chatbot cevabını ekle

    } catch (error) {
      console.error('Chatbot API hatası:', error.response ? error.response.data : error.message);
      setMessages((prevMessages) => [...prevMessages, { 
        text: "Üzgünüm, bir sorun oluştu. Lütfen tekrar deneyin.", 
        sender: "bot",
        timestamp: new Date()
      }]);
    }
  };

  const newChat = () => {
    // Mevcut sohbeti kaydet (eğer mesaj varsa ve geçici sohbet değilse)
    if (messages.length > 1 && currentChatId === null && !isTemporaryChat) {
      const newChatId = Date.now().toString();
      const firstUserMessage = messages.find(msg => msg.sender === 'user');
      const chatTitle = firstUserMessage 
        ? firstUserMessage.text.substring(0, 30) + (firstUserMessage.text.length > 30 ? '...' : '')
        : 'Yeni Sohbet';
      
      const newChatHistory = {
        id: newChatId,
        title: chatTitle,
        messages: [...messages],
        lastMessage: new Date()
      };
      
      setChatHistory(prev => [newChatHistory, ...prev]);
    }

    // Yeni sohbet başlat
    setCurrentChatId(null);
    setIsTemporaryChat(false);
    setSelectedFile(null);
    setMessages([
      { 
        text: "Merhaba! Ben Tüketici Hukuku Pusulanızım. Tüketici haklarınız konusunda size nasıl yardımcı olabilirim?", 
        sender: "bot",
        timestamp: new Date()
      }
    ]);
  };

  const startTemporaryChat = () => {
    // Mevcut sohbeti kaydet (eğer normal sohbet ise)
    if (messages.length > 1 && currentChatId === null && !isTemporaryChat) {
      const newChatId = Date.now().toString();
      const firstUserMessage = messages.find(msg => msg.sender === 'user');
      const chatTitle = firstUserMessage 
        ? firstUserMessage.text.substring(0, 30) + (firstUserMessage.text.length > 30 ? '...' : '')
        : 'Yeni Sohbet';
      
      const newChatHistory = {
        id: newChatId,
        title: chatTitle,
        messages: [...messages],
        lastMessage: new Date()
      };
      
      setChatHistory(prev => [newChatHistory, ...prev]);
    }

    // Geçici sohbet başlat
    setCurrentChatId(null);
    setIsTemporaryChat(true);
    setSelectedFile(null);
    setMessages([
      { 
        text: "🕐 Geçici Sohbet Modu\n\nBu sohbet geçici olarak açılmıştır. Sohbet geçmişinize kaydedilmeyecek ve oturum sonlandığında silinecektir.\n\nTüketici haklarınız konusunda size nasıl yardımcı olabilirim?", 
        sender: "bot",
        timestamp: new Date()
      }
    ]);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    } else {
      alert('Lütfen sadece PDF dosyası seçiniz.');
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const loadChat = (chatId) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
    }
  };

  const deleteChat = (chatId) => {
    setChatHistory(prev => prev.filter(c => c.id !== chatId));
    if (currentChatId === chatId) {
      newChat();
    }
  };

  // Sohbet geçmişini filtrele
  const filteredChatHistory = chatHistory.filter(chat => 
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="page-container">
      <Header />
      <div className="chatpage-container">
        {/* Sidebar */}
      <div className={`chatpage-sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="menu-toggle">
            ☰
          </button>
          {sidebarOpen && <h3 className="sidebar-title">Hukuk Pusulası</h3>}
        </div>
        
        {!sidebarOpen && (
          <div className="compact-buttons">
            <button onClick={newChat} className="compact-btn" title="Yeni Sohbet">
              ✏️
            </button>
            <button onClick={() => setSidebarOpen(true)} className="compact-btn" title="Sohbette Ara">
              🔍
            </button>
          </div>
        )}
        
        {sidebarOpen && (
          <div className="sidebar-content">
            <button onClick={newChat} className="new-chat-btn">
              ✏️ Yeni Sohbet
            </button>
            
            <div className="search-section">
              <div className="search-wrapper">
                <input
                  type="text"
                  placeholder="Sohbetlerde ara..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
                <span className="search-icon">🔍</span>
              </div>
            </div>

            <div className="chat-history">
              <h4 className="section-title">Sohbetler</h4>
              <div className="chat-list">
                {filteredChatHistory.length === 0 ? (
                  <div className="empty-list">
                    {searchQuery ? 'Arama sonucu bulunamadı' : 'Henüz sohbet geçmişi yok'}
                  </div>
                ) : (
                  filteredChatHistory.map((chat) => (
                    <div key={chat.id} className="chat-item">
                      <button 
                        onClick={() => loadChat(chat.id)}
                        className={`chat-btn ${currentChatId === chat.id ? 'active' : ''}`}
                      >
                        <div className="chat-title">{chat.title}</div>
                        <div className="chat-time">
                          {chat.lastMessage.toLocaleDateString('tr-TR', { 
                            day: 'numeric', 
                            month: 'short' 
                          })}
                        </div>
                      </button>
                      <button onClick={() => deleteChat(chat.id)} className="delete-btn" title="Sohbeti sil">
                        🗑️
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Ana İçerik */}
      <div className="chatpage-main">
        <div className="chatpage-header">
          <div className="header-left">
            <h2 className="header-title">Tüketici Hukuku Chatbot</h2>
          </div>
          <div className="header-right">
            <button onClick={startTemporaryChat} className="temp-chat-btn">
              🕐 Geçici Sohbet
            </button>
          </div>
        </div>

        {isTemporaryChat && (
          <div className="temp-notification">
            <span className="temp-icon">🕐</span>
            <span className="temp-text">Geçici Sohbet Modu - Bu sohbet kaydedilmeyecek</span>
            <button onClick={newChat} className="temp-close" title="Normal sohbete dön">✕</button>
          </div>
        )}

        <div className="messages-container">
          {messages.length === 1 ? (
            <div className="welcome-container">
              <div className="welcome-icon">🛡️</div>
              <h2 className="welcome-title">Tüketici Hukuku Pusulanıza Hoş Geldiniz</h2>
              <p className="welcome-subtitle">
                Tüketici haklarınız konusunda sorularınız için buradayım. Size nasıl yardımcı olabilirim?
              </p>
              <div className="suggestions">
                <button onClick={() => setInputMessage("Tüketici haklarım nelerdir?")} className="suggestion-btn">
                  Tüketici Hakları
                </button>
                <button onClick={() => setInputMessage("Satın aldığım üründe sorun var, ne yapmalıyım?")} className="suggestion-btn">
                  Ürün Sorunu
                </button>
                <button onClick={() => setInputMessage("İade ve değişim haklarım nelerdir?")} className="suggestion-btn">
                  İade Hakları
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className="message-wrapper">
                <div className={`message-container ${msg.sender}`}>
                  <div className="message-avatar">
                    {msg.sender === 'user' ? '👤' : '⚖️'}
                  </div>
                  <div className="message-content">
                    <div className="message-text">{msg.text}</div>
                    <div className="message-time">
                      {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          
          {selectedFile && (
            <div className="file-preview">
              <div className="file-info">
                <span className="file-icon">📄</span>
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
              </div>
              <button onClick={removeFile} className="remove-file">✕</button>
            </div>
          )}
          
          <form onSubmit={handleSendMessage} className="input-form">
            <div className="input-wrapper">
              <button 
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="file-btn"
                title="PDF yükle"
              >
                ➕
              </button>
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Tüketici hukuku sorunuzu buraya yazın..."
                className="message-input"
              />
              <button 
                type="submit" 
                disabled={!inputMessage.trim() && !selectedFile}
                className={`send-btn ${(inputMessage.trim() || selectedFile) ? 'active' : ''}`}
              >
                ↗️
              </button>
            </div>
          </form>
          
          <div className="input-footer">
            Hukuk Pusulası size hukuki konularda yardımcı olmaya çalışır, ancak profesyonel hukuki tavsiye yerine geçmez.
          </div>
        </div>
      </div>
    </div>
    </div>
  );
}



export default ChatPage;