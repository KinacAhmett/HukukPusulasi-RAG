# Docker Kurulumu ve Kullanımı

Bu proje Docker ve Docker Compose kullanılarak çalıştırılabilir.

## Gereksinimler

- Docker Desktop (veya Docker Engine + Docker Compose)
- Docker versiyonu 20.10 veya üzeri

## Hızlı Başlangıç

### 1. Tüm servisleri başlatma

Proje kök dizininde (docker-compose.yml dosyasının bulunduğu yerde) şu komutu çalıştırın:

```bash
docker-compose up --build
```

Bu komut:
- Backend ve frontend için Docker image'larını oluşturur
- Her iki servisi de başlatır
- Backend: http://localhost:5000
- Frontend: http://localhost:3000

### 2. Arka planda çalıştırma

Servisleri arka planda çalıştırmak için:

```bash
docker-compose up -d --build
```

### 3. Servisleri durdurma

```bash
docker-compose down
```

### 4. Logları görüntüleme

```bash
docker-compose logs -f
```

Belirli bir servisin loglarını görmek için:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Yapılandırma

### Environment Variables

#### Backend

Backend için `.env` dosyası oluşturmanız gerekiyor. `backend/` klasöründe `.env` dosyası oluşturun:

```env
GOOGLE_API_KEY=your_api_key_here
```

#### Frontend

Frontend için API URL'i environment variable ile ayarlanabilir. `docker-compose.yml` dosyasında `REACT_APP_API_URL` değişkenini düzenleyebilirsiniz.

## Veri Kalıcılığı

Aşağıdaki veriler Docker volume'ları ile kalıcı hale getirilmiştir:

- `backend/chat.db` - SQLite veritabanı
- `backend/legal_chroma_db/` - ChromaDB vektör veritabanı

Bu dosyalar host makinede saklanır ve container'lar yeniden başlatıldığında korunur.

## Sorun Giderme

### Port zaten kullanılıyor

Eğer 5000 veya 3000 portları zaten kullanılıyorsa, `docker-compose.yml` dosyasındaki port mapping'leri değiştirebilirsiniz:

```yaml
ports:
  - "5001:5000"  # Backend için
  - "3001:3000"  # Frontend için
```

### Backend bağlantı hatası

Frontend'den backend'e bağlanamıyorsanız:

1. Backend container'ının çalıştığından emin olun: `docker-compose ps`
2. Backend loglarını kontrol edin: `docker-compose logs backend`
3. `.env` dosyasının doğru yapılandırıldığından emin olun

### Image'ları yeniden oluşturma

Değişikliklerden sonra image'ları yeniden oluşturmak için:

```bash
docker-compose build --no-cache
docker-compose up
```

## Geliştirme Notları

- Frontend development modunda çalışır (hot reload aktif)
- Backend debug modunda çalışır
- Her iki servis de değişiklikleri otomatik olarak algılar

## Production Kullanımı

Production için:

1. Frontend'i build edin: `npm run build` (veya Dockerfile'da production build kullanın)
2. Backend'de `FLASK_ENV=production` ayarlayın
3. Gerekli güvenlik önlemlerini alın (HTTPS, firewall, vb.)

