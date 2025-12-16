import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# =========================
# GLOBAL STATE
# =========================
model = None
tokenizer = None
vector_store = None
embedder = None

# =========================
# MODEL YÜKLE
# =========================
def load_llm(model_id: str):
    global model, tokenizer

    print(f"📄 LLM yükleniyor: {model_id}")

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Padding token ekle (yoksa)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        device_map={"": "cpu"},
        low_cpu_mem_usage=True
    )

    model.eval()
    print("✅ LLM yüklendi")

# =========================
# VECTOR STORE YÜKLE
# =========================
def load_vector_store():
    global vector_store, embedder

    print("📚 Vector store yükleniyor...")

    embedder = SentenceTransformer(
        "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"
    )

    client = chromadb.PersistentClient(
        path="./legal_chroma_db",
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=False
        )
    )

    try:
        vector_store = client.get_collection("legal_documents_v2")
        print(f"✅ Vector store hazır ({vector_store.count()} doküman)")
    except Exception as e:
        print(f"⚠ Collection bulunamadı: {e}")
        try:
            vector_store = client.get_collection("legal_documents_v1")
            print(f"✅ Vector store hazır (v1 kullanıldı, {vector_store.count()} doküman)")
        except:
            print("❌ Hiçbir collection bulunamadı!")
            print("📋 Mevcut collections:")
            for col in client.list_collections():
                print(f"   • {col.name}")
            raise

# =========================
# CEVAP ÜRET
# =========================
def generate_answer(query: str) -> str:
    try:
        if model is None or tokenizer is None or vector_store is None:
            return "❌ Sistem henüz hazır değil"

        print(f"🔍 Soru işleniyor: {query[:50]}...")

        # --- Vector search ---
        query_embedding = embedder.encode(query).tolist()

        results = vector_store.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        # Sonuç kontrolü
        if not results["documents"] or not results["documents"][0]:
            return "❌ İlgili doküman bulunamadı"

        context = "\n".join(results["documents"][0])
        print(f"📄 {len(results['documents'][0])} doküman bulundu")

        # Daha kısa ve net prompt
        prompt = f"""Aşağıdaki hukuki bilgiye göre soruyu yanıtla.

BİLGİ:
{context[:1000]}

SORU: {query}

CEVAP:"""

        print("💭 LLM'e gönderiliyor...")

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=384   # ⬅ düşürüldü
        )

        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=64,        # ⬅ düşürüldü
                do_sample=False,          # ⬅ KRİTİK
                num_beams=1,              # ⬅ greedy
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Sadece cevap kısmını al
        if "CEVAP:" in full_text:
            answer = full_text.split("CEVAP:")[-1].strip()
        else:
            answer = full_text.strip()

        print(f"✅ Cevap hazır: {len(answer)} karakter")
        return answer

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Hata: {str(e)}"
