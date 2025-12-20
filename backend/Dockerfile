FROM python:3.12-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# ChromaDB veritabanı dizinini oluştur (eğer yoksa)
RUN mkdir -p ./legal_chroma_db

# Port 5000'i expose et
EXPOSE 5000

# Uygulamayı başlat
CMD ["python", "app.py"]

