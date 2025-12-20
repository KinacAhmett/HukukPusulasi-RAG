#
# BU DOSYA: app.py (EN GÜNCEL VE DÜZELTİLMİŞ HALİ)
#
import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# İki "Fiş"imizi (servisimizi) import ediyoruz:
import model_service
import database      # YENİ EKLENDİ (database.py dosyamız)

# .env dosyasındaki değişkenleri (API anahtarı gibi) yükler
load_dotenv()

# --- FLASK UYGULAMASI VE SERVİSLERİ BAŞLATMA ---
app = Flask(__name__)
CORS(app)

# Servisleri başlat
is_model_ready = model_service.initialize_model()
database.init_db() # YENİ EKLENDİ

# --- API ENDPOINT'LERİ (KAPILAR) ---

@app.route('/api/health', methods=['GET'])
def health_check():
    if is_model_ready:
        return jsonify({"status": "healthy"}), 200
    else:
        return jsonify({"status": "unhealthy", "reason": "Model yüklenemedi"}), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """
    Frontend'in sol kenar çubuğunu (sidebar) doldurması için.
    Tüm sohbet oturumlarının bir listesini döner.
    """
    try:
        sessions_raw = database.get_all_sessions()
        sessions_list = []

        for row in sessions_raw:
            session_id, first_message, last_message_time = row

            # Frontend'in beklediği 'title' formatını (ilk 30 karakter) oluşturalım
            title = first_message[:30] + '...' if len(first_message) > 30 else first_message

            sessions_list.append({
                "id": session_id,
                "title": title,
                "lastMessage": last_message_time
            })

        return jsonify({"sessions": sessions_list})

    except Exception as e:
        print(f"❌ [app.py] Hata (get_sessions): {e}")
        return jsonify({"error": f"Oturumlar getirilirken sunucu hatası: {e}"}), 500

@app.route('/api/history/<string:session_id>', methods=['GET'])
def get_history(session_id):
    """
    Frontend'in, kenar çubuğundaki bir sohbete tıkladığında
    o sohbetin tüm mesajlarını yüklemesi için.
    """
    try:
        history_raw = database.get_chat_history(session_id)
        history_list = []

        # Frontend'in beklediği 'messages' formatına çevirelim
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
        return jsonify({"error": f"Geçmiş getirilirken sunucu hatası: {e}"}), 500

@app.route('/api/chat/<string:session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    """
    Frontend'in, kenar çubuğundaki bir sohbeti silmesi için.
    """
    try:
        # database.py'deki yeni fonksiyonumuzu çağır
        success = database.delete_chat(session_id)

        if success:
            # Başarılı olursa frontend'e 'tamam' mesajı yolla
            return jsonify({"success": True, "message": "Sohbet başarıyla silindi."}), 200
        else:
            return jsonify({"success": False, "error": "Veritabanında silinirken bir hata oluştu."}), 500

    except Exception as e:
        print(f"❌ [app.py] Hata (delete_chat_session): {e}")
        return jsonify({"error": f"Sunucu hatası: {e}"}), 500

@app.route('/api/chatbot', methods=['POST'])
def chat():
    if not is_model_ready:
        return jsonify({"error": "Model yüklenemedi, lütfen sunucu loglarını kontrol edin."}), 500

    try:
        # --- 1. VERİYİ JSON'DAN DEĞİL, FORM'DAN AL ---
        # Artık request.json yerine request.form kullanıyoruz
        user_message = request.form.get('message')
        session_id = request.form.get('session_id')

        # 'is_temporary' string ('true'/'false') olarak gelir, Python bool'una çevir
        is_temporary_str = request.form.get('is_temporary', 'false')
        is_temporary = is_temporary_str.lower() == 'true'

        # --- 2. DOSYAYI AL ---
        # Dosyayı request.files'dan alıyoruz
        pdf_file = request.files.get('file') # Eğer dosya yoksa bu 'None' olacak

        print(f"DEBUG: Form verisi alındı: message='{user_message}', session_id='{session_id}', is_temporary='{is_temporary}'")
        if pdf_file:
            print(f"DEBUG: Dosya alındı: {pdf_file.filename}")

        # --- Session ve mesaj kontrolü (aynı) ---
        if not session_id or session_id == 'null': # Frontend 'null' stringi yollayabilir
            session_id = str(uuid.uuid4())
            print(f"✅ [app.py] Yeni oturum başlatıldı: {session_id}")

        if not user_message and not pdf_file:
             return jsonify({"error": "Mesaj veya dosya içeriği boş olamaz"}), 400

        # --- Loglama (aynı) ---
        log_text = user_message or f"[Dosya Yüklendi: {pdf_file.filename}]"
        if not is_temporary:
            database.log_message(session_id, "user", log_text)

        # --- 3. MODELİ ÇAĞIR (Yeni parametreyle) ---
        # Modeli çağırırken artık 'pdf_file' stream'ini ve 'session_id'yi de yolluyoruz
        # session_id conversation history tutmak için kullanılır
        bot_response = model_service.get_model_response(user_message, pdf_file_stream=pdf_file, session_id=session_id)

        # --- Loglama (aynı) ---
        if not is_temporary:
            database.log_message(session_id, "bot", bot_response)

        # --- Yanıt (aynı) ---
        return jsonify({
            "reply": bot_response,
            "session_id": session_id
        })

    except Exception as e:
        print(f"❌ [app.py] Hata oluştu: {e}")
        return jsonify({"error": f"Sunucu tarafında bir hata oluştu: {e}"}), 500

# Bu dosya doğrudan çalıştırıldığında sunucuyu başlat
if __name__ == '__main__':
    # Docker container içinde çalışırken host=0.0.0.0 olmalı
    app.run(host='0.0.0.0', port=5000, debug=True)
