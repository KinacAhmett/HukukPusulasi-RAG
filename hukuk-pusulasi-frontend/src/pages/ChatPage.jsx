// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Header from '../components/Header';
import AccessibilityPanel from '../components/AccessibilityPanel';
import logo from '../logo.png';
import { API_ENDPOINTS } from '../config'; // ← YENİ: Config import

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
  const [sessionId, setSessionId] = useState(null);
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Backend bağlantı kontrolü
  useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.HEALTH); // ← DEĞİŞTİ
        if (response.data.status === 'healthy') {
          setIsBackendConnected(true);
          setMessages([
            {
              text: "Merhaba! Ben Tüketici Hukuku Pusulasınızım. Tüketici haklarınız konusunda size nasıl yardımcı olabilirim?",
              sender: "bot",
              timestamp: new Date()
            }
          ]);
          loadChatSessions();
        }
      } catch (error) {
        setIsBackendConnected(false);
        setMessages([
          {
            text: "⚠️ Backend sunucusuna bağlanılamadı. Lütfen backend'in çalıştığından emin olun.",
            sender: "bot",
            timestamp: new Date()
          }
        ]);
      }
    };

    checkBackendConnection();

    const savedSessionId = localStorage.getItem('chatSessionId');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  const handleSendMessage = async (event) => {
    event.preventDefault();
    if (inputMessage.trim() === '' && !selectedFile) return;

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
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    const currentMessage = inputMessage;
    const currentFile = selectedFile;

    setInputMessage('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    try {
      const response = await axios.post(
        API_ENDPOINTS.CHATBOT, // ← DEĞİŞTİ
        {
          message: currentMessage,
          session_id: sessionId || null,
          is_temporary: isTemporaryChat
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data.session_id) {
        const isNewChat = sessionId !== response.data.session_id;
        setSessionId(response.data.session_id);
        localStorage.setItem('chatSessionId', response.data.session_id);
        if (isNewChat) {
          loadChatSessions();
        }
      }

      const botMessage = {
        text: response.data.reply || "Yanıt alınamadı",
        sender: "bot",
        timestamp: new Date()
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);

    } catch (error) {
      console.error('HukukPusulası API hatası:', error);
      let errorMessage = "Üzgünüm, bir sorun oluştu. Lütfen tekrar deneyin.";

      if (error.response) {
        errorMessage = error.response.data.error || errorMessage;
      } else if (error.request) {
        errorMessage = "Backend sunucusuna ulaşılamıyor. Lütfen backend'in çalıştığından emin olun.";
      }

      setMessages((prevMessages) => [...prevMessages, {
        text: errorMessage,
        sender: "bot",
        timestamp: new Date()
      }]);
    }
  };

  const newChat = () => {
    setMessages([
      {
        text: "Merhaba! Ben Tüketici Hukuku Pusulasınızım. Tüketici haklarınız konusunda size nasıl yardımcı olabilirim?",
        sender: "bot",
        timestamp: new Date()
      }
    ]);

    setCurrentChatId(null);
    setSessionId(null);
    localStorage.removeItem('chatSessionId');
    setIsTemporaryChat(false);
    setSelectedFile(null);
    setInputMessage('');

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const loadChatSessions = async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.SESSIONS); // ← DEĞİŞTİ

      const loadedSessions = response.data.sessions.map(chat => ({
        ...chat,
        lastMessage: new Date(chat.lastMessage)
      }));

      setChatHistory(loadedSessions);
      console.log('Sohbet oturumları yüklendi:', loadedSessions);

    } catch (error) {
      console.error("Sohbet geçmişi (sessions) yüklenemedi:", error);
    }
  };

  const startTemporaryChat = () => {
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

  const loadChat = async (chatId) => {
    if (currentChatId === chatId) return;

    console.log(`Sohbet yükleniyor: ${chatId}`);
    try {
      const response = await axios.get(API_ENDPOINTS.HISTORY(chatId)); // ← DEĞİŞTİ

      const loadedMessages = response.data.history.map(msg => ({
        text: msg.text,
        sender: msg.sender,
        timestamp: new Date(msg.timestamp)
      }));

      setCurrentChatId(chatId);
      setMessages(loadedMessages);
      setIsTemporaryChat(false);

    } catch (error) {
      console.error('Sohbet geçmişi (history) yüklenirken hata:', error);
      alert('Seçili sohbet yüklenemedi.');
    }
  };

  const deleteChat = async (chatId) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm("Bu sohbeti kalıcı olarak silmek istediğinizden emin misiniz?")) {
      return;
    }

    try {
      await axios.delete(API_ENDPOINTS.DELETE_CHAT(chatId)); // ← DEĞİŞTİ

      setChatHistory(prev => prev.filter(c => c.id !== chatId));

      if (currentChatId === chatId) {
        newChat();
      }

    } catch (error) {
      console.error('Sohbet silinirken hata:', error);
      alert('Sohbet silinirken bir hata oluştu.');
    }
  };

  const filteredChatHistory = chatHistory.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="page-container">
      <a href="#main-content" className="skip-link">
        Ana içeriğe geç (Skip to main content)
      </a>

      <div id="input-help" className="sr-only">
        Tüketici hakları konusunda sorularınızı yazabilirsiniz. En fazla 500 karakter.
      </div>

      <Header />
      <div className="chatpage-container">
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

        <div className="chatpage-main" id="main-content">
          <div className="chatpage-header">
            <div className="header-left">
              <h2 className="header-title">Tüketici Hukuku Chatbot</h2>
              <div className="connection-status">
                <span className={`status-indicator ${isBackendConnected ? 'connected' : 'disconnected'}`}>
                  {isBackendConnected ? '🟢' : '🔴'}
                </span>
                <span className="status-text">
                  {isBackendConnected ? 'AI Bağlı' : 'AI Bağlantısız'}
                </span>
              </div>
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
            {messages.length === 0 ? (
              <div className="welcome-container">
                <div className="welcome-icon">🛡️</div>
                <h2 className="welcome-title">Tüketici Hukuku Pusulasına Hoş Geldiniz</h2>
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
                      <div className="message-text">
                        {msg.text}
                      </div>
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

            <form
              onSubmit={handleSendMessage}
              className="input-form"
              role="search"
              aria-label="Hukuki soru formu"
            >
              <div className="input-wrapper">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="file-btn"
                  title="PDF belge yükle (Alt+U)"
                  aria-label="PDF belge yükle"
                  accessKey="u"
                >
                  <span aria-hidden="true">➕</span>
                  <span className="sr-only">Dosya Ekle</span>
                </button>
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Tüketici hukuku sorunuzu buraya yazın..."
                  className="message-input"
                  aria-label="Hukuki soru yazın"
                  aria-describedby="input-help"
                  autoComplete="off"
                  maxLength="500"
                />
                <button
                  type="submit"
                  disabled={!inputMessage.trim() && !selectedFile}
                  className={`send-btn ${(inputMessage.trim() || selectedFile) ? 'active' : ''}`}
                  title="Mesajı gönder (Enter)"
                  aria-label="Mesajı gönder"
                >
                  <span aria-hidden="true">↗️</span>
                  <span className="sr-only">Gönder</span>
                </button>
              </div>
            </form>

            <div className="input-footer">
              Hukuk Pusulası size hukuki konularda yardımcı olmaya çalışır, ancak profesyonel hukuki tavsiye yerine geçmez.
            </div>
          </div>
        </div>
      </div>

      <AccessibilityPanel />
    </div>
  );
}

export default ChatPage;
