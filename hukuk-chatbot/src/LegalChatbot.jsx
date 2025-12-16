import React, { useState, useRef, useEffect } from 'react';
import { Send, BookOpen, Scale, AlertCircle, Loader2 } from 'lucide-react';

// Config dosyası
const config = {
  API_BASE_URL: 'https://cathern-imino-alfredo.ngrok-free.dev', // ngrok URL'inizi buraya yazın (örn: https://xxxx-xx-xx-xx-xx.ngrok-free.app)
  ENDPOINTS: {
    HEALTH: '/health',
    CHAT: '/chat',
    CHAT_STREAM: '/chat/stream'
  }
};

const LegalChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}${config.ENDPOINTS.HEALTH}`);
      if (response.ok) {
        setApiStatus('connected');
      } else {
        setApiStatus('error');
      }
    } catch (error) {
      setApiStatus('error');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${config.API_BASE_URL}${config.ENDPOINTS.CHAT_STREAM}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage.content })
      });

      if (!response.ok) {
        throw new Error('API isteği başarısız oldu');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let assistantMessage = {
        role: 'assistant',
        content: '',
        sources: [],
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.chunk) {
                assistantMessage.content += data.chunk;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = { ...assistantMessage };
                  return newMessages;
                });
              }

              if (data.sources) {
                assistantMessage.sources = data.sources;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = { ...assistantMessage };
                  return newMessages;
                });
              }

              if (data.done) {
                break;
              }
            } catch (e) {
              console.error('JSON parse error:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
        error: true,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const exampleQuestions = [
    "Mesafeli satışta cayma hakkım var mı?",
    "Ayıplı ürünü nasıl iade edebilirim?",
    "Online alışverişte iade süresi ne kadar?"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-2">
            <Scale className="w-8 h-8" />
            <h1 className="text-2xl font-bold">Hukuk Pusulası</h1>
          </div>
          <p className="text-blue-100 text-sm">Türk Tüketici Hukuku Asistanı</p>

          {/* API Status */}
          <div className="mt-3 flex items-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${
              apiStatus === 'connected' ? 'bg-green-400' :
              apiStatus === 'error' ? 'bg-red-400' : 'bg-yellow-400'
            }`} />
            <span className="text-blue-100">
              {apiStatus === 'connected' ? 'Bağlı' :
               apiStatus === 'error' ? 'Bağlantı Hatası' : 'Kontrol Ediliyor...'}
            </span>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 text-blue-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Hoş Geldiniz!
              </h3>
              <p className="text-gray-600 mb-6">
                Tüketici haklarınız hakkında soru sorabilirsiniz
              </p>

              <div className="space-y-2 max-w-md mx-auto">
                <p className="text-sm text-gray-500 mb-3">Örnek sorular:</p>
                {exampleQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(question)}
                    className="w-full text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all text-sm text-gray-700"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.error
                    ? 'bg-red-50 border border-red-200 text-red-800'
                    : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>

                {message.sources && message.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
                      <BookOpen className="w-4 h-4" />
                      Kaynaklar:
                    </div>
                    <div className="space-y-1">
                      {message.sources.map((source, sourceIdx) => (
                        <div
                          key={sourceIdx}
                          className="text-xs text-gray-600 bg-gray-50 p-2 rounded"
                        >
                          {source}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Yanıt hazırlanıyor...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          {apiStatus === 'error' && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span>API'ye bağlanılamıyor. Config dosyasında URL'yi kontrol edin.</span>
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Sorunuzu yazın..."
              disabled={isLoading || apiStatus === 'error'}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim() || apiStatus === 'error'}
              className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          <p className="text-xs text-gray-500 mt-2 text-center">
            Bu asistan Türk Tüketici Hukuku konusunda bilgi sağlar
          </p>
        </div>
      </div>
    </div>
  );
};

export default LegalChatbot;
