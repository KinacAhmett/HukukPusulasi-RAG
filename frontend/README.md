# Hukuk Pusulası - Frontend

Hukuk Pusulası projesinin React tabanlı frontend uygulaması.

## Özellikler

- 💬 AI destekli hukuki danışmanlık sohbeti
- 📄 PDF belge yükleme ve analiz
- 📚 Çoklu sohbet oturumu yönetimi
- 🔍 Sohbet geçmişi arama
- ♿ Erişilebilirlik özellikleri
- 🔐 Kullanıcı girişi ve kayıt

## Kurulum

### Gereksinimler

- Node.js 16+ ve npm
- Backend servisinin çalışıyor olması (http://localhost:5000)

### Yerel Geliştirme

```bash
# Bağımlılıkları yükle
npm install

# Geliştirme sunucusunu başlat
npm start
```

Uygulama http://localhost:3000 adresinde açılacaktır.

### Environment Variables

Frontend için API URL'i ayarlamak isterseniz `.env.local` dosyası oluşturabilirsiniz:

```env
REACT_APP_API_URL=http://localhost:5000
```

### Production Build

```bash
npm run build
```

Build edilmiş dosyalar `build/` klasörüne oluşturulur.

## Docker ile Çalıştırma

Detaylı Docker kurulumu için [DOCKER_README.md](./DOCKER_README.md) dosyasına bakın.

```bash
docker-compose up --build
```

## Proje Yapısı

```
frontend/
├── public/          # Statik dosyalar
├── src/
│   ├── components/  # React bileşenleri
│   │   ├── AccessibilityPanel.jsx
│   │   └── Header.jsx
│   ├── pages/       # Sayfa bileşenleri
│   │   ├── ChatPage.jsx
│   │   ├── HomePage.jsx
│   │   ├── LoginPage.jsx
│   │   └── RegisterPage.jsx
│   ├── App.js       # Ana uygulama bileşeni
│   └── index.js     # Giriş noktası
├── Dockerfile
└── docker-compose.yml
```

## Teknolojiler

- React 19
- React Router DOM
- Axios (HTTP istekleri)
- Create React App

## Geliştirme Notları

- API istekleri `src/config.js` dosyasında yapılandırılır
- Backend API URL'i environment variable ile ayarlanabilir
- Hot reload development modunda aktif
