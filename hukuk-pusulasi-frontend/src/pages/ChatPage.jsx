// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Header from '../components/Header';
import AccessibilityPanel from '../components/AccessibilityPanel';
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
  const [sessionId, setSessionId] = useState(null);
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    // console.log('📊 Messages güncellendi:', messages.length, 'mesaj var'); // Debug
    // console.log('📋 Messages array:', messages); // Debug  
    scrollToBottom();
  }, [messages]);

  // Backend bağlantı kontrolü
useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/health');
        if (response.data.status === 'healthy') {
          setIsBackendConnected(true);
          setMessages([
            { 
              text: "Merhaba! Ben Tüketici Hukuku Pusulanızım. Tüketici haklarınız konusunda size nasıl yardımcı olabilirim?", 
              sender: "bot",
              timestamp: new Date()
            }
          ]);

          // Backend'in çalıştığını öğrendiğimiz an,
          // gidip sohbet geçmişimizi ondan istiyoruz.
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
    
    // Session ID'yi localStorage'dan al
    const savedSessionId = localStorage.getItem('chatSessionId');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  //
// ESKİ handleSendMessage FONKSİYONUNU TAMAMEN SİL
// VE YERİNE BU YENİ KODU YAPIŞTIR
//
  const handleSendMessage = async (event) => {
    event.preventDefault();
    if (inputMessage.trim() === '' && !selectedFile) return; // Boş mesaj ve dosya kontrolü

    // 1. Kullanıcı mesajını ekrana hemen ekle
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
    
    // 2. State'teki verileri geçici değişkenlere al (temizlemeden önce)
    const currentMessage = inputMessage;
    const currentFile = selectedFile;
    
    // 3. Input'ları temizle
    setInputMessage(''); 
    setSelectedFile(null); 
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    try {
      // --- BURASI DEĞİŞTİ (JSON -> FORMDATA) ---
      
      // 4. Veri paketi olarak 'FormData' oluştur
      // Bu, metin ve dosyaları birlikte göndermenin standart yoludur.
      const formData = new FormData();
      
      // 5. Backend'in (app.py) beklediği tüm verileri pakete ekle
      formData.append('message', currentMessage);
      formData.append('session_id', sessionId); // Bu 'null' olabilir, backend bunu anlıyor
      formData.append('is_temporary', isTemporaryChat); // 'true' veya 'false'
      
      if (currentFile) {
        // En önemli kısım: Dosyanın kendisini pakete ekle
        formData.append('file', currentFile, currentFile.name);
      }
      
      // 6. Backend API'yi 'FormData' ile çağır
      const response = await axios.post('http://localhost:5000/api/chatbot', 
        formData, // JSON objesi yerine formData'yı yolla
        {
          // 'Content-Type': 'application/json' HEADER'INI MUTLAKA KALDIRDIK.
          // Axios, FormData için 'multipart/form-data'yı otomatik ayarlar.
        }
      );
      // --- DEĞİŞİKLİK BİTTİ ---

      // 7. Gelen cevabı işle (Bu kısım eskisiyle aynı)
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
    // 1. EKRANI TEMİZLE (Bu sende zaten vardı)
    setMessages([
      { 
        text: "Merhaba! Ben Tüketici Hukuku Pusulanızım. Tüketici haklarınız konusunda size nasıl yardımcı olabilirim?", 
        sender: "bot",
        timestamp: new Date()
      }
    ]);
    
    // 2. HAFIZAYI SIFIRLA (Eksik olan ve hatayı çözen kısım bu)
    setCurrentChatId(null);   // Aktif seçili sohbeti kaldır
    setSessionId(null);       // Ana oturum ID'sini state'den sıfırla
    localStorage.removeItem('chatSessionId'); // Tarayıcı hafızasından da sıfırla
    
    // 3. DİĞERLERİNİ TEMİZLE (Bunlar da sende vardı)
    setIsTemporaryChat(false);
    setSelectedFile(null);
    setInputMessage(''); // Ekstra olarak input'u da temizleyelim

    // 4. DOSYA INPUT'UNU TEMİZLE
  if (fileInputRef.current) {
    fileInputRef.current.value = '';
    }
  };

//
// BU YENİ FONKSİYONU ChatPage.jsx İÇİNE EKLE
//
  const loadChatSessions = async () => {
    try {
      // 1. Backend'deki /api/sessions kapısını çağır
      const response = await axios.get('http://localhost:5000/api/sessions');
      
      // 2. Gelen "sessions" dizisini al
      const loadedSessions = response.data.sessions.map(chat => ({
        ...chat,
        // Backend'den gelen 'lastMessage' tarihini Date objesine çevir
        // Bu, senin 'filteredChatHistory' kodunun düzgün çalışması için önemli
        lastMessage: new Date(chat.lastMessage) 
      }));
      
      // 3. Kenar çubuğunu doldurmak için state'i güncelle
      setChatHistory(loadedSessions);
      console.log('Sohbet oturumları yüklendi:', loadedSessions);

    } catch (error) {
      console.error("Sohbet geçmişi (sessions) yüklenemedi:", error);
    }
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

  
  const loadChat = async (chatId) => {
    // Zaten o sohbetteyse bir şey yapma
    if (currentChatId === chatId) return; 

    console.log(`Sohbet yükleniyor: ${chatId}`);
    try {
      // 1. Backend'deki /api/history/<id> kapısını çağır
      const response = await axios.get(`http://localhost:5000/api/history/${chatId}`);
      
      // 2. Gelen 'history' dizisini frontend'in 'messages' formatına çevir
      const loadedMessages = response.data.history.map(msg => ({
        text: msg.text,
        sender: msg.sender,
        timestamp: new Date(msg.timestamp) // Tarih formatını düzelt
      }));

      // 3. State'i güncelle
      setCurrentChatId(chatId); // Hangi sohbette olduğumuzu ayarla
      setMessages(loadedMessages); // Mesajları ekrana bas
      setIsTemporaryChat(false); // Geçici sohbet modunda olmadığımızdan emin ol

    } catch (error) {
      console.error('Sohbet geçmişi (history) yüklenirken hata:', error);
      alert('Seçili sohbet yüklenemedi.');
    }
  };

  const deleteChat = async (chatId) => {
    // 1. Önce kullanıcıdan onay isteyelim (İsteğe bağlı ama iyi bir pratik)
    // eslint-disable-next-line no-restricted-globals
    if (!confirm("Bu sohbeti kalıcı olarak silmek istediğinizden emin misiniz?")) {
      return; // Kullanıcı "İptal" derse hiçbir şey yapma
    }

    try {
      // 2. Backend'deki /api/chat/<id> "DELETE" kapısını çağır
      await axios.delete(`http://localhost:5000/api/chat/${chatId}`);
      
      // 3. Backend'den SİLME BAŞARILI olursa, EKRANI güncelle
      // (Listeden o sohbeti çıkar)
      setChatHistory(prev => prev.filter(c => c.id !== chatId));
      
      // 4. Eğer silinen sohbet, o an açık olan sohbetse, "Yeni Sohbet" ekranına geç
      if (currentChatId === chatId) {
        newChat();
      }

    } catch (error) {
      console.error('Sohbet silinirken hata:', error);
      alert('Sohbet silinirken bir hata oluştu.');
    }
  };

  // Sohbet geçmişini filtrele
  const filteredChatHistory = chatHistory.filter(chat => 
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="page-container">
      {/* Skip Link */}
      <a href="#main-content" className="skip-link">
        Ana içeriğe geç (Skip to main content)
      </a>
      
      {/* Gizli yardım metni */}
      <div id="input-help" className="sr-only">
        Tüketici hakları konusunda sorularınızı yazabilirsiniz. En fazla 500 karakter.
      </div>
      
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

      {/* Erişilebilirlik Paneli */}
      <AccessibilityPanel />
    </div>
  );
}

export default ChatPage;