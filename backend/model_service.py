"""
model_service.py - Gemini + ChromaDB RAG Entegrasyonu
Bu dosya modelle ilgili tüm işlemleri yönetir.
"""

import os
import google.generativeai as genai
import PyPDF2
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional

# ============================================================================
# GLOBAL DEĞİŞKENLER
# ============================================================================
gemini_model = None
vector_store = None
semantic_processor = None
distance_analyzer = None
# Session bazlı chat session'ları tutmak için dictionary
chat_sessions = {}  # {session_id: ChatSession}
# Session bazlı PDF içeriklerini tutmak için dictionary
pdf_contexts = {}  # {session_id: str}

# ============================================================================
# YAPILANDIRMA
# ============================================================================
CHROMADB_PERSIST_DIR = "./legal_chroma_db"  # ChromaDB klasörü
CHROMADB_COLLECTION_NAME = "legal_documents_v2"
EMBEDDING_MODEL_NAME = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"

# ============================================================================
# DISTANCE ANALYZER (Notebook'tan alındı)
# ============================================================================
class DistanceAnalyzer:
    """ChromaDB L2 distance için optimize edilmiş threshold'lar"""

    QUALITY_THRESHOLDS = {
        'excellent': 200.0,
        'good': 350.0,
        'acceptable': 500.0,
        'poor': 650.0
    }

    def __init__(self):
        self.distance_history = []

    def categorize_distance(self, distance: float) -> str:
        if distance < self.QUALITY_THRESHOLDS['excellent']:
            return 'excellent'
        elif distance < self.QUALITY_THRESHOLDS['good']:
            return 'good'
        elif distance < self.QUALITY_THRESHOLDS['acceptable']:
            return 'acceptable'
        elif distance < self.QUALITY_THRESHOLDS['poor']:
            return 'poor'
        else:
            return 'very_poor'

    def filter_by_quality(self, results: Dict, quality_level: str = 'acceptable') -> Dict:
        if not results.get('documents') or not results['documents']:
            return {'documents': [], 'metadatas': [], 'distances': [], 'n_results': 0}

        docs = results['documents'][0] if isinstance(results['documents'][0], list) else results['documents']
        metas = results['metadatas'][0] if isinstance(results['metadatas'][0], list) else results['metadatas']
        dists = results['distances'][0] if isinstance(results['distances'][0], list) else results['distances']

        threshold = self.QUALITY_THRESHOLDS.get(quality_level, 500.0)

        filtered_docs = []
        filtered_metas = []
        filtered_dists = []

        for doc, meta, dist in zip(docs, metas, dists):
            if dist <= threshold:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                filtered_dists.append(dist)

        if filtered_dists:
            self.distance_history.extend(filtered_dists)

        return {
            'documents': filtered_docs,
            'metadatas': filtered_metas,
            'distances': filtered_dists,
            'n_results': len(filtered_docs)
        }

# ============================================================================
# SEMANTIC QUERY PROCESSOR (Notebook'tan alındı)
# ============================================================================
class SemanticQueryProcessor:
    def __init__(self, embedding_model_name: str):
        self.embedder = SentenceTransformer(embedding_model_name)

        self.legal_concept_examples = {
            'cayma_hakki': [
                "ürünü iade etmek istiyorum",
                "siparişimi iptal edebilir miyim",
                "aklımı değiştirdim geri verebilir miyim",
                "cayma hakkım var mı",
                "vazgeçme süresi ne kadar"
            ],
            'ayipli_mal': [
                "ürün bozuk geldi",
                "kusurlu mal aldım",
                "telefon kırık çıktı",
                "defolu ürün ne yapmalıyım",
                "çalışmayan cihaz iade"
            ],
            'garanti': [
                "garanti süresi ne kadar",
                "arıza için garanti var mı",
                "üretici garantisi",
                "tamire gönderebilir miyim"
            ],
            'tazminat': [
                "zarar tazminatı isteyebilir miyim",
                "maddi zarar",
                "manevi tazminat",
                "zararımı karşılayabilir miyim"
            ]
        }

        self.contract_type_examples = {
            'mesafeli': [
                "online alışveriş",
                "internet üzerinden aldım",
                "e-ticaret sitesinden",
                "web sitesinden sipariş",
                "uzaktan satış"
            ],
            'kapidan': [
                "kapıda satış",
                "eve gelen satıcı",
                "kapımda sattılar",
                "iş yeri dışında satış"
            ],
            'taksitli': [
                "taksitle aldım",
                "kredi kartı taksit",
                "ödeme planı"
            ]
        }

        self.legal_embeddings = self._prepare_concept_embeddings(self.legal_concept_examples)
        self.contract_embeddings = self._prepare_concept_embeddings(self.contract_type_examples)

    def _prepare_concept_embeddings(self, examples_dict: Dict) -> Dict:
        import numpy as np
        result = {}
        for concept, examples in examples_dict.items():
            embeddings = self.embedder.encode(examples, convert_to_tensor=False)
            result[concept] = np.mean(embeddings, axis=0)
        return result

    def _semantic_similarity(self, query: str, concept_embeddings: Dict, threshold: float = 0.5) -> List[tuple]:
        import numpy as np
        query_embedding = self.embedder.encode([query], convert_to_tensor=False)[0]

        similarities = []
        for concept, concept_emb in concept_embeddings.items():
            sim = np.dot(query_embedding, concept_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(concept_emb)
            )
            if sim > threshold:
                similarities.append((concept, float(sim)))

        return sorted(similarities, key=lambda x: x[1], reverse=True)

    def detect_contract_type(self, query: str) -> Optional[str]:
        matches = self._semantic_similarity(query, self.contract_embeddings, threshold=0.45)
        return matches[0][0] if matches else None

    def extract_legal_concepts(self, query: str) -> List[tuple]:
        return self._semantic_similarity(query, self.legal_embeddings, threshold=0.40)

    def enrich_query(self, query: str) -> Dict:
        contract_type = self.detect_contract_type(query)
        legal_concepts = self.extract_legal_concepts(query)

        enriched_parts = [query]

        if contract_type:
            type_map = {
                'mesafeli': 'mesafeli sözleşme internet alışverişi',
                'kapidan': 'kapıdan satış doğrudan satış',
                'taksitli': 'taksitle satış kredi'
            }
            enriched_parts.append(type_map.get(contract_type, ''))

        concept_map = {
            'cayma_hakki': 'cayma hakkı iade vazgeçme',
            'ayipli_mal': 'ayıplı mal kusurlu ürün defolu',
            'garanti': 'garanti satıcı garantisi üretici garantisi',
            'tazminat': 'tazminat zarar ziyan'
        }

        for concept, score in legal_concepts[:2]:
            if score > 0.5:
                enriched_parts.append(concept_map.get(concept, ''))

        metadata_filters = None
        if contract_type:
            if contract_type == 'mesafeli':
                metadata_filters = {
                    "$or": [
                        {"file_name": {"$eq": "Regulation_MESAFELI_SOZLESMELER_YONETMELIGI.pdf"}},
                        {"file_name": {"$eq": "Law_TUKETICININ_KORUNMASI_HAKKINDA_KANUN.pdf"}},
                    ]
                }

        return {
            'original': query,
            'enriched': ' '.join(filter(None, enriched_parts)),
            'contract_type': contract_type,
            'legal_concepts': [c for c, s in legal_concepts],
            'concept_scores': legal_concepts,
            'metadata_filters': metadata_filters,
        }

# ============================================================================
# SMART VECTOR STORE (Notebook'tan alındı)
# ============================================================================
class SmartVectorStore:
    def __init__(self, persist_dir: str, collection_name: str, model_name: str):
        self.persist_directory = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name, device="cpu"
        )

        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"✅ ChromaDB: {self.collection.count()} doküman yüklendi")
        except Exception as e:
            print(f"❌ ChromaDB collection bulunamadı: {e}")
            self.collection = None

        self.semantic_processor = SemanticQueryProcessor(model_name)
        self.distance_analyzer = DistanceAnalyzer()

    def smart_search(self, query: str, n_results: int = 5) -> Dict:
        if not self.collection:
            return {'documents': [], 'metadatas': [], 'distances': [], 'n_results': 0}

        analysis = self.semantic_processor.enrich_query(query)

        print(f"\n🔍 Sorgu: '{query}'")
        print(f"📊 Sözleşme tipi: {analysis['contract_type'] or 'Belirsiz'}")

        all_results = []

        # Filtered search
        if analysis['metadata_filters']:
            print("1️⃣ Filtered search...")
            try:
                filtered = self.collection.query(
                    query_texts=[analysis['enriched']],
                    n_results=n_results,
                    where=analysis['metadata_filters'],
                    include=["documents", "metadatas", "distances"]
                )

                if filtered['ids'][0]:
                    for doc, meta, dist in zip(
                        filtered['documents'][0],
                        filtered['metadatas'][0],
                        filtered['distances'][0]
                    ):
                        all_results.append({
                            'document': doc,
                            'metadata': meta,
                            'distance': dist
                        })
                    print(f"   ✅ {len(filtered['ids'][0])} sonuç")
            except Exception as e:
                print(f"   ⚠️ Filtre hatası: {e}")

        # Semantic search
        print("2️⃣ Semantic search...")
        semantic = self.collection.query(
            query_texts=[analysis['enriched']],
            n_results=n_results * 2,
            include=["documents", "metadatas", "distances"]
        )

        for doc, meta, dist in zip(
            semantic['documents'][0],
            semantic['metadatas'][0],
            semantic['distances'][0]
        ):
            all_results.append({
                'document': doc,
                'metadata': meta,
                'distance': dist
            })

        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x['distance']):
            doc_hash = hash(r['document'][:100])
            if doc_hash not in seen_ids:
                seen_ids.add(doc_hash)
                unique_results.append(r)

        final_results = self.distance_analyzer.filter_by_quality(
            {
                'documents': [r['document'] for r in unique_results],
                'metadatas': [r['metadata'] for r in unique_results],
                'distances': [r['distance'] for r in unique_results],
            },
            quality_level='acceptable'
        )

        print(f"✅ Toplam {final_results['n_results']} kaliteli sonuç\n")

        return {
            'query': query,
            'n_results': min(final_results['n_results'], n_results),
            'documents': final_results['documents'][:n_results],
            'metadatas': final_results['metadatas'][:n_results],
            'distances': final_results['distances'][:n_results],
            'analysis': analysis
        }

# ============================================================================
# SOURCE FORMATTER
# ============================================================================
def format_source(doc: str, meta: Dict) -> str:
    """Kaynak bilgisini formatlar"""
    import re

    file_name = meta.get('file_name', 'Kaynak')
    doc_type = meta.get('doc_type', '')

    # Mahkeme kararları için esas no ve karar no'yu parse et
    if doc_type == 'court_decision':
        try:
            # Chunk içeriğinden esas no ve karar no'yu çıkar
            # Format: "ESAS NO : 2024/693 KARAR NO : 2025/160" veya "ESAS NO : 2024/752 Esas KARAR NO : 2025/363"
            # İlk 2000 karakter içinde ara (chunk başında olmalı)
            doc_start = doc[:2000] if len(doc) > 2000 else doc

            esas_match = re.search(r'ESAS\s+NO\s*[:：]\s*(\d{4}/\d+)', doc_start, re.IGNORECASE)
            karar_match = re.search(r'KARAR\s+NO\s*[:：]\s*(\d{4}/\d+)', doc_start, re.IGNORECASE)

            # Mahkeme adını çıkar - daha kapsamlı regex
            mahkeme_adi = None

            # Önce T.C. ile başlayanları kontrol et
            mahkeme_match = re.search(r'T\.C\.\s*([^\n]+?)(?:\n|ESAS|KARAR|DAVA)', doc_start, re.IGNORECASE | re.DOTALL)
            if mahkeme_match:
                mahkeme_adi = mahkeme_match.group(1).strip()
            else:
                # T.C. olmadan, satır başında mahkeme adı
                mahkeme_match = re.search(r'^([^\n]*?(?:ASLİYE|HUKUK|TİCARET|TÜKETİCİ|İŞ|AĞIR|CEZA)[^\n]*?MAHKEMESİ[^\n]*)', doc_start, re.IGNORECASE | re.MULTILINE)
                if mahkeme_match:
                    mahkeme_adi = mahkeme_match.group(1).strip()
                else:
                    # Sadece mahkeme adı (numarasız)
                    mahkeme_match = re.search(r'^([^\n]+(?:Hukuk Dairesi|Mahkemesi|MAHKEMESİ))', doc_start, re.IGNORECASE | re.MULTILINE)
                    if mahkeme_match:
                        mahkeme_adi = mahkeme_match.group(1).strip()

            # İçtihat Metni kontrolü
            ictihat_match = re.search(r'İçtihat\s+Metni', doc, re.IGNORECASE)
            ictihat_text = ' "İçtihat Metni"' if ictihat_match else ''

            esas_no = esas_match.group(1) if esas_match else None
            karar_no = karar_match.group(1) if karar_match else None

            # Format: "Mahkeme Adı 2024/752 E., 2025/363 K."
            parts = []

            if mahkeme_adi:
                # Mahkeme adını temizle (gereksiz boşlukları kaldır)
                mahkeme_adi = re.sub(r'\s+', ' ', mahkeme_adi).strip()
                parts.append(mahkeme_adi)

            if esas_no and karar_no:
                parts.append(f"{esas_no} E., {karar_no} K.")
            elif esas_no:
                parts.append(f"{esas_no} E.")
            elif karar_no:
                parts.append(f"{karar_no} K.")

            if parts:
                result = ' '.join(parts) + ictihat_text
                return result
        except Exception as e:
            print(f"⚠️ format_source hatası (court_decision): {e}")

        # Fallback durumunda None döndür (kaynak gösterilmeyecek)
        return None

    if file_name.startswith('Regulation_'):
        clean_name = file_name.replace('Regulation_', '').replace('.pdf', '').replace('_', ' ')
        article_num = meta.get('article_number')
        if article_num:
            return f"{clean_name} - Madde {article_num}"
        return clean_name
    elif file_name.startswith('Law_'):
        clean_name = file_name.replace('Law_', '').replace('.pdf', '').replace('_', ' ')
        article_num = meta.get('article_number')
        if article_num:
            return f"{clean_name} - Madde {article_num}"
        return clean_name

    return file_name.replace('.pdf', '').replace('_', ' ')

# ============================================================================
# MODEL İNİTİALİZATİON
# ============================================================================
def initialize_model():
    """
    Gemini modelini ve RAG sistemini yükler.
    """
    global gemini_model, vector_store

    try:
        # 1. Gemini'yi yapılandır
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")

        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Google Gemini modeli yüklendi.")

        # 2. ChromaDB Vector Store'u yükle
        vector_store = SmartVectorStore(
            CHROMADB_PERSIST_DIR,
            CHROMADB_COLLECTION_NAME,
            EMBEDDING_MODEL_NAME
        )

        if vector_store.collection is None:
            print("⚠️ ChromaDB yüklenemedi! RAG çalışmayacak, sadece PDF upload çalışacak.")

        return True

    except Exception as e:
        print(f"❌ Model yüklenirken hata: {e}")
        gemini_model = None
        vector_store = None
        return False

# ============================================================================
# PDF TEXT EXTRACTION
# ============================================================================
def _extract_text_from_pdf(pdf_file_stream):
    """PDF'ten metin çıkarır"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file_stream)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

        print(f"✅ PDF'ten {len(text)} karakter metin çıkarıldı.")
        return text
    except Exception as e:
        print(f"❌ PDF okunurken hata: {e}")
        return None

# ============================================================================
# SMART PROMPT CREATION
# ============================================================================
def create_smart_prompt(query: str, search_results: Dict, pdf_context: Optional[str] = None) -> tuple:
    """RAG için akıllı prompt oluşturur. PDF içeriği varsa onu da ekler."""
    analysis = search_results.get('analysis', {})

    contexts = []
    source_details = []

    for i, (doc, meta) in enumerate(zip(
        search_results['documents'],
        search_results['metadatas']
    )):
        source_info = format_source(doc, meta)
        # Fallback durumunda None dönen kaynakları atla
        if source_info is None:
            continue
        doc_text = doc.strip()[:600] + "..." if len(doc.strip()) > 600 else doc.strip()
        contexts.append(f"[Kaynak {i+1}]:\n{doc_text}")
        # Sadece kaynak adını sakla (numara olmadan)
        source_details.append(source_info)

    context_block = "\n\n".join(contexts)

    contract_guidance = ""
    if analysis.get('contract_type') == 'mesafeli':
        contract_guidance = "\n• Bu mesafeli sözleşme sorusu - cayma hakkı ve iade süreçlerine odaklan"
    elif 'ayipli_mal' in analysis.get('legal_concepts', []):
        contract_guidance = "\n• Bu ayıplı mal sorusu - tüketici haklarını ve çözüm yollarını açıkla"

    system_prompt = f"""
Sen Türkiye'de aktif olarak çalışan bir avukatsın.

UZMANLIK ALANIN:
SADECE TÜKETİCİ HUKUKU konularında danışmanlık veriyorsun.
Tüketicinin Korunması Hakkında Kanun, mesafeli satış, ayıplı mal/hizmet, garanti, cayma hakkı, tüketici kredileri, konut finansmanı, taksitle satış, doğrudan satış, abonelik sözleşmeleri, paket tur, devre tatil, ön ödemeli konut, tüketici hakem heyetleri, haksız şartlar, reklam ve haksız ticari uygulamalar gibi konularda uzmanlaşmışsın.

ROLÜN:
Kullanıcılara tüketici hukuku konularında hukuki danışmanlık verir gibi,
uygulamaya dönük, pratik ve yol gösterici cevaplar verirsin.

ÖNEMLİ KURAL - MUTLAKA UY:
Eğer kullanıcının sorusu tüketici hukuku dışında bir konuyla ilgiliyse (ceza hukuku, aile hukuku, iş hukuku, gayrimenkul hukuku, idare hukuku, belediye kararları, miras hukuku, ticaret hukuku vb.),
KESİNLİKLE cevap verme. Sadece şunu yaz: "Üzgünüm, bu konuda danışmanlık veremem. Sadece tüketici hukuku konularında (tüketici hakları, mesafeli satış, ayıplı mal, garanti, cayma hakkı, tüketici kredileri vb.) yardımcı olabilirim. Başka bir sorunuz varsa memnuniyetle yardımcı olurum."

Tüketici hukuku dışı konulara asla detaylı cevap verme, sadece yukarıdaki reddetme mesajını yaz.

KURALLAR:
- Akademik veya tez dili kullanma
- "verilen kaynaklara göre", "dokümanlar şunu söylüyor" gibi ifadeler kullanma
- Kaynak numarası, belge adı veya PDF referansı belirtme
- Bilgiyi içselleştirerek anlat
- KISA VE ÖZ cevap ver - kullanıcı sorunun cevabına hızlıca ulaşmalı
- Gereksiz detaylara girmeden direkt soruya odaklan

CEVAP TARZI:
- Net ve öz
- Resmi ama insani
- Gereksiz empati yok, samimi giriş var
- Avukat refleksiyle yönlendirici

CEVAP YAPISI (KISA VE ÖZ):
1. Durum özeti (sadece gerekirse "geçmiş olsun" - bilgi edinme sorularında gerekmez)
2. Kullanıcının hakları (kısa ve net)
3. Yapılması gerekenler (adım adım, öz)
4. Alternatif yollar (varsa, kısa)
5. Pratik öneriler (varsa, kısa)

HUKUKİ SINIR:
Somut olayda mutlaka bir avukata danışılması gerektiğini
nazikçe belirt ama cevabı bundan kaçmak için kullanma.
{contract_guidance}
"""

    user_prompt = f"""
Aşağıdaki hukuki bilgiler senin içindir.
Kullanıcıya cevap verirken bu metinlere atıf yapma.

HUKUKİ BAĞLAM:
{context_block}
"""

    # PDF içeriği varsa ekle
    if pdf_context:
        pdf_text = pdf_context.strip()[:2000] + "..." if len(pdf_context.strip()) > 2000 else pdf_context.strip()
        user_prompt += f"""

KULLANICININ YÜKLEDİĞİ PDF İÇERİĞİ:
{pdf_text}

**ÖNEMLİ:** Kullanıcının yüklediği PDF içeriğini de dikkate al. Hem yukarıdaki hukuki bağlamdaki bilgileri hem de PDF içeriğindeki bilgileri birleştirerek cevap ver.
"""

    user_prompt += f"""

SORU:
{query}
"""

    user_prompt += """

**ÇOK ÖNEMLİ - ÖNCE BUNU KONTROL ET:**
Kullanıcının sorusu TÜKETİCİ HUKUKU ile ilgili mi?

Tüketici hukuku konuları (sadece bunlar):
- Tüketicinin Korunması Hakkında Kanun ve tüketici hakları
- Mesafeli satış sözleşmeleri, online alışveriş
- Ayıplı mal ve ayıplı hizmet
- Garanti, garanti belgesi
- Cayma hakkı (mesafeli satış, taksitle satış, tüketici kredileri)
- Tüketici kredileri, konut finansmanı
- Taksitle satış sözleşmeleri
- Doğrudan satışlar, kapıdan satış
- İş yeri dışında kurulan sözleşmeler
- Abonelik sözleşmeleri
- Paket tur sözleşmeleri
- Devre tatil ve uzun süreli tatil hizmeti sözleşmeleri
- Ön ödemeli konut satışları
- Yenilenmiş ürünlerin satışı
- Tüketici sözleşmelerindeki haksız şartlar
- Tüketici hakem heyetleri
- Reklam ve haksız ticari uygulamalar
- Fiyat etiketi, satış sonrası hizmetler
- Finansal hizmetlere ilişkin mesafeli sözleşmeler
- Tüketici mahkemeleri ve tüketici davaları

Tüketici hukuku DIŞI konular (BUNLARI REDDET):
- Ceza hukuku, trafik cezaları, hakaret davaları
- Aile hukuku, boşanma, velayet, nafaka
- İş hukuku, işten çıkarma, fazla mesai
- Gayrimenkul hukuku, tapu, kira
- Miras hukuku, vasiyetname
- İdare hukuku, belediye kararları, kamu görevlisi
- Ticaret hukuku (işletme kuruluşu, ortaklık)
- Sigorta hukuku (hayat sigortası, genel sigorta)

EĞER SORU TÜKETİCİ HUKUKU DIŞINDA İSE:
Sadece şunu yaz: "Üzgünüm, bu konuda danışmanlık veremem. Sadece tüketici hukuku konularında (Tüketicinin Korunması Hakkında Kanun, mesafeli satış, ayıplı mal/hizmet, garanti, cayma hakkı, tüketici kredileri, konut finansmanı, taksitle satış, doğrudan satış, abonelik sözleşmeleri, paket tur, devre tatil, ön ödemeli konut, tüketici hakem heyetleri, haksız şartlar, reklam ve haksız ticari uygulamalar vb.) yardımcı olabilirim. Başka bir sorunuz varsa memnuniyetle yardımcı olurum."

EĞER SORU TÜKETİCİ HUKUKU İLE İLGİLİ İSE:
Cevabını KISA VE ÖZ yaz. Kullanıcı sorunun cevabına hızlıca ulaşmalı.

**ÖNEMLİ:**
- Sadece gerçekten bir sorun/zarar durumu varsa "geçmiş olsun" de
- Bilgi edinme sorularında "geçmiş olsun" deme
- Cevabında [1], [2] gibi referans numaraları KULLANMA - kaynaklar cevabın sonunda otomatik olarak güzel bir formatta listelenecek
- Cevabını doğrudan ve akıcı yaz, kaynak referansları olmadan

Cevabını şu yapıya uygun yaz (KISA VE ÖZ):
1. Durum özeti (gerekirse)
2. Haklarınız
3. Yapılması gerekenler
4. Alternatif yollar (varsa)
5. Pratik öneriler (varsa)
"""

    return system_prompt, user_prompt, source_details

# ============================================================================
# TITLE GENERATION FUNCTION
# ============================================================================
def generate_chat_title(user_message: str) -> str:
    """
    Kullanıcının ilk mesajından kısa bir başlık oluşturur.
    Gemini'yi kullanarak maksimum 5-6 kelimelik özet başlık üretir.
    """
    if gemini_model is None:
        # Model yoksa basit bir başlık oluştur
        return user_message[:30] + '...' if len(user_message) > 30 else user_message

    try:
        title_prompt = f"""
Aşağıdaki kullanıcı sorusundan, sohbet geçmişi için kısa ve öz bir başlık oluştur.

KURALLAR:
- Maksimum 5-6 kelime
- Türkçe
- Sorunun özünü yansıtmalı
- Başlık formatında (büyük harf başlangıç)
- Noktalama işareti yok

KULLANICI SORUSU:
{user_message}

Sadece başlığı yaz, başka bir şey yazma:"""

        response = gemini_model.generate_content(title_prompt)
        title = response.text.strip()

        # Başlığı temizle (gereksiz karakterleri kaldır)
        title = title.replace('"', '').replace("'", '').strip()

        # Eğer çok uzunsa kısalt
        if len(title) > 50:
            words = title.split()
            title = ' '.join(words[:6])

        print(f"✅ Başlık oluşturuldu: {title}")
        return title

    except Exception as e:
        print(f"⚠️ Başlık oluşturulurken hata: {e}, varsayılan başlık kullanılıyor")
        # Hata durumunda basit başlık
        return user_message[:30] + '...' if len(user_message) > 30 else user_message

# ============================================================================
# MAIN RESPONSE FUNCTION
# ============================================================================
def get_model_response(user_message, pdf_file_stream=None, session_id=None):
    """
    Ana RAG fonksiyonu - ChromaDB'den arama yapar ve Gemini ile yanıt üretir
    Conversation history tutar (session_id ile)
    """
    if gemini_model is None:
        return "Model düzgün yüklenemedi. Lütfen sunucu loglarına bakın."

    # Session ID yoksa veya geçersizse, conversation history olmadan çalış
    use_history = session_id and session_id != 'null'

    # PDF ile çalışma - RAG ile birleştirilmiş sistem
    if pdf_file_stream:
        pdf_context = _extract_text_from_pdf(pdf_file_stream)
        if pdf_context is None:
            return "Üzgünüm, yüklediğiniz PDF dosyasından metin çıkarılamadı. Lütfen dosyanın bozuk olmadığından veya şifre korumalı olmadığından emin olun ve tekrar deneyin."

        if not pdf_context.strip():
            return "Üzgünüm, yüklediğiniz PDF dosyasından metin çıkarılamadı. Dosya görüntü tabanlı (taranmış) bir PDF olabilir. Lütfen metin içeren bir PDF dosyası yükleyin."

        # PDF içeriğini session'da sakla (sonraki mesajlarda kullanmak için)
        if session_id and session_id != 'null':
            pdf_contexts[session_id] = pdf_context
            print(f"✅ PDF içeriği session {session_id} için kaydedildi ({len(pdf_context)} karakter)")

        # PDF yüklendiğinde de RAG kullan (hem PDF hem RAG bilgileri)
        if vector_store and vector_store.collection and user_message:
            # Hem PDF hem RAG kullan
            try:
                # 1. RAG'den arama yap
                search_results = vector_store.smart_search(query=user_message, n_results=5)

                # 2. Prompt oluştur (PDF içeriği ile birlikte)
                system_prompt, user_prompt, source_details = create_smart_prompt(
                    user_message,
                    search_results,
                    pdf_context=pdf_context
                )

                # 3. Gemini'ye gönder
                if use_history:
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    if session_id not in chat_sessions:
                        chat_sessions[session_id] = gemini_model.start_chat(history=[])
                    response = chat_sessions[session_id].send_message(full_prompt)
                else:
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = gemini_model.generate_content(full_prompt)

                # Kaynakları ekle (eğer zaten yazılmamışsa)
                response_text = response.text
                # Eğer cevap reddetme mesajı içeriyorsa kaynak ekleme
                rejection_keywords = ["bu konuda danışmanlık veremem", "sadece tüketici hukuku", "yardımcı olamam"]
                is_rejection = any(keyword in response_text.lower() for keyword in rejection_keywords)

                if is_rejection:
                    return response_text

                # Eğer cevapta zaten "KAYNAKLAR" veya "Kaynaklar" varsa tekrar ekleme
                if "KAYNAKLAR" not in response_text.upper() and "Kaynaklar" not in response_text and source_details:
                    # Kaynakları güzel bir formatta göster
                    sources_text = "\n\n---\n\n📚 Kaynaklar\n\n"
                    for source in source_details:
                        sources_text += f"• {source}\n"
                    return response_text + sources_text
                return response_text

            except Exception as e:
                print(f"⚠️ RAG ile PDF birleştirme hatası: {e}, sadece PDF ile devam ediliyor...")
                # Hata durumunda sadece PDF ile devam et

        # RAG yoksa veya hata varsa sadece PDF ile çalış
        final_prompt = f"""
Sen Türkiye'de çalışan bir avukatsın.

Aşağıdaki metni yalnızca hukuki dayanak olarak kullan.
Kullanıcıya avukat gibi, yol gösterici ve pratik cevap ver.

METİN:
{pdf_context}

SORU:
{user_message}
"""

        try:
            if use_history:
                # Chat session kullan (history ile)
                if session_id not in chat_sessions:
                    chat_sessions[session_id] = gemini_model.start_chat(history=[])
                response = chat_sessions[session_id].send_message(final_prompt)
            else:
                # Normal generate (history olmadan)
                response = gemini_model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            return f"Hata: {e}"

    # ChromaDB RAG ile çalışma (PDF yoksa veya PDF yüklendikten sonraki mesajlar)
    if vector_store and vector_store.collection:
        # Eğer bu session'da daha önce PDF yüklendiyse, onu da kullan
        session_pdf_context = None
        if session_id and session_id != 'null' and session_id in pdf_contexts:
            session_pdf_context = pdf_contexts[session_id]
            print(f"✅ Session {session_id} için kaydedilmiş PDF içeriği kullanılıyor")

        # 1. Semantic search yap
        search_results = vector_store.smart_search(query=user_message, n_results=5)

        if search_results['n_results'] == 0:
            # Eğer PDF içeriği varsa sadece PDF ile devam et
            if session_pdf_context:
                print("⚠️ RAG'de sonuç bulunamadı, sadece PDF içeriği ile devam ediliyor...")
                final_prompt = f"""
Sen Türkiye'de çalışan bir avukatsın.

Aşağıdaki metni yalnızca hukuki dayanak olarak kullan.
Kullanıcıya avukat gibi, yol gösterici ve pratik cevap ver.

METİN:
{session_pdf_context}

SORU:
{user_message}
"""
                try:
                    if use_history:
                        if session_id not in chat_sessions:
                            chat_sessions[session_id] = gemini_model.start_chat(history=[])
                        response = chat_sessions[session_id].send_message(final_prompt)
                    else:
                        response = gemini_model.generate_content(final_prompt)
                    return response.text
                except Exception as e:
                    return f"Hata: {e}"

            # RAG'de sonuç yoksa, tüketici hukuku dışı bir soru olabilir
            print("⚠️ RAG'de sonuç bulunamadı - tüketici hukuku dışı soru olabilir")
            rejection_prompt = f"""
Sen Türkiye'de aktif olarak çalışan bir avukatsın ve SADECE TÜKETİCİ HUKUKU konularında uzmanlaşmışsın.

Kullanıcının sorusu:
{user_message}

Bu soru tüketici hukuku dışında bir konuyla ilgili görünüyor. Kibarca ve nazikçe, sadece tüketici hukuku konularında (Tüketicinin Korunması Hakkında Kanun, mesafeli satış, ayıplı mal/hizmet, garanti, cayma hakkı, tüketici kredileri, konut finansmanı, taksitle satış, doğrudan satış, abonelik sözleşmeleri, paket tur, devre tatil, ön ödemeli konut, tüketici hakem heyetleri, haksız şartlar, reklam ve haksız ticari uygulamalar vb.) danışmanlık verebildiğini belirt.
Kısa ve samimi bir şekilde yaz.
"""
            try:
                if use_history:
                    if session_id not in chat_sessions:
                        chat_sessions[session_id] = gemini_model.start_chat(history=[])
                    response = chat_sessions[session_id].send_message(rejection_prompt)
                else:
                    response = gemini_model.generate_content(rejection_prompt)
                return response.text
            except Exception as e:
                return "Üzgünüm, bu konuda yeterli kaliteli kaynak bulunamadı. Sadece tüketici hukuku konularında yardımcı olabilirim."

        # Sonuçların kalitesini kontrol et - eğer tüm distance'lar çok yüksekse, tüketici hukuku dışı soru olabilir
        distances = search_results.get('distances', [])
        if distances and all(dist > 650.0 for dist in distances):
            print("⚠️ Tüm sonuçların distance'ı çok yüksek - tüketici hukuku dışı soru olabilir")
            rejection_prompt = f"""
Sen Türkiye'de aktif olarak çalışan bir avukatsın ve SADECE TÜKETİCİ HUKUKU konularında uzmanlaşmışsın.

Kullanıcının sorusu:
{user_message}

Bu soru tüketici hukuku dışında bir konuyla ilgili görünüyor. Kibarca ve nazikçe, sadece tüketici hukuku konularında (Tüketicinin Korunması Hakkında Kanun, mesafeli satış, ayıplı mal/hizmet, garanti, cayma hakkı, tüketici kredileri, konut finansmanı, taksitle satış, doğrudan satış, abonelik sözleşmeleri, paket tur, devre tatil, ön ödemeli konut, tüketici hakem heyetleri, haksız şartlar, reklam ve haksız ticari uygulamalar vb.) danışmanlık verebildiğini belirt.
Kısa ve samimi bir şekilde yaz.
"""
            try:
                if use_history:
                    if session_id not in chat_sessions:
                        chat_sessions[session_id] = gemini_model.start_chat(history=[])
                    response = chat_sessions[session_id].send_message(rejection_prompt)
                else:
                    response = gemini_model.generate_content(rejection_prompt)
                return response.text
            except Exception as e:
                return "Üzgünüm, bu konuda yeterli kaliteli kaynak bulunamadı. Sadece tüketici hukuku konularında yardımcı olabilirim."

        # 2. Prompt oluştur (PDF içeriği varsa onu da ekle)
        system_prompt, user_prompt, source_details = create_smart_prompt(
            user_message,
            search_results,
            pdf_context=session_pdf_context
        )

        # 3. Gemini'ye gönder
        try:
            if use_history:
                # Chat session kullan (history ile)
                # System instruction'ı chat session başlatırken veya her mesajda belirtebiliriz
                # Her mesajda farklı RAG sonuçları olduğu için, full prompt'u birleştirip gönderiyoruz
                full_prompt = f"{system_prompt}\n\n{user_prompt}"

                # Session yoksa oluştur
                if session_id not in chat_sessions:
                    chat_sessions[session_id] = gemini_model.start_chat(history=[])

                # Mesajı chat session'a gönder (history otomatik tutulur)
                response = chat_sessions[session_id].send_message(full_prompt)
            else:
                # History olmadan normal generate
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = gemini_model.generate_content(full_prompt)

            # Kaynakları ekle (eğer zaten yazılmamışsa)
            response_text = response.text
            # Eğer cevap reddetme mesajı içeriyorsa kaynak ekleme
            rejection_keywords = ["bu konuda danışmanlık veremem", "sadece tüketici hukuku", "yardımcı olamam"]
            is_rejection = any(keyword in response_text.lower() for keyword in rejection_keywords)

            if is_rejection:
                return response_text

            # Eğer cevapta zaten "KAYNAKLAR" veya "Kaynaklar" varsa tekrar ekleme
            if "KAYNAKLAR" not in response_text.upper() and "Kaynaklar" not in response_text and source_details:
                # Kaynakları güzel bir formatta göster
                sources_text = "\n\n---\n\n📚 Kaynaklar\n\n"
                for source in source_details:
                    sources_text += f"• {source}\n"
                return response_text + sources_text
            return response_text

        except Exception as e:
            return f"Model cevabı üretirken hata: {e}"

    # ChromaDB yoksa normal yanıt
    try:
        if use_history:
            # Chat session kullan (history ile)
            if session_id not in chat_sessions:
                chat_sessions[session_id] = gemini_model.start_chat(history=[])
            response = chat_sessions[session_id].send_message(user_message)
        else:
            # History olmadan normal generate
            response = gemini_model.generate_content(user_message)
        return response.text
    except Exception as e:
        return f"Hata: {e}"
