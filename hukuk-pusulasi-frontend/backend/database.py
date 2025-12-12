#
# BU DOSYA: database.py (YENİ DOSYA)
# BU BİZİM "VERİTABANI FİŞ"İMİZ (ADAPTÖR)
#
import sqlite3
import datetime

# Veritabanı dosyamızın adı. app.py ile aynı yerde olacak.
DB_NAME = 'chat.db'

def init_db():
    """
    Veritabanını ve 'conversations' tablosunu oluşturur (eğer yoksa).
    Bu fonksiyon, ana app.py tarafından sunucu başlarken SADECE BİR KEZ çağrılır.
    """
    try:
        # Veritabanına bağlan (dosya yoksa oluşturulur)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 'conversations' adında bir tablo oluştur
        # Bu tablo, tüm sohbetleri tutacak
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
        ''')
        
        conn.commit() # Değişiklikleri kaydet
        conn.close()  # Bağlantıyı kapat
        
        print(f"✅ [database] Veritabanı '{DB_NAME}' başarıyla başlatıldı.")
        
    except Exception as e:
        print(f"❌ [database] HATA: Veritabanı başlatılırken sorun oluştu: {e}")

def log_message(session_id, sender, message):
    """
    Bir mesajı (kullanıcıdan veya bottan) veritabanına kaydeder.
    app.py, her soru ve cevap için bu fonksiyonu çağıracak.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # O anki zamanı al
        now = datetime.datetime.now()
        
        # SQL sorgusu ile veriyi ekle
        cursor.execute('''
        INSERT INTO conversations (session_id, sender, message, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (session_id, sender, message, now))
        
        conn.commit()
        conn.close()
        
        print(f"✅ [database] Mesaj loglandı: {sender} (Oturum: ...{session_id[-6:]})")
        
    except Exception as e:
        print(f"❌ [database] HATA: Mesaj loglanırken sorun oluştu: {e}")

def get_all_sessions():
    """
    Sol kenar çubuğunu (sidebar) doldurmak için,
    veritabanındaki tüm benzersiz sohbet oturumlarının
    ilk kullanıcı mesajını ve ID'sini getirir.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Her 'session_id' için 'sender'='user' olan en eski mesajı (ilk soruyu)
        # ve o oturumdaki en YENİ mesajın tarihini (lastMessage) al.
        query = """
        SELECT 
            t1.session_id, 
            t1.message, 
            (SELECT MAX(t2.timestamp) FROM conversations t2 WHERE t2.session_id = t1.session_id) as last_message
        FROM conversations t1
        WHERE t1.sender = 'user' AND t1.id IN (
            SELECT MIN(t3.id)
            FROM conversations t3
            WHERE t3.sender = 'user'
            GROUP BY t3.session_id
        )
        ORDER BY last_message DESC
        """
        cursor.execute(query)
        sessions = cursor.fetchall()
        conn.close()
        
        # [(session_id_1, ilk_mesaj_1, son_tarih_1), (session_id_2, ilk_mesaj_2, son_tarih_2), ...]
        return sessions
        
    except Exception as e:
        print(f"❌ [database] HATA: Oturumlar getirilirken sorun oluştu: {e}")
        return []

def get_chat_history(session_id):
    """
    Belirli bir 'session_id'ye ait tüm sohbet geçmişini (hem user hem bot)
    tarih sırasına göre getirir.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        query = """
        SELECT sender, message, timestamp 
        FROM conversations 
        WHERE session_id = ? 
        ORDER BY timestamp ASC
        """
        cursor.execute(query, (session_id,))
        history = cursor.fetchall()
        conn.close()
        
        # [('user', 'merhaba', '2025-11-07...'), ('bot', 'merhaba size...', '2025-11-07...')]
        return history
        
    except Exception as e:
        print(f"❌ [database] HATA: Sohbet geçmişi getirilirken sorun oluştu: {e}")
        return []        

# (Gelecek Adım - İstersek)
# def get_chat_history(session_id):
#     """
#     Belirli bir oturumun tüm sohbet geçmişini getirir.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("SELECT sender, message, timestamp FROM conversations WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
#     history = cursor.fetchall()
#     conn.close()
#     return history


def delete_chat(session_id):
    """
    Belirli bir 'session_id'ye ait TÜM mesajları
    veritabanından kalıcı olarak SİLER.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # SQL'in DELETE komutunu kullanıyoruz
        query = "DELETE FROM conversations WHERE session_id = ?"
        
        cursor.execute(query, (session_id,))
        conn.commit() # Değişikliği veritabanına işle
        conn.close()
        
        print(f"✅ [database] Sohbet silindi: {session_id}")
        return True
        
    except Exception as e:
        print(f"❌ [database] HATA: Sohbet silinirken sorun oluştu: {e}")
        return False