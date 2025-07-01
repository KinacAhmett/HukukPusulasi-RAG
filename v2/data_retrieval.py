import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote, urlunparse
import time
import os
import hashlib # Dosya içeriği hash'i için
import mimetypes # Dosya türü tahmin etmek için
import re # Dosya adı temizleme için
from fpdf import FPDF
import html

# User agent tanımı
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Timeout ayarları
TIMEOUT_SHORT = 30  # Kısa istekler için
TIMEOUT_LONG = 45   # Uzun istekler için
RETRY_ATTEMPTS = 3  # Yeniden deneme sayısı
RETRY_DELAY = 2     # Denemeler arası bekleme süresi (saniye)

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Varsayılan değerler (kendi kodunuzdaki RETRY_ATTEMPTS, HEADERS, TIMEOUT_SHORT değerlerini kullanın)
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2 # Saniye
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
TIMEOUT_SHORT = 10 # Saniye

def fix_url_path_encoding(url):
    """
    Verilen URL'nin path (dizin/dosya adı) kısmındaki kodlama sorunlarını düzeltir.
    Boşlukları, Türkçe karakterleri ve diğer özel karakterleri URL uyumlu hale getirir.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    path_parts = path.split('/')
    
    # Her bir path parçasını (dosya adı dahil) URL kodlamasından geçiriyoruz.
    # safe='' parametresi, '/' gibi karakterlerin de kodlanmasını engellemek için genellikle kullanılır
    # ancak burada sadece dosya adını etkilemek istediğimizden her şeyi kodlayıp sonra birleştiriyoruz.
    encoded_path_parts = [quote(part, safe='') for part in path_parts if part]
    
    new_path = '/' + '/'.join(encoded_path_parts)
    fixed_url = urlunparse(parsed_url._replace(path=new_path))
    
    return fixed_url

def get_category_links(base_url, main_mevzuat_page_url):
    """
    Ana mevzuat sayfasından alt kategori linklerini çeker.
    Link ulaşılamazsa veya hatalıysa URL kodlamasını düzeltmeyi dener.
    """
    print(f"Ana mevzuat sayfasından kategori linkleri çekiliyor: {main_mevzuat_page_url}")
    category_links = {}
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            print(f"Deneme {attempt + 1}/{RETRY_ATTEMPTS}")
            response = requests.get(main_mevzuat_page_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            category_elements = soup.select('div.__content ul.dizin-content li a')

            if not category_elements:
                print("Belirtilen CSS seçici ile kategori linkleri bulunamadı. Lütfen HTML yapısını kontrol edin.")
                return {}

            for a_tag in category_elements:
                h5_tag = a_tag.select_one('div.text h5')
                link_text = h5_tag.get_text(strip=True) if h5_tag else a_tag.get_text(strip=True)
                initial_full_url = urljoin(base_url, a_tag['href'])

                # İlk olarak orijinal URL'yi kontrol et
                current_url_to_check = initial_full_url
                
                # Bu link için birden fazla deneme yapabiliriz (opsiyonel)
                for link_check_attempt in range(2): # Orijinal + Düzeltilmiş deneme
                    try:
                        print(f"Kontrol ediliyor: {current_url_to_check}")
                        # requests.head() isteği, sadece başlık bilgilerini alır, içeriği indirmez. Daha hızlıdır.
                        check_response = requests.head(current_url_to_check, headers=HEADERS, timeout=TIMEOUT_SHORT)
                        check_response.raise_for_status() # HTTP hatası varsa istisna fırlatır

                        # Eğer buraya geldiyse, link geçerli demektir
                        if current_url_to_check not in category_links.values():
                            category_links[link_text] = current_url_to_check
                            print(f"Başarılı: {link_text} -> {current_url_to_check}")
                        break # Link geçerli, sonraki kategoriye geç
                        
                    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                        print(f"Link hatası tespit edildi ({current_url_to_check}): {e}")
                        
                        # Eğer ilk deneme başarısız olduysa ve URL henüz düzeltilmemişse
                        if link_check_attempt == 0:
                            print(f"URL kodlaması düzeltilmeye çalışılıyor...")
                            current_url_to_check = fix_url_path_encoding(initial_full_url)
                            # Eğer düzeltilen URL orijinalden farklıysa tekrar deneme yap
                            if current_url_to_check == initial_full_url:
                                print("URL zaten doğru şekilde kodlanmış veya düzeltme mümkün değil.")
                                break # Düzeltme yapılamıyorsa döngüyü sonlandır
                            else:
                                print(f"Düzeltilmiş URL: {current_url_to_check}")
                                # Döngü bir sonraki adımda düzeltilmiş URL'yi kontrol edecek
                        else:
                            # İkinci deneme de (düzeltilmiş URL ile) başarısız oldu
                            print(f"URL düzeltme denemesi başarısız oldu: {link_text}")
                            break # Bu link için başka deneme yapma
                    
            return category_links

        except requests.exceptions.RequestException as e:
            print(f"Ana sayfa isteği hatası: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
            else:
                print("Maksimum deneme sayısına ulaşıldı, çıkılıyor.")
                return {}
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            return {}
    return {}
    
"""BASE_URL = "https://ticaret.gov.tr/"
MAIN_MEVZUAT_PAGE = urljoin(BASE_URL, "tuketici/mevzuat")
category_links = get_category_links(BASE_URL, MAIN_MEVZUAT_PAGE)"""
# print(category_links)

def get_document_info_from_category_page(category_url, base_url):
    """
    Kategori sayfasından belge başlıklarını, tarihlerini (varsa) ve İNDİR linklerini çeker.
    Bu versiyon, sağlanan HTML tbody yapısına göre düzenlenmiştir.
    Hatalı indirme linklerini URL kodlaması açısından düzeltmeyi dener.
    """
    print(f"Belge bilgileri çekiliyor: {category_url}")
    documents = []
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            print(f"Deneme {attempt + 1}/{RETRY_ATTEMPTS}")
            response = requests.get(category_url, headers=HEADERS, timeout=TIMEOUT_LONG)
            response.raise_for_status() # HTTP hataları için istisna fırlatır
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Sayfa genelindeki tarih bilgisini bulma (ör: '31 Aralık 2024')
            # Bu kısım her sayfada mevcut olmayabilir veya farklı bir etikette olabilir.
            page_date = None
            date_element = soup.find('span', string=lambda text: text and text.strip() and text.strip().split() and text.strip().split()[-1].isdigit())
            
            if date_element:
                page_date = date_element.get_text(strip=True)
                print(f"Sayfa genelinde tarih bilgisi bulundu: {page_date}")

            all_tables = soup.find_all('table')
            
            if not all_tables:
                print(f"Uyarı: '{category_url}' sayfasında hiç tablo bulunamadı.")
                return []

            for table in all_tables:
                # Belirli bir başlık satırı arayabiliriz, ancak bu her tabloda olmayabilir.
                # Eğer birden fazla tablo varsa ve belirli olanı ayırt etmemiz gerekiyorsa,
                # bu 'header_row' kontrolü daha spesifik hale getirilmelidir.
                # Şu anki haliyle, header_row'un bulunup bulunmaması tüm tabloyu işlememizi engellemiyor.
                # header_row = table.find('tr', style=lambda s: s and "rgb(35, 87, 178)" in s) 
                
                target_tbody = table.find('tbody') or table # tbody yoksa doğrudan table etiketini kullan
                if not target_tbody:
                    continue # Bu tabloyu atla, bir sonraki tabloya bak

                rows = target_tbody.find_all('tr')
                # İlk satırı (başlık satırı) atlamak için kontrol ekle
                # Eğer tabloda başlık satırı varsa, 'i == 0' kontrolü doğru çalışır.
                for i, row in enumerate(rows):
                    # Eğer başlık satırı ayırt edici bir şekilde varsa (örneğin CSS sınıfı/stili ile),
                    # o satırı atlamak için daha spesifik bir kontrol ekleyebiliriz.
                    # Şimdilik, sadece ilk satırı atlıyoruz.
                    if i == 0: 
                        # Başlık satırını atlamadan önce, gerçekten başlık olup olmadığını kontrol edebiliriz.
                        # Örneğin, <th> etiketleri içeriyor mu?
                        if row.find('th'):
                            continue 
                        # Veya belirli bir metin içeriyor mu?
                        # if "Belge Adı" in row.get_text():
                        #     continue
                    
                    cols = row.find_all('td')
                    if len(cols) >= 2: # En az 2 sütun bekliyoruz (başlık ve link)
                        document_title = cols[0].get_text(strip=True).replace('- ', '', 1).strip()
                        
                        download_link_element = cols[1].find('a', href=True)
                        if download_link_element:
                            initial_download_url = urljoin(base_url, download_link_element['href'])
                            
                            # İndirme linkini kontrol et ve gerekirse düzelt
                            final_download_url = initial_download_url
                            
                            # Bu link için birden fazla deneme yapabiliriz (Orijinal + Düzeltilmiş)
                            for link_check_attempt in range(2): 
                                try:
                                    print(f"İndirme linki kontrol ediliyor: {final_download_url}")
                                    # HEAD isteği daha hızlıdır, sadece URL'nin erişilebilirliğini kontrol eder.
                                    check_response = requests.head(final_download_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
                                    check_response.raise_for_status() 
                                    print(check_response)

                                    # Eğer buraya geldiyse, link geçerli demektir
                                    documents.append({
                                        'title': document_title,
                                        'date': page_date, # Sayfa genelindeki tarih, belgeye atanır
                                        'download_url': final_download_url
                                    })
                                    print(f"✅ Belge Başarılı: {document_title} -> {final_download_url}")
                                    break # Link geçerli, sonraki belgeye geç
                                    
                                except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                                    print(f"❌ İndirme linki hatası tespit edildi ({final_download_url}): {e}")
                                    
                                    if link_check_attempt == 0:
                                        print(f"URL kodlaması düzeltilmeye çalışılıyor...")
                                        fixed_url = fix_url_path_encoding(initial_download_url)
                                        
                                        if fixed_url == initial_download_url:
                                            print("URL zaten doğru şekilde kodlanmış veya düzeltme mümkün değil. Bu link atlanıyor.")
                                            break # Düzeltme yapılamıyorsa döngüyü sonlandır
                                        else:
                                            final_download_url = fixed_url # Düzeltilmiş URL ile tekrar dene
                                            print(f"Düzeltilmiş URL: {final_download_url}")
                                    else:
                                        print(f"Düzeltilmiş URL denemesi de başarısız oldu. Bu belge linki atlanıyor: {document_title}")
                                        break # İkinci deneme de başarısız oldu, bu belge linkini atla
                        else:
                            print(f"Uyarı: '{document_title}' için İNDİR linki bulunamadı.")
                    else:
                        print(f"Uyarı: Beklenmeyen sütun sayısı bulunan satır atlandı: {row.get_text(strip=True)}")
            
            return documents  # Başarılı olursa döndür
            
        except requests.exceptions.Timeout:
            print(f"Timeout hatası (deneme {attempt + 1}/{RETRY_ATTEMPTS}) için {category_url}")
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"{RETRY_DELAY} saniye bekleniyor...")
                time.sleep(RETRY_DELAY)
            else:
                print("Maksimum deneme sayısına ulaşıldı.")
                return []
        except requests.exceptions.RequestException as e:
            print(f"İstek hatası (deneme {attempt + 1}/{RETRY_ATTEMPTS}) için {category_url}: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"{RETRY_DELAY} saniye bekleniyor...")
                time.sleep(RETRY_DELAY)
            else:
                print("Maksimum deneme sayısına ulaşıldı.")
                return []
        except Exception as e:
            print(f"Beklenmeyen hata (deneme {attempt + 1}/{RETRY_ATTEMPTS}) için {category_url}: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"{RETRY_DELAY} saniye bekleniyor...")
                time.sleep(RETRY_DELAY)
            else:
                print("Maksimum deneme sayısına ulaşıldı.")
                return []
    
    return []  # Hiçbir deneme başarılı olmazsa boş liste döndür
    
"""i = 1
# Örnek kullanım
for category_name, category_url in category_links.items():
    documents = get_document_info_from_category_page(category_url, BASE_URL)"""
    
# --- Dosya Adı Temizleme Fonksiyonu ---
def clean_filename(filename):
    """
    Dosya adlarında kullanılamayacak karakterleri temizler ve güvenli bir isim döndürür.
    """
    cleaned_name = re.sub(r'[\\/:*?"<>|]', '', filename)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    return cleaned_name    

def find_first_document_link_in_page(page_url, base_url):
    """
    Bir web sayfasındaki ilk PDF veya Word dosyası linkini bulur ve tam URL olarak döndürür.
    """
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # PDF ve Word dosya uzantılarını arıyoruz
        for ext in ['.pdf', '.doc', '.docx']:
            link = soup.find('a', href=lambda href: href and href.lower().endswith(ext))
            if link:
                return urljoin(base_url, link['href'])
        # Alternatif olarak gömülü PDF (iframe/embed) de olabilir
        for tag in soup.find_all(['iframe', 'embed']):
            src = tag.get('src')
            if src and any(src.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
                return urljoin(base_url, src)
    except Exception as e:
        print(f"Sayfa içindeki belge linki aranırken hata oluştu: {e}")
    return None

# --- Yeni Yardımcı Fonksiyon: HTML Metnini PDF'e Dönüştürme ---
def convert_html_text_to_pdf(html_content, output_filepath):
    """
    HTML içeriğinden metni çıkarır ve bu metni kullanarak bir PDF dosyası oluşturur.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Sadece görünür metni alıyoruz, script, style etiketlerini ve yorumları atlayarak.
        # Bu, PDF'e gereksiz kodların dahil edilmesini önler.
        for script in soup(["script", "style"]):
            script.extract()    # remove them
        
        text = soup.get_text(separator='\n', strip=True) # Metni alırken yeni satırlar ekle
        text = html.unescape(text)
        text = (text
                .replace('\u2019', "'")
                .replace('\u2018', "'")
                .replace('\u201c', '"')
                .replace('\u201d', '"')
                .replace('\u2013', '-')
                .replace('\u2014', '-'))
        
        # FPDF kütüphanesini kullanarak PDF oluştur
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font('DejavuSans', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font("DejavuSans", size=10) # Türkçe karakter desteği için font ayarı önemli!
        
        # Eğer font ekleme başarısız olursa veya font bulunamazsa varsayılan olarak bırakabiliriz,
        # ama Türkçe karakterler için 'CP1254' gibi bir encoding kullanmamız gerekebilir (fpdf'in eski versiyonlarında).
        # fpdf2 ile UTF-8 desteği daha iyidir.

        # Metni satırlara ayır ve PDF'e ekle
        lines = text.split('\n')
        for line in lines:
            pdf.write(5, line + '\n') # 5mm satır yüksekliği

        pdf.output(output_filepath)
        print(f"HTML metni PDF olarak kaydedildi: {output_filepath}")
        return True
    except Exception as e:
        print(f"HTML metnini PDF'e dönüştürürken hata oluştu: {e}")
        return False
    
def download_documents(documents_info, download_folder="Documents"):
    """
    Belge bilgilerini (başlık, URL) kullanarak dosyaları indirir ve belirtilen klasöre kaydeder.
    Dosya adı olarak belge başlığını kullanır.
    Eğer indirme linki bir web sayfasıysa, içindeki ilk PDF/Word dosyasını bulup onu indirir.
    """
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"'{download_folder}' klasörü oluşturuldu.")

    for doc in documents_info:
        title = doc.get('title', 'bilinmeyen_baslik')
        download_url = doc.get('download_url')

        if not download_url:
            print(f"Uyarı: '{title}' için indirme URL'si bulunamadı, atlanıyor.")
            continue

        # Dosya uzantısını URL'den al
        file_extension = os.path.splitext(urlparse(download_url).path)[1]
        is_document = file_extension.lower() in ['.pdf', '.doc', '.docx']
        is_html_file = file_extension.lower() in ['.htm', '.html']
        final_url = download_url
        # Eğer uzantı yoksa veya HTML ise, içerik tipine bak
        if not is_document:
            try:
                head_resp = requests.head(download_url, headers=HEADERS, timeout=TIMEOUT_SHORT, allow_redirects=True)
                content_type = head_resp.headers.get('Content-Type', '').lower()
                if 'html' in content_type or not any(ext in content_type for ext in ['pdf', 'msword', 'officedocument']):
                    # Sayfa ise, içindeki ilk belge linkini bul
                    print(f"'{title}' için doğrudan belge değil, web sayfası tespit edildi. İçerik aranıyor...")
                    found_doc_url = find_first_document_link_in_page(download_url, base_url='https://ticaret.gov.tr/')
                    if found_doc_url:
                        print(f"Gerçek belge linki bulundu: {found_doc_url}")
                        final_url = found_doc_url
                        file_extension = os.path.splitext(urlparse(final_url).path)[1]
                        is_document = file_extension.lower() in ['.pdf', '.doc', '.docx']
                        is_html_file = file_extension.lower() in ['.htm', '.html']
                    else:
                        print(f"'{title}' için sayfa içinde belge linki bulunamadı, HTM içeriği PDF'e dönüştürülecek.")
                        # HTM içeriğini PDF'e dönüştür
                        response = requests.get(download_url, headers=HEADERS, timeout=TIMEOUT_LONG)
                        response.raise_for_status()
                        html_content = response.text
                        
                        # PDF dosya adını oluştur
                        file_extension = '.pdf'
                        file_name_with_ext = f"{title}{file_extension}"
                        full_save_path = os.path.join(download_folder, file_name_with_ext)
                        
                        # HTM'i PDF'e dönüştür
                        if convert_html_text_to_pdf(html_content, full_save_path):
                            print(f"HTM içeriği başarıyla PDF'e dönüştürüldü: {file_name_with_ext}")
                            continue
                        else:
                            print(f"HTM içeriği PDF'e dönüştürülemedi, orijinal HTM indiriliyor.")
                            final_url = download_url
                            file_extension = '.html'
            except Exception as e:
                print(f"'{title}' için içerik tipi kontrolünde hata: {e}")
                continue

        # Tam dosya adını oluştur: Temizlenmiş Başlık + Uzantı
        file_name_with_ext = f"{title}{file_extension}" if file_extension else title
        full_save_path = os.path.join(download_folder, file_name_with_ext)

        print(f"'{title}' belgesi, {file_extension} uzantılı olarak indiriliyor...")
        try:
            response = requests.get(final_url, stream=True, headers=HEADERS, timeout=TIMEOUT_LONG)
            response.raise_for_status()
            with open(full_save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"'{file_name_with_ext}' başarıyla indirildi.")
        except requests.exceptions.RequestException as e:
            print(f"'{file_name_with_ext}' indirme hatası: {e}")
        except Exception as e:
            print(f"Beklenmeyen bir hata oluştu '{file_name_with_ext}' indirilirken: {e}")
            
#download_documents(documents)

# --- Ana Çalışma Akışı ---
if __name__ == "__main__":
    print(os.getcwd())
    BASE_URL = "https://ticaret.gov.tr/"
    MAIN_MEVZUAT_PAGE = urljoin(BASE_URL, "tuketici/mevzuat")
    category_links_dict = get_category_links(BASE_URL, MAIN_MEVZUAT_PAGE)

    if category_links_dict:
        print("\n--- Kategori Linkleri Bulundu ---")
        # Her bir kategori için döngü kuruyoruz
        for category_name, category_url in category_links_dict.items():
            print(f"\nİşleniyor: Kategori: {category_name}, URL: {category_url}")
            
            print(f"--- '{category_name}' Kategorisindeki Belgeler Çekiliyor ---")
            documents_to_download = get_document_info_from_category_page(category_url, BASE_URL)

            if documents_to_download:
                print(f"--- '{category_name}' Kategorisindeki Belgeler İndiriliyor ---")
                # Her kategori için ayrı bir alt klasör oluşturuyoruz
                # Klasör adını kategori adından türetiyoruz ve güvenli hale getiriyoruz
                category_download_folder = os.path.join("Documents", clean_filename(category_name))
                download_documents(documents_to_download, download_folder=category_download_folder)
            else:
                print(f"'{category_name}' kategorisinde indirilecek belge bulunamadı.")
    else:
        print("Kategori linkleri bulunamadı. İşlem sonlandırılıyor.")
        