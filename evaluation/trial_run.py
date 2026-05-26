"""
Ragas v0.4 — Hukuk Pusulası RAG Evaluation (PRODUCTION)
========================================================
✅ Aynı 30 soru, 7 model = 210 satır (fair karşılaştırma)
✅ Llama 3.1 8B judge
✅ 6 metrik (LLM-judge + embedding) — TÜM modeller için
✅ Resume desteği
✅ Periyodik mola (her 10 satırda)

Gerekli:
  ollama serve
  ollama pull llama3.1:latest
  ollama pull nomic-embed-text

Çalıştırma:
  python trial_run.py
"""
import pandas as pd
import ast
import os
import time
import warnings
import logging
from dotenv import load_dotenv

logging.getLogger("ragas").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

load_dotenv()

# =====================================================================
# Imports
# =====================================================================
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from ragas import evaluate, EvaluationDataset
from ragas.metrics import (
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    Faithfulness,
    ResponseRelevancy,
    SemanticSimilarity,
    FactualCorrectness,
)
from ragas.run_config import RunConfig

# =====================================================================
# AYARLAR
# =====================================================================
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_LLM_MODEL = "llama3.1:latest"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
CSV_PATH = "master_benchmark_results_with_contexts.csv"
OUTPUT_PATH = "ragas_results.csv"

# 🎯 SAMPLING - İLK N SORU (rastgele değil, sırayla)
NUM_QUESTIONS_START = 150
NUM_QUESTIONS_END = 200
CONTEXT_MAX_CHARS = 2000

# Parallel & retry
MAX_WORKERS = 1
TIMEOUT = 600
MAX_RETRY = 3
SATIR_ARASI_BEKLEME = 2

# 🛌 MOLA SİSTEMİ
COOL_DOWN_EVERY = 10
COOL_DOWN_SECONDS = 60

# =====================================================================
# Ollama Setup
# =====================================================================
print(f"🔧 Setup başlatılıyor...")
print(f"   LLM: {OLLAMA_LLM_MODEL}")
print(f"   Embedding: {OLLAMA_EMBED_MODEL}")
print(f"   Max Workers: {MAX_WORKERS}")
print(f"   🛌 Mola: Her {COOL_DOWN_EVERY} satırda {COOL_DOWN_SECONDS}s")
print()

try:
    llm = OllamaLLM(
        model=OLLAMA_LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.0,
        num_ctx=8192,
    )
    
    embeddings = OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    
    print("  Ollama test çağrısı...")
    test = llm.invoke("Merhaba")
    print(f"  ✅ Ollama OK: '{test[:50]}...'")
    print()
except Exception as e:
    print(f"❌ HATA: {e}")
    exit(1)

judge_llm = LangchainLLMWrapper(llm)
judge_embeddings = LangchainEmbeddingsWrapper(embeddings)

# =====================================================================
# Metrikler — 6 METRIK (TÜM modeller için, hep birlikte hesaplanır)
# =====================================================================
metrics = [
    LLMContextPrecisionWithReference(llm=judge_llm),
    LLMContextRecall(llm=judge_llm),
    Faithfulness(llm=judge_llm),
    ResponseRelevancy(llm=judge_llm, embeddings=judge_embeddings),
    SemanticSimilarity(embeddings=judge_embeddings),
    FactualCorrectness(llm=judge_llm, mode="f1", atomicity="high", coverage="high"),
]

run_config = RunConfig(
    timeout=TIMEOUT,
    max_workers=MAX_WORKERS,
    max_retries=2,
    max_wait=60,
)

# =====================================================================
# Veri + Sampling
# =====================================================================
def trim_contexts(contexts, max_chars=CONTEXT_MAX_CHARS):
    if isinstance(contexts, str):
        contexts = ast.literal_eval(contexts)
    return [ctx[:max_chars] + "..." if len(ctx) > max_chars else ctx for ctx in contexts]


print(f"📂 CSV: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)
df["contexts"] = df["retrieved_contexts"].apply(lambda x: trim_contexts(x))
print(f"   Toplam: {len(df)} satır ({df['model_name'].nunique()} model)")

# 🎯 İLK N SORU (rastgele DEĞİL, CSV'deki sırasıyla)
all_questions = df['question'].unique().tolist()
end_idx = min(NUM_QUESTIONS_END, len(all_questions))
selected_questions = all_questions[NUM_QUESTIONS_START:end_idx]
num_selected = len(selected_questions)

print(f"\n🎯 Sampling:")
print(f"   Strateji: CSV'deki SIRAYLA ilk {num_selected} soru (rastgele değil)")
print(f"   Aşama: {NUM_QUESTIONS_START}-{end_idx}")

df_sample = df[df['question'].isin(selected_questions)].copy()

# 🎯 SIRALAMA: Önce model bazlı, sonra soru sırasına göre
question_order = {q: idx for idx, q in enumerate(selected_questions)}
df_sample['_q_order'] = df_sample['question'].map(question_order)

# Model alfabetik, her model içinde Q1→Q30
df_sample = df_sample.sort_values(['model_name', '_q_order']).drop('_q_order', axis=1).reset_index(drop=True)

print(f"   Toplam: {len(df_sample)} satır işlenecek")
print(f"   🎯 Sıralama: Model bazlı")
print(f"      → DeepSeek-R1-7B Q1→Q30 (1-30)")
print(f"      → Gemini-3.1-Flash-Lite Q1→Q30 (31-60)")
print(f"      → ... (toplam 7 model)")

print(f"\n📋 Model dağılımı:")
for model, count in df_sample.groupby('model_name', sort=False).size().items():
    print(f"   {model:25s}: {count}")
print()

# Soru numaralandırma
question_to_idx = {q: idx+1 for idx, q in enumerate(selected_questions)}
print(f"📝 Soru numaralandırma: Q1 → Q{len(selected_questions)}")

# =====================================================================
# Resume
# =====================================================================
already_processed = 0
processed_keys = set()

if os.path.exists(OUTPUT_PATH):
    try:
        existing_df = pd.read_csv(OUTPUT_PATH)
        already_processed = len(existing_df)
        if 'model_name' in existing_df.columns and 'user_input' in existing_df.columns:
            processed_keys = set(zip(existing_df['model_name'], existing_df['user_input']))
        print(f"♻️ Resume: {already_processed} satır işlenmiş, {len(processed_keys)} atlanacak.")
    except Exception as e:
        print(f"⚠️ Resume hatası: {e}")

# =====================================================================
# WHILE DÖNGÜSÜ
# =====================================================================
print(f"\n🚀 Başlatılıyor...")
print(f"   Tahmini süre: ~{len(df_sample) * 130 / 60:.0f} dakika ({len(df_sample) * 130 / 3600:.1f} saat)")
print()

global_start = time.time()
toplam_satir = len(df_sample)
basarili_satir = 0
basarisiz_satir = 0
atlanan_satir = 0
yeni_islem_sayisi = 0

i = 0
while i < toplam_satir:
    row = df_sample.iloc[i]
    
    # Resume kontrolü
    key = (row['model_name'], row['user_input'] if 'user_input' in row else row['question'])
    if key in processed_keys:
        atlanan_satir += 1
        if atlanan_satir % 10 == 0 or atlanan_satir == 1:
            print(f"   ⏩ {atlanan_satir} satır atlandı (önceden işlenmiş)")
        i += 1
        continue
    
    # İlk YENİ işlemde başlangıç mesajı
    if basarili_satir == 0 and atlanan_satir > 0:
        print(f"\n✅ {atlanan_satir} satır atlandı, şimdi yeniden başlıyor:")
        print(f"   ↪ {row['model_name']} | Q{question_to_idx.get(row['question'], '?')} ile devam\n")
    
    # 🛌 MOLA (her 10 satırda)
    if yeni_islem_sayisi > 0 and yeni_islem_sayisi % COOL_DOWN_EVERY == 0:
        print(f"\n  🛌 MOLA: {COOL_DOWN_SECONDS}s dinleniyor...")
        time.sleep(COOL_DOWN_SECONDS)
        print(f"  ✅ Devam.\n")
    
    row_start = time.time()
    progress = f"[{i+1}/{toplam_satir}]"
    q_idx = question_to_idx.get(row['question'], '?')
    print(f"⏳ {progress} Q{q_idx:2d} | {row['model_name']:25s} | {str(row['question'])[:50]}...")
    
    # Dataset
    eval_samples = [{
        "user_input": str(row["question"]),
        "retrieved_contexts": list(row["contexts"]),
        "response": str(row["model_output"]),
        "reference": str(row["ground_truth"]),
    }]
    eval_dataset = EvaluationDataset.from_list(eval_samples)
    
    success = False
    retry_count = 0
    
    while retry_count < MAX_RETRY and not success:
        try:
            results = evaluate(
                dataset=eval_dataset,
                metrics=metrics,
                llm=judge_llm,
                embeddings=judge_embeddings,
                run_config=run_config,
                raise_exceptions=False,
                show_progress=False,
            )
            
            res_df = results.to_pandas()
            res_df.insert(0, "question_idx", q_idx)
            res_df.insert(1, "model_name", row["model_name"])
            res_df.insert(2, "question_short", str(row["question"])[:100])
            res_df["latency_seconds"] = row.get("latency_seconds", None)
            res_df["avg_distance"] = row.get("avg_distance", None)
            res_df["question_type"] = row.get("question_type", None)
            res_df["source_article"] = row.get("source_article", None)
            
            file_exists = os.path.exists(OUTPUT_PATH)
            res_df.to_csv(OUTPUT_PATH, mode="a", index=False, header=not file_exists, encoding="utf-8-sig")
            
            elapsed = time.time() - row_start
            metric_cols = [c for c in res_df.columns if any(m in c.lower() for m in 
                          ["precision", "recall", "faithfulness", "relevancy"])]
            scores_str = " | ".join([f"{c[:6]}={res_df[c].iloc[0]:.2f}" for c in metric_cols[:4] if pd.notna(res_df[c].iloc[0])])
            
            print(f"   ✅ {elapsed:.0f}s | {scores_str}")
            success = True
            basarili_satir += 1
            yeni_islem_sayisi += 1
            
        except Exception as e:
            err_str = str(e)
            retry_count += 1
            print(f"   ⚠️ Hata (deneme {retry_count}/{MAX_RETRY}): {err_str[:80]}")
            if retry_count < MAX_RETRY:
                time.sleep(10)
            else:
                print(f"   ❌ Atlandı.")
                basarisiz_satir += 1
                break
    
    i += 1
    
    # Periyodik özet
    if yeni_islem_sayisi > 0 and yeni_islem_sayisi % 10 == 0:
        elapsed_min = (time.time() - global_start) / 60
        avg = (time.time() - global_start) / max(basarili_satir, 1)
        kalan = (toplam_satir - i) * avg / 60
        print(f"\n  📊 {i}/{toplam_satir} | Geçen: {elapsed_min:.1f}dk | Kalan: ~{kalan:.0f}dk\n")
    
    # Satır arası bekleme
    if SATIR_ARASI_BEKLEME > 0 and i < toplam_satir:
        time.sleep(SATIR_ARASI_BEKLEME)

# =====================================================================
# ÖZET
# =====================================================================
total_elapsed = time.time() - global_start

print(f"\n{'='*70}")
print(f"🏁 TAMAMLANDI")
print(f"{'='*70}")
print(f"  Süre: {total_elapsed:.0f}s ({total_elapsed/60:.1f}dk, {total_elapsed/3600:.2f}sa)")
print(f"  Başarılı: {basarili_satir} | Başarısız: {basarisiz_satir} | Atlanan: {atlanan_satir}")
print(f"  Çıktı: {OUTPUT_PATH}")

if os.path.exists(OUTPUT_PATH):
    final_df = pd.read_csv(OUTPUT_PATH)
    metric_cols = [c for c in final_df.columns if any(m in c.lower() for m in 
                   ["precision", "recall", "faithfulness", "relevancy", "similarity", "correctness"])]
    
    if metric_cols:
        print(f"\n📊 Model bazında ortalamalar:")
        summary = final_df.groupby('model_name')[metric_cols].mean().round(3)
        print(summary.to_string())
        summary.to_csv("model_summary.csv", encoding="utf-8-sig")
        print(f"\n💾 Özet: model_summary.csv")

print(f"{'='*70}")