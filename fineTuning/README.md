# Fine-Tuning ve RAG Hazırlık

Bu klasör, Hukuk Pusulası projesi için model fine-tuning ve RAG (Retrieval-Augmented Generation) sisteminin hazırlanması için kullanılan Jupyter notebook'larını içerir.

## İçerik

### Notebook'lar

1. **dataset_create.ipynb**
   - Hukuki belgelerden veri seti oluşturma
   - PDF'lerden metin çıkarma ve yapılandırma
   - Soru-cevap çiftleri oluşturma

2. **HukukPusulasi_RAG.ipynb**
   - RAG sistemi kurulumu ve testi
   - ChromaDB ile vektör veritabanı oluşturma
   - Embedding modeli entegrasyonu

3. **mahkeme_karar_download.ipynb**
   - Mahkeme kararlarını indirme ve işleme
   - Veri toplama ve temizleme

4. **model_finetune.ipynb**
   - Model fine-tuning işlemleri
   - Eğitim ve değerlendirme

5. **rag_finetune_combined.ipynb**
   - RAG ve fine-tuning'in birleşik kullanımı
   - Kombine model eğitimi

## Kurulum

### Gereksinimler

```bash
pip install jupyter notebook
pip install pandas numpy
pip install chromadb sentence-transformers
pip install google-generativeai
pip install PyPDF2
```

Veya backend'in `requirements.txt` dosyasındaki paketleri kullanabilirsiniz.

### Environment Variables

`.env.example` dosyasını kopyalayıp `.env` olarak kaydedin ve gerekli API anahtarlarını ekleyin:

```bash
cp .env.example .env
```

## Kullanım

1. Jupyter Notebook'u başlatın:
   ```bash
   jupyter notebook
   ```

2. İlgili notebook'u açın ve hücreleri sırayla çalıştırın.

3. Not: Büyük veri setleri ve model eğitimleri için yeterli RAM ve işlem gücü gereklidir.

## Notlar

- Notebook'lar geliştirme aşamasında kullanılmıştır
- Production ortamında backend'deki `model_service.py` kullanılır
- ChromaDB veritabanı `backend/legal_chroma_db/` klasöründe saklanır
- Eğitim verileri ve çıktılar `.gitignore` ile korunur

## Veri Güvenliği

- Asla gerçek API anahtarlarını commit etmeyin
- `.env` dosyaları `.gitignore` ile korunur
- Büyük veri dosyaları repository'ye eklenmez
