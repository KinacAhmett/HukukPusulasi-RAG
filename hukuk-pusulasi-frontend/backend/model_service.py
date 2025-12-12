#
# model_service.py - HUKUK PUSULASI RAG SİSTEMİ
#
import os
import torch
import numpy as np
from typing import List, Dict, Optional
from threading import Thread

# ChromaDB imports
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Sentence Transformers
from sentence_transformers import SentenceTransformer

# Transformers imports (Unsloth yerine)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# ChromaDB ayarları
CHROMADB_PERSIST_DIR = os.getenv("CHROMADB_DIR", "./legal_chroma_db")
CHROMADB_COLLECTION_NAME = "legal_documents_v2"
EMBEDDING_MODEL_NAME = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"

# LLM model ayarları
HF_MODEL_ID = "beyzasn/hukuk-pusulasi-llm-v1-MERGED"
MAX_SEQ_LENGTH = 8192
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Global değişkenler
llm_model = None
llm_tokenizer = None
vector_store = None

# ==============================================================================
# ✅ DISTANCE ANALYZER (Notebook'tan)
# ==============================================================================

class DistanceAnalyzer:
    """ChromaDB L2 distance için optimize edilmiş threshold analizi"""

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

        docs = results['documents']
        metas = results['metadatas']
        dists = results['distances']

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

# ==============================================================================
# SEMANTIC QUERY PROCESSOR (Notebook'tan)
# ==============================================================================

class SemanticQueryProcessor:
    """Semantic similarity ile query processing"""

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
            ],
            'konut': [
                "ev aldım",
                "daire satın aldım",
                "ön ödemeli konut",
                "konut finansmanı"
            ]
        }

        self.legal_embeddings = self._prepare_concept_embeddings(self.legal_concept_examples)
        self.contract_embeddings = self._prepare_concept_embeddings(self.contract_type_examples)

    def _prepare_concept_embeddings(self, examples_dict: Dict) -> Dict:
        result = {}
        for concept, examples in examples_dict.items():
            embeddings = self.embedder.encode(examples, convert_to_tensor=False)
            result[concept] = np.mean(embeddings, axis=0)
        return result

    def _semantic_similarity(self, query: str, concept_embeddings: Dict, threshold: float = 0.5) -> List[tuple]:
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
                'taksitli': 'taksitle satış kredi',
                'konut': 'ön ödemeli konut finansmanı'
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
            elif contract_type == 'konut':
                metadata_filters = {"file_name": {"$eq": "Regulation_KONUT_FINANSMANI_SOZLESMELERI_YONETMELIGI.pdf"}}
            elif contract_type == 'kapidan':
                metadata_filters = {"file_name": {"$eq": "Regulation_DOGRUDAN_SATISLAR_HAKKINDA_YONETMELIK.pdf"}}

        return {
            'original': query,
            'enriched': ' '.join(filter(None, enriched_parts)),
            'contract_type': contract_type,
            'legal_concepts': [c for c, s in legal_concepts],
            'concept_scores': legal_concepts,
            'metadata_filters': metadata_filters,
        }

# ==============================================================================
# ADAPTIVE SEARCH STRATEGY (Notebook'tan)
# ==============================================================================

class AdaptiveSearchStrategy:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def determine_search_strategy(self, query_analysis: Dict) -> Dict:
        has_strong_concept = any(score > 0.6 for _, score in query_analysis.get('concept_scores', []))
        has_clear_contract = query_analysis.get('contract_type') is not None

        strategy = {
            'semantic_weight': 0.5,
            'filtered_weight': 0.3,
            'hybrid_weight': 0.2,
            'n_results_semantic': 10,
            'n_results_filtered': 5,
            'quality_threshold': 'good'
        }

        if has_strong_concept and has_clear_contract:
            strategy.update({
                'semantic_weight': 0.4,
                'filtered_weight': 0.5,
                'n_results_semantic': 8,
                'n_results_filtered': 7,
            })
        elif has_strong_concept:
            strategy.update({
                'semantic_weight': 0.7,
                'filtered_weight': 0.1,
                'n_results_semantic': 15,
                'quality_threshold': 'acceptable'
            })
        elif has_clear_contract:
            strategy.update({
                'semantic_weight': 0.3,
                'filtered_weight': 0.6,
                'n_results_filtered': 10,
            })
        else:
            strategy.update({
                'semantic_weight': 0.6,
                'n_results_semantic': 20,
                'quality_threshold': 'acceptable'
            })

        return strategy

# ==============================================================================
# SMART VECTOR STORE (Notebook'tan)
# ==============================================================================

class SmartVectorStore:
    def __init__(self, persist_dir: str, collection_name: str, model_name: str):
        self.persist_directory = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name, device=DEVICE
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
        self.search_strategy = AdaptiveSearchStrategy(self)
        self.distance_analyzer = DistanceAnalyzer()

    def smart_search(self, query: str, n_results: int = 5) -> Dict:
        analysis = self.semantic_processor.enrich_query(query)

        print(f"\n🔍 Sorgu: '{query}'")
        print(f"📊 Semantic Analiz:")
        print(f"   • Sözleşme tipi: {analysis['contract_type'] or 'Belirsiz'}")
        print(f"   • Yasal konseptler: {[f'{c} ({s:.2f})' for c, s in analysis.get('concept_scores', [])]}")

        strategy = self.search_strategy.determine_search_strategy(analysis)
        all_results = []

        # Filtered search
        if analysis['metadata_filters']:
            try:
                filtered = self.collection.query(
                    query_texts=[analysis['enriched']],
                    n_results=strategy['n_results_filtered'],
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
                            'distance': dist,
                            'strategy': 'filtered',
                            'score': dist * (1 - strategy['filtered_weight'])
                        })
            except Exception as e:
                print(f"⚠️ Filtre hatası: {e}")

        # Semantic search
        semantic = self.collection.query(
            query_texts=[analysis['enriched']],
            n_results=strategy['n_results_semantic'],
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
                'distance': dist,
                'strategy': 'semantic',
                'score': dist * (1 - strategy['semantic_weight'])
            })

        # Deduplicate & sort
        seen_ids = set()
        unique_results = []

        for r in sorted(all_results, key=lambda x: x['score']):
            doc_hash = hash(r['document'][:100])
            if doc_hash not in seen_ids:
                seen_ids.add(doc_hash)
                unique_results.append(r)

        # Filter by quality
        final_results = self.distance_analyzer.filter_by_quality(
            {
                'documents': [r['document'] for r in unique_results],
                'metadatas': [r['metadata'] for r in unique_results],
                'distances': [r['distance'] for r in unique_results],
            },
            quality_level=strategy['quality_threshold']
        )

        print(f"\n✅ Toplam {final_results['n_results']} kaliteli sonuç")

        return {
            'query': query,
            'n_results': min(final_results['n_results'], n_results),
            'documents': final_results['documents'][:n_results],
            'metadatas': final_results['metadatas'][:n_results],
            'distances': final_results['distances'][:n_results],
            'analysis': analysis
        }

# ==============================================================================
# PROMPT ENGINEERING (Notebook'tan optimize edilmiş)
# ==============================================================================

def format_source(doc: str, meta: Dict) -> str:
    """Kaynak bilgisini akıllıca çıkarır"""
    doc_type = meta.get('doc_type', '')
    content_lines = doc.strip().split('\n')

    if doc_type == 'court_decision':
        for line in content_lines[:3]:
            if line.startswith('T.C.'):
                mahkeme_adi = line.replace('T.C.', '').strip()
                return mahkeme_adi

    elif doc_type in ['regulation', 'law']:
        if content_lines:
            baslik = content_lines[0].strip()
            article_num = meta.get('article_number')
            if article_num:
                return f"{baslik} - Madde {article_num}"
            return baslik

    file_name = meta.get('file_name', 'Kaynak')
    return file_name.replace('.pdf', '').replace('_', ' ')

def create_smart_prompt(query: str, search_results: Dict) -> tuple:
    """Semantic analiz sonuçlarına göre optimized prompt"""
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

    system_prompt = f"""Sen Türk Tüketici Hukuku uzmanısın.

KURALLAR:
1. SADECE verilen kaynaklardaki bilgileri kullan
2. Net, anlaşılır ve yapılandırılmış yanıt ver
3. İlk cümlede soruya doğrudan yanıt ver
4. Kaynak numaralarını belirt (örn: [Kaynak 1])
5. Yasal dayanakları (madde numarası) belirt
6. Pratik öneriler ver{contract_guidance}

FORMAT:
• Ana yanıt (2-3 cümle)
• Yasal dayanak (1 cümle)
• Pratik öneri (1 cümle - varsa)
"""

    user_prompt = f"""KAYNAKLAR:

{context_block}

SORU: {query}

Yukarıdaki kaynaklara göre yanıt ver."""

    return system_prompt, user_prompt, source_details

# ==============================================================================
# MODEL INITIALIZATION
# ==============================================================================

def initialize_model():
    """Tüm sistem bileşenlerini yükler"""
    global llm_model, llm_tokenizer, vector_store

    try:
        print("\n" + "="*60)
        print("🚀 HUKUK PUSULASI RAG SİSTEMİ BAŞLATILIYOR")
        print("="*60)

        # 1. LLM Yükleme (Normal Transformers ile)
        print(f"\n📄 LLM yükleniyor: {HF_MODEL_ID}...")

        # Mac için: CPU veya MPS (Metal Performance Shaders)
        if torch.backends.mps.is_available():
            device = "mps"  # Mac M1/M2/M3 için
            print("🍎 Apple Silicon GPU (MPS) kullanılıyor")
        elif torch.cuda.is_available():
            device = "cuda"
            print("🎮 NVIDIA GPU kullanılıyor")
        else:
            device = "cpu"
            print("💻 CPU kullanılıyor (yavaş olabilir)")

        # Quantization config (bellek tasarrufu için)
        quantization_config = None

        # SADECE ve SADECE CUDA kullanılıyorsa 4-bit nicelemeyi etkinleştir.
        if device == "cuda":
            print("🚀 CUDA algılandı, 4-bit niceleme kullanılıyor.")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        else:
            # MPS veya CPU için nicelemeyi devre dışı bırak.
            print(f"⚠️ {device.upper()} kullanılıyor, 4-bit niceleme devre dışı bırakıldı.")

        # Tokenizer yükle
        llm_tokenizer = AutoTokenizer.from_pretrained(
            HF_MODEL_ID,
            trust_remote_code=True
        )

        # Ortak parametreleri hazırla
        model_kwargs = {
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
            # MPS'de float16 desteklenir, CPU'da float32 daha güvenlidir.
            "torch_dtype": torch.float16 if device in ["cuda", "mps"] else torch.float32,
        }

        # device_map ekle (Sadece CUDA'da 4-bit ile kullanılması önerilir)
        if device == "cuda":
            model_kwargs["device_map"] = "auto"

        # quantization_config ekle (Sadece None değilse, yani CUDA ise ekle)
        if quantization_config is not None:
            model_kwargs["quantization_config"] = quantization_config

        # Model yükle (Hata veren satır)
        llm_model = AutoModelForCausalLM.from_pretrained(
            HF_MODEL_ID,
            **model_kwargs
        )

        # Mac için modeli MPS'ye taşı (Niceleme yoksa bu gereklidir)
        if device == "mps" and llm_model is not None:
            llm_model = llm_model.to(device)

        llm_model.eval()  # Inference mode
        print("✅ LLM başarıyla yüklendi!")

        # 2. Vector Store Yükleme
        print(f"\n📚 Vector store yükleniyor: {CHROMADB_PERSIST_DIR}...")
        vector_store = SmartVectorStore(
            CHROMADB_PERSIST_DIR,
            CHROMADB_COLLECTION_NAME,
            EMBEDDING_MODEL_NAME
        )
        print("✅ Vector store başarıyla yüklendi!")

        print(f"\n✅ SİSTEM HAZIR! (Device: {device})\n")
        return True

    except Exception as e:
        print(f"❌ Model yükleme hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==============================================================================
# MAIN RESPONSE FUNCTION
# ==============================================================================

def get_model_response(user_message: str, pdf_file_stream=None) -> str:
    """
    Ana RAG fonksiyonu - kullanıcı mesajını işler ve yanıt üretir
    """
    if llm_model is None or vector_store is None:
        return "❌ Model düzgün yüklenemedi. Lütfen sunucu loglarına bakın."

    try:
        # 1. Smart Search (RAG)
        search_results = vector_store.smart_search(query=user_message, n_results=5)

        if search_results['n_results'] == 0:
            return "Üzgünüm, bu konuda yeterli kaliteli kaynak bulunamadı. Sorunuzu farklı kelimelerle tekrar sorabilir misiniz?"

        # 2. Smart Prompt Oluştur
        system_prompt, user_prompt, source_details = create_smart_prompt(user_message, search_results)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 3. LLM'den Yanıt Al
        # Chat template uygula
        if hasattr(llm_tokenizer, 'apply_chat_template'):
            input_text = llm_tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # Fallback: Manuel format
            input_text = f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:"

        # Tokenize
        inputs = llm_tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_SEQ_LENGTH
        )

        # Device'a taşı
        device = llm_model.device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = llm_model.generate(
                **inputs,
                max_new_tokens=500,
                temperature=0.4,
                top_p=0.9,
                repetition_penalty=1.15,
                do_sample=True,
                pad_token_id=llm_tokenizer.eos_token_id,
            )

        # Decode
        response = llm_tokenizer.decode(
            outputs[0][len(inputs['input_ids'][0]):],
            skip_special_tokens=True
        )

        # 4. Kaynakları Ekle
        if source_details:
            source_block = "\n\n" + "─"*50 + "\n📚 **Kaynaklar:**\n" + "\n".join([f"• {s}" for s in source_details])
            response += source_block

        return response.strip()

    except Exception as e:
        print(f"❌ Model cevabı üretirken hata: {e}")
        import traceback
        traceback.print_exc()
        return f"Üzgünüm, yanıt üretirken bir hata oluştu: {e}"
