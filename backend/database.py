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

        # 'sessions' tablosu - sohbet başlıklarını tutar
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
        ''')

        conn.commit() # Değişiklikleri kaydet
        conn.close()  # Bağlantıyı kapat

        print(f"✅ Veritabanı hazır")

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

        # Mesaj veritabanına kaydedildi (sessizce)

    except Exception as e:
        print(f"❌ [database] HATA: Mesaj loglanırken sorun oluştu: {e}")

def get_all_sessions():
    """
    Sol kenar çubuğunu (sidebar) doldurmak için,
    veritabanındaki tüm benzersiz sohbet oturumlarının
    başlığını ve son mesaj tarihini getirir.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Tüm session_id'leri conversations tablosundan al
        # Sessions tablosunda başlık varsa onu kullan, yoksa ilk mesajı kullan
        query = """
        SELECT DISTINCT
            c1.session_id,
            COALESCE(s.title,
                (SELECT c2.message FROM conversations c2
                 WHERE c2.session_id = c1.session_id
                 AND c2.sender = 'user'
                 ORDER BY c2.id ASC LIMIT 1)) as title,
            (SELECT MAX(c3.timestamp) FROM conversations c3
             WHERE c3.session_id = c1.session_id) as last_message
        FROM conversations c1
        LEFT JOIN sessions s ON s.session_id = c1.session_id
        ORDER BY last_message DESC
        """
        cursor.execute(query)
        sessions = cursor.fetchall()
        conn.close()


        # [(session_id_1, başlık_1, son_tarih_1), (session_id_2, başlık_2, son_tarih_2), ...]
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
    Belirli bir 'session_id'ye ait TÜM mesajları ve session kaydını
    veritabanından kalıcı olarak SİLER.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Conversations tablosundan mesajları sil
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))

        # Sessions tablosundan session kaydını sil
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

        conn.commit() # Değişikliği veritabanına işle
        conn.close()

        print(f"✅ [database] Sohbet silindi: {session_id}")
        return True

    except Exception as e:
        print(f"❌ [database] HATA: Sohbet silinirken sorun oluştu: {e}")
        return False

def save_session_title(session_id, title):
    """
    Bir sohbet oturumunun başlığını kaydeder veya günceller.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.datetime.now()

        # Eğer session zaten varsa güncelle, yoksa ekle
        cursor.execute('''
        INSERT OR REPLACE INTO sessions (session_id, title, created_at, updated_at)
        VALUES (?, ?,
            COALESCE((SELECT created_at FROM sessions WHERE session_id = ?), ?),
            ?)
        ''', (session_id, title, session_id, now, now))

        conn.commit()
        conn.close()

        print(f"✅ [database] Başlık kaydedildi: {title[:30]}... (Oturum: ...{session_id[-6:]})")

    except Exception as e:
        print(f"❌ [database] HATA: Başlık kaydedilirken sorun oluştu: {e}")

def get_session_title(session_id):
    """
    Belirli bir session_id'nin başlığını getirir.
    Eğer başlık yoksa None döner.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT title FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        return None

    except Exception as e:
        print(f"❌ [database] HATA: Başlık getirilirken sorun oluştu: {e}")
        return None

def session_has_messages(session_id):
    """
    Belirli bir session_id için veritabanında mesaj olup olmadığını kontrol eder.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM conversations WHERE session_id = ?', (session_id,))
        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    except Exception as e:
        print(f"❌ [database] HATA: Mesaj kontrolü yapılırken sorun oluştu: {e}")
        return False
