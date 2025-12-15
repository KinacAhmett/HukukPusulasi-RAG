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

    # PersistentClient kullan (Client deprecated)
    client = chromadb.PersistentClient(
        path="./legal_chroma_db",
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=False
        )
    )

    # ✅ Collection adını "legal_documents_v2" olarak değiştir
    try:
        vector_store = client.get_collection("legal_documents_v2")
        print(f"✅ Vector store hazır ({vector_store.count()} doküman)")
    except Exception as e:
        print(f"❌ Collection bulunamadı: {e}")
        # Alternatif: v1'i dene
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
    if model is None or tokenizer is None or vector_store is None:
        return "❌ Sistem henüz hazır değil"

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

    prompt = f"""
Aşağıdaki hukuki metne dayanarak soruyu yanıtla.

METİN:
{context}

SORU:
{query}

CEVAP:
"""

    # Her zaman cpu kullanılacak
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to("cpu") for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7
        )

    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return answer.split("CEVAP:")[-1].strip()
