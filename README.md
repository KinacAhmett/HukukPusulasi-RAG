# Hukuk Pusulası - Google Arama API ile Dosya Link Bulma

Bu proje, bozuk dosya linklerini Google arama API'si kullanarak bulmak için geliştirilmiş Python araçlarını içerir.

## Özellikler

- 🔍 **Google Arama Entegrasyonu**: Bozuk linkler için Google'da otomatik arama
- 📁 **Çoklu Dosya Formatı Desteği**: PDF, DOCX, DOC, XLSX, XLS
- 🔄 **Alternatif Uzantı Deneme**: Bir format bulunamazsa diğer formatları dener
- 📊 **Toplu İşlem**: Birden fazla URL'yi aynı anda işleyebilir
- 💾 **Sonuç Kaydetme**: JSON ve CSV formatlarında sonuç kaydetme
- ⚡ **Rate Limiting**: Google'ın arama limitlerini aşmamak için otomatik bekleme

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Proje dizinine gidin:
```bash
cd DataRetrieval
```

## Kullanım

### 1. Tek Link Arama

```python
from links import find_file_via_google_search

# Bozuk bir link için Google arama yap
broken_url = "https://ticaret.gov.tr/tuketici/mevzuat/6502-sayili-tuketicinin-korunmasi-hakkinda-kanun.pdf"
valid_url = find_file_via_google_search(broken_url)

if valid_url:
    print(f"Geçerli link bulundu: {valid_url}")
else:
    print("Geçerli link bulunamadı")
```

### 2. Sayfa Üzerindeki Linkleri Arama

```python
from links import find_possible_links_with_google_search

# Bir sayfadaki tüm linkleri kontrol et ve bozuk olanları Google'da ara
page_url = "https://ticaret.gov.tr/tuketici/mevzuat/6502-sayili-tuketicinin-korunmasi-mevzuati"
valid_links = find_possible_links_with_google_search(page_url, keyword="tüketici")

for link in valid_links:
    print(link)
```

### 3. Toplu İşlem

```python
from batch_google_search import BatchGoogleSearch

# Bozuk URL listesi
broken_urls = [
    "https://ticaret.gov.tr/tuketici/mevzuat/6502-sayili-tuketicinin-korunmasi-hakkinda-kanun.pdf",
    "https://ticaret.gov.tr/tuketici/mevzuat/tuketici-sozlesmeleri-hakkinda-yonetmelik.docx"
]

# Batch işlemi başlat
batch_searcher = BatchGoogleSearch()
summary = batch_searcher.process_broken_urls(broken_urls)

print(f"Başarı oranı: {summary['success_rate']:.1f}%")
```

### 4. Test Çalıştırma

```bash
# Basit test
python test_google_search.py

# Toplu işlem testi
python batch_google_search.py
```

## Fonksiyonlar

### `find_file_via_google_search(broken_url, max_results=10)`

Bozuk bir URL için Google arama yaparak geçerli dosya linkini bulur.

**Parametreler:**
- `broken_url` (str): Bozuk URL
- `max_results` (int): Maksimum arama sonucu sayısı

**Döndürür:**
- `str`: Geçerli dosya linki veya `None`

### `find_possible_links_with_google_search(page_url, keyword="")`

Bir sayfadaki linkleri bulur ve bozuk olanları Google arama ile düzeltir.

**Parametreler:**
- `page_url` (str): Kontrol edilecek sayfa URL'si
- `keyword` (str): Aranacak anahtar kelime

**Döndürür:**
- `list`: Geçerli link listesi

### `BatchGoogleSearch` Sınıfı

Toplu URL işleme için sınıf.

**Metodlar:**
- `process_broken_urls(broken_urls, max_results_per_url=10)`: URL listesini işler
- `save_results()`: Sonuçları JSON dosyasına kaydeder
- `export_to_csv(csv_file)`: Sonuçları CSV dosyasına aktarır
- `get_summary()`: Sonuçların özetini döndürür

## Arama Stratejisi

1. **Dosya Adı Arama**: URL'den dosya adını çıkarır ve Google'da arar
2. **Site Kısıtlaması**: Aynı domain içinde arama yapar
3. **Dosya Tipi Filtresi**: Belirli dosya uzantılarını arar
4. **Alternatif Uzantı Deneme**: Bulunamazsa farklı dosya formatlarını dener

## Çıktı Formatları

### JSON Çıktısı
```json
[
  {
    "original_url": "https://example.com/broken.pdf",
    "found_url": "https://example.com/working.pdf",
    "status": "found_via_google",
    "timestamp": "2024-01-15T10:30:00"
  }
]
```

### CSV Çıktısı
```csv
Orijinal URL,Bulunan URL,Durum,Zaman
https://example.com/broken.pdf,https://example.com/working.pdf,found_via_google,2024-01-15T10:30:00
```

## Durum Kodları

- `already_valid`: URL zaten geçerli
- `found_via_google`: Google arama ile bulundu
- `not_found`: Hiçbir geçerli link bulunamadı

## Önemli Notlar

⚠️ **Rate Limiting**: Google arama limitlerini aşmamak için her arama arasında 1 saniye bekleme yapılır.

⚠️ **API Sınırlamaları**: `googlesearch-python` kütüphanesi kullanıldığı için Google'ın resmi API'si değildir.

⚠️ **Türkçe Arama**: Türkçe sonuçlar için `lang="tr"` parametresi kullanılır.

## Sorun Giderme

### Yaygın Hatalar

1. **"No module named 'googlesearch'"**
   ```bash
   pip install googlesearch-python
   ```

2. **"Connection timeout"**
   - İnternet bağlantınızı kontrol edin
   - VPN kullanıyorsanız kapatmayı deneyin

3. **"Too many requests"**
   - Daha uzun bekleme süreleri ekleyin
   - Daha az URL ile test edin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 