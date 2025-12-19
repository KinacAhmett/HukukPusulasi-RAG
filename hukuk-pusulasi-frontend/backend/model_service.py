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
    file_name = meta.get('file_name', 'Kaynak')
    
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
def create_smart_prompt(query: str, search_results: Dict) -> tuple:
    """RAG için akıllı prompt oluşturur"""
    analysis = search_results.get('analysis', {})

    contexts = []
    source_details = []

    for i, (doc, meta) in enumerate(zip(
        search_results['documents'],
        search_results['metadatas']
    )):
        source_info = format_source(doc, meta)
        doc_text = doc.strip()[:600] + "..." if len(doc.strip()) > 600 else doc.strip()
        contexts.append(f"[Kaynak {i+1}]:\n{doc_text}")
        source_details.append(f"[{i+1}] {source_info}")

    context_block = "\n\n".join(contexts)

    contract_guidance = ""
    if analysis.get('contract_type') == 'mesafeli':
        contract_guidance = "\n• Bu mesafeli sözleşme sorusu - cayma hakkı ve iade süreçlerine odaklan"
    elif 'ayipli_mal' in analysis.get('legal_concepts', []):
        contract_guidance = "\n• Bu ayıplı mal sorusu - tüketici haklarını ve çözüm yollarını açıkla"

    system_prompt = f"""
Sen Türkiye'de aktif olarak çalışan bir avukatsın.

ROLÜN:
Kullanıcılara hukuki danışmanlık verir gibi,
uygulamaya dönük, pratik ve yol gösterici cevaplar verirsin.

KURALLAR:
- Akademik veya tez dili kullanma
- "verilen kaynaklara göre", "dokümanlar şunu söylüyor" gibi ifadeler kullanma
- Kaynak numarası, belge adı veya PDF referansı belirtme
- Bilgiyi içselleştirerek anlat

CEVAP TARZI:
- Net
- Resmi ama insani
- Gereksiz empati yok, samimi giriş var
- Avukat refleksiyle yönlendirici

ZORUNLU CEVAP YAPISI:
1. Kısa bir geçmiş olsun / durum özeti
2. Kullanıcının hangi hakları olduğu
3. Adım adım ne yapması gerektiği
4. Alternatif yollar (dava, tahkim, başvuru)
5. Pratik uyarılar (sık yapılan hatalar)
6. Kaynakları belirtmek

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

SORU:
{query}
"""

    user_prompt += """

Cevabını aşağıdaki şablona uygun yaz:

Geçmiş olsun.

[Durumun kısa özeti]

**ÇOK ÖNEMLİ:** 
Cevabında her hukuki bilgi, süre, hak veya yükümlülükten bahsettiğinde,
hemen arkasına [1], [2], [3] gibi kaynak numarası koy.

Örnek:
"Cayma hakkı 14 gün içinde kullanılabilir [1]. Bu süre içinde..."
"Mesafeli sözleşmelerde iade ücretsizdir [2]."

Cevabını şablona uygun yaz , kaynak kullandığın bir kısımda [kaynaklı] yaz:
1. Haklarınız [kaynaklı]
2. Yapılması gerekenler [kaynaklı]
3. Süreç nasıl ilerler [kaynaklı]
4. Alternatif yollar [kaynaklı]
5. Pratik öneriler [kaynaklı]
6. Kaynakları belirtmek [kaynaklı]
"""

    return system_prompt, user_prompt, source_details

# ============================================================================
# MAIN RESPONSE FUNCTION
# ============================================================================
def get_model_response(user_message, pdf_file_stream=None):
    """
    Ana RAG fonksiyonu - ChromaDB'den arama yapar ve Gemini ile yanıt üretir
    """
    if gemini_model is None:
        return "Model düzgün yüklenemedi. Lütfen sunucu loglarına bakın."

    # PDF ile çalışma (eski sistem)
    if pdf_file_stream:
        pdf_context = _extract_text_from_pdf(pdf_file_stream)
        if pdf_context:
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
                response = gemini_model.generate_content(final_prompt)
                return response.text
            except Exception as e:
                return f"Hata: {e}"

    # ChromaDB RAG ile çalışma (YENİ SİSTEM)
    if vector_store and vector_store.collection:
        # 1. Semantic search yap
        search_results = vector_store.smart_search(query=user_message, n_results=5)
        
        if search_results['n_results'] == 0:
            return "Üzgünüm, bu konuda yeterli kaliteli kaynak bulunamadı."

        # 2. Prompt oluştur
        system_prompt, user_prompt, source_details = create_smart_prompt(user_message, search_results)

        # 3. Gemini'ye gönder
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = gemini_model.generate_content(full_prompt)
            
            # Kaynakları ekle
            response_text = response.text
            sources_text = "\n\n**KAYNAKLAR:**\n" + "\n".join(source_details)
            
            return response_text + sources_text

        except Exception as e:
            return f"Model cevabı üretirken hata: {e}"

    # ChromaDB yoksa normal yanıt
    try:
        response = gemini_model.generate_content(user_message)
        return response.text
    except Exception as e:
        return f"Hata: {e}"