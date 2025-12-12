#
# app.py - HUKUK PUSULASI FLASK API
#
import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Servislerimizi import et
import model_service
import database

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# --- FLASK UYGULAMASI ---
app = Flask(__name__)
CORS(app)

# --- SERVİSLERİ BAŞLAT ---
print("\n🚀 Flask sunucusu başlatılıyor...")

# Model ve vector store'u yükle (bu biraz zaman alabilir)
is_model_ready = model_service.initialize_model()

# Veritabanını başlat
database.init_db()

if not is_model_ready:
    print("\n⚠️ UYARI: Model yüklenemedi! API çalışmayacak.")
else:
    print("\n✅ Tüm servisler başarıyla yüklendi!")

# --- API ENDPOINT'LERİ ---

@app.route('/api/health', methods=['GET'])
def health_check():
    """Sunucunun durumunu kontrol et"""
    if is_model_ready:
        return jsonify({
            "status": "healthy",
            "model": "loaded",
            "rag": "active"
        }), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "reason": "Model yüklenemedi"
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Tüm sohbet oturumlarını getir (sidebar için)"""
    try:
        sessions_raw = database.get_all_sessions()
        sessions_list = []

        for row in sessions_raw:
            session_id, first_message, last_message_time = row

            # Frontend'in beklediği format
            title = first_message[:30] + '...' if len(first_message) > 30 else first_message

            sessions_list.append({
                "id": session_id,
                "title": title,
                "lastMessage": last_message_time
            })

        return jsonify({"sessions": sessions_list})

    except Exception as e:
        print(f"❌ [app.py] Hata (get_sessions): {e}")
        return jsonify({"error": f"Oturumlar getirilirken hata: {e}"}), 500

@app.route('/api/history/<string:session_id>', methods=['GET'])
def get_history(session_id):
    """Belirli bir sohbetin tüm mesajlarını getir"""
    try:
        history_raw = database.get_chat_history(session_id)
        history_list = []

        for row in history_raw:
            sender, message, timestamp = row
            history_list.append({
                "sender": sender,
                "text": message,
                "timestamp": timestamp
            })

        return jsonify({"history": history_list})

    except Exception as e:
        print(f"❌ [app.py] Hata (get_history): {e}")
        return jsonify({"error": f"Geçmiş getirilirken hata: {e}"}), 500

@app.route('/api/chat/<string:session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    """Belirli bir sohbeti sil"""
    try:
        success = database.delete_chat(session_id)

        if success:
            return jsonify({
                "success": True,
                "message": "Sohbet başarıyla silindi."
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Veritabanında silinirken hata oluştu."
            }), 500

    except Exception as e:
        print(f"❌ [app.py] Hata (delete_chat_session): {e}")
        return jsonify({"error": f"Sunucu hatası: {e}"}), 500

@app.route('/api/chatbot', methods=['POST'])
def chat():
    """Ana chatbot endpoint'i - RAG sistemiyle yanıt üretir"""

    if not is_model_ready:
        return jsonify({
            "error": "Model yüklenemedi, lütfen sunucu loglarını kontrol edin."
        }), 500

    try:
        # JSON'dan veri al
        data = request.get_json()

        if not data:
            return jsonify({"error": "İstek gövdesi boş"}), 400

        user_message = data.get('message')
        session_id = data.get('session_id')
        is_temporary = data.get('is_temporary', False)

        print(f"\n📨 Yeni istek: session_id={session_id}, is_temporary={is_temporary}")
        print(f"💬 Mesaj: {user_message[:50]}...")

        # Session kontrolü
        if not session_id or session_id == 'null':
            session_id = str(uuid.uuid4())
            print(f"✅ Yeni oturum: {session_id}")

        if not user_message:
            return jsonify({"error": "Mesaj içeriği boş olamaz"}), 400

        # Mesajı veritabanına kaydet (geçici değilse)
        if not is_temporary:
            database.log_message(session_id, "user", user_message)

        # 🎯 RAG SİSTEMİNİ ÇAĞIR
        print("🤖 RAG sistemi çalışıyor...")
        bot_response = model_service.get_model_response(user_message)

        print(f"✅ Yanıt oluşturuldu: {len(bot_response)} karakter")

        # Bot yanıtını kaydet (geçici değilse)
        if not is_temporary:
            database.log_message(session_id, "bot", bot_response)

        return jsonify({
            "reply": bot_response,
            "session_id": session_id
        })

    except Exception as e:
        print(f"❌ [app.py] Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Sunucu tarafında bir hata oluştu: {e}"
        }), 500

# --- SUNUCU BAŞLAT ---
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Production'da debug=False
