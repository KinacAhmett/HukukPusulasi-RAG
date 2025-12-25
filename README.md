# Hukuk Pusulası - Tüketici Hukuku Chatbot

Tüketici hakları konusunda hukuki danışmanlık sağlayan AI destekli chatbot uygulaması.

## Proje Yapısı

```
HukukPusulasi/
├── backend/          # Flask backend API
│   ├── app.py        # Ana Flask uygulaması
│   ├── database.py   # SQLite veritabanı yönetimi
│   ├── model_service.py  # Gemini AI ve RAG entegrasyonu
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React frontend uygulaması
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── fineTuning/       # Model fine-tuning ve RAG hazırlık notebook'ları
│   ├── dataset_create.ipynb
│   ├── HukukPusulasi_RAG.ipynb
│   ├── .env.example
│   └── README.md
└── docker-compose.yml # Docker Compose yapılandırması (frontend klasöründe)
```

## Kurulum

### Docker ile Çalıştırma (Önerilen)

1. **Backend için `.env` dosyası oluşturun:**
   ```bash
   cd backend
   cp .env.example .env
   # .env dosyasını düzenleyip GOOGLE_API_KEY değerini ekleyin
   ```

2. **Docker Compose ile başlatın:**
   ```bash
   cd frontend
   docker-compose up --build
   ```

   Backend: http://localhost:5000
   Frontend: http://localhost:3000

   Detaylı Docker kurulumu için [frontend/DOCKER_README.md](./frontend/DOCKER_README.md) dosyasına bakın.

### Manuel Kurulum

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını düzenleyip GOOGLE_API_KEY değerini ekleyin
python app.py
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Özellikler

- 🤖 Gemini AI ile hukuki danışmanlık
- 📚 ChromaDB ile RAG (Retrieval-Augmented Generation)
- 💬 Çoklu sohbet oturumu yönetimi
- 📄 PDF belge yükleme ve analiz
- 🔍 Sohbet geçmişi arama
- ♿ Erişilebilirlik özellikleri

## Geliştirme Notları

- Backend `.env` dosyası `backend/` klasöründe olmalıdır (`.env.example` dosyasını kopyalayarak oluşturun)
- ChromaDB veritabanı `backend/legal_chroma_db/` klasöründe saklanır
- SQLite veritabanı `backend/chat.db` dosyasında saklanır
- Frontend API URL'i `REACT_APP_API_URL` environment variable ile ayarlanabilir
- Fine-tuning notebook'ları için detaylı bilgi: [fineTuning/README.md](./fineTuning/README.md)
- Frontend geliştirme için: [frontend/README.md](./frontend/README.md)

## Privacy & Security

- Asla gerçek API anahtarlarını commit etmeyin
- `.env` dosyaları `.gitignore` ile korunur
- Veritabanı dosyaları ve ChromaDB verileri kalıcı volume'lar ile saklanır
