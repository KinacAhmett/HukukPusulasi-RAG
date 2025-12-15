from fastapi import FastAPI
from pydantic import BaseModel

from rag_engine import (
    load_llm,
    load_vector_store,
    generate_answer
)

app = FastAPI()

# =========================
# STARTUP
# =========================
print("🚀 Sistem başlatılıyor...")

load_llm("beyzasn/hukuk-pusulasi-llm-v1-MERGED")
load_vector_store()

print("✅ Sistem tamamen hazır")

# =========================
# API SCHEMA
# =========================
class ChatRequest(BaseModel):
    message: str

# =========================
# ENDPOINT
# =========================
@app.post("/chat")
def chat(req: ChatRequest):
    print("📩 Soru geldi:", req.message)

    try:
        answer = generate_answer(req.message)  # RAG + LLM fonksiyonun
        print("✅ Cevap üretildi")

        return {
            "answer": answer
        }

    except Exception as e:
        print("❌ Hata:", e)
        return {
            "error": str(e)
        }
