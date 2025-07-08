import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import re
from playwright.sync_api import sync_playwright
import subprocess

# --- Sabitler ve Ayarlar ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
TIMEOUT_SHORT = 30
TIMEOUT_LONG = 60
ROOT_DOWNLOAD_DIR = "Documents"
DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

# --- Yardımcı Fonksiyonlar ---
def clean_filename(filename):
    if not filename: return "isimsiz"
    filename = filename.replace('İ', 'I').replace('ı', 'i').replace('Ö', 'O').replace('ö', 'o')
    filename = filename.replace('Ü', 'U').replace('ü', 'u').replace('Ş', 'S').replace('ş', 's')
    filename = filename.replace('Ğ', 'G').replace('ğ', 'g').replace('Ç', 'C').replace('ç', 'c')
    cleaned_name = re.sub(r'[\\/:*?"<>|]', '', filename)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    return cleaned_name

def get_main_category_links(hub_page_url, base_url):
    print(f"Ana kategori linkleri çekiliyor: {hub_page_url}")
    main_categories = {}
    try:
        response = requests.get(hub_page_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        link_elements = soup.select('div.__side-menu ul li a')
        for a_tag in link_elements:
            href = a_tag.get('href')
            name = a_tag.get_text(strip=True)
            if not href or not name or not href.startswith('/tuketici/') or href == '/tuketici': continue
            full_url = urljoin(base_url, href)
            if full_url not in main_categories.values():
                main_categories[name] = full_url
                print(f"Ana kategori bulundu: {name} -> {full_url}")
    except requests.exceptions.RequestException as e: print(f"HATA: Ana kategori sayfası alınamadı: {e}")
    return main_categories

# Direkt metin HTML'in içindeyse onu alıp pdf olarak kaydeder.
# --- İndirme ve Dönüştürme Fonksiyonları ---
def save_content_as_pdf(html_content_div, full_path):
    if os.path.exists(full_path):
        print(f"Atlandı: Sayfa içeriği PDF'i zaten mevcut: {full_path}")
        return
    print(f"Sayfa içeriği PDF olarak kaydediliyor: {full_path}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            full_html = f'<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>İçerik</title><style>body {{ font-family: sans-serif; line-height: 1.6; }} img {{ max-width: 100%; height: auto; }}</style></head><body>{html_content_div.prettify()}</body></html>'
            page.set_content(full_html, wait_until='load')
            page.pdf(path=full_path, format='A4', margin={'top': '20mm', 'bottom': '20mm', 'left': '15mm', 'right': '15mm'})
            browser.close()
        print(f"Başarılı: Sayfa içeriği PDF'e dönüştürüldü.")
    except Exception as e: print(f"HATA: HTML'den PDF'e dönüştürme hatası: {e}")

def download_file(url, full_path):
    if os.path.exists(full_path):
        print(f"Atlandı: Dosya zaten mevcut: {full_path}")
        return
    print(f"İndiriliyor: {url} -> {os.path.basename(full_path)}")
    try:
        response = requests.get(url, stream=True, headers=HEADERS, timeout=TIMEOUT_LONG)
        response.raise_for_status()
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        print("Başarılı: İndirme tamamlandı.")
        if full_path.lower().endswith(('.doc', '.docx')): convert_word_to_pdf(full_path)
    except requests.exceptions.RequestException as e: print(f"HATA: İndirme hatası: {e}")

def convert_word_to_pdf(doc_path):
    print(f"Converting Word to PDF: {os.path.basename(doc_path)}")
    try:
        output_dir = os.path.dirname(doc_path)
        command = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, doc_path]
        process = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if process.returncode == 0:
            print("Success: Word file converted to PDF and original deleted.")
            os.remove(doc_path)
        else: print(f"ERROR: soffice conversion error: {process.stderr}")
    except Exception as e: print(f"ERROR: Unexpected error during Word to PDF conversion: {e}")

def scan_external_page_for_docs(external_url):
    print(f"Scanning external page: {external_url}")
    docs_found = []
    try:
        response = requests.get(external_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.select('a[href]'):
            href = link.get('href')
            if not href: continue
            is_document = any(href.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)
            img_inside = link.find('img')
            img_title = img_inside.get('title', '') if img_inside else ''
            if is_document or 'pdf' in img_title.lower() or 'word' in img_title.lower():
                doc_title = clean_filename(img_title or "Belge")
                full_download_url = urljoin(external_url, href)
                file_ext = os.path.splitext(urlparse(full_download_url).path)[1]
                if not file_ext: file_ext = ".pdf" if 'pdf' in img_title.lower() else ".doc"
                docs_found.append({'title': doc_title, 'download_url': full_download_url, 'extension': file_ext})
    except Exception as e:
        print(f"    HATA: Harici sayfa taranırken hata ({external_url}): {e}")
    return docs_found

# --- ÖZYİNELEMELİ ANA FONKSİYON ---

def process_page(url, base_url, path_context, visited_urls):
    """Bir sayfayı özyinelemeli olarak işler: tüm linkleri takip eder, belgeleri indirir."""
    clean_url = url.split('#')[0].rstrip('/')
    if clean_url in visited_urls: return
    visited_urls.add(clean_url)

    indent = "  " * len(path_context)
    print(f"\n{indent}➡️  İşleniyor ({len(path_context)}. seviye): {' / '.join(path_context)}")
    print(f"{indent}    URL: {url}")
    
    current_dir = os.path.join(ROOT_DOWNLOAD_DIR, *path_context)
    os.makedirs(current_dir, exist_ok=True)

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SHORT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- DEĞİŞİKLİK BURADA BAŞLIYOR ---
        # Sayfadaki tüm işlemleri alakasız linkleri (header/footer vb.) elemek için __zone içinde yap
        zone_div = soup.select_one('div.__zone')
        
        if not zone_div:
            print(f"{indent}Uyarı: Sayfada '__zone' alanı bulunamadı. Bu sayfa atlanıyor.")
            return
        # --- DEĞİŞİKLİK BİTTİ ---

        processed_hrefs = set()

        # 1. Sayfadaki TÜM linkleri (SADECE __zone İÇİNDEKİ) bul ve sınıflandır
        for link in zone_div.select('a[href]'): # <-- DEĞİŞİKLİK: soup yerine zone_div kullanılıyor
            href = link.get('href', '').strip()
            if not href or href.startswith(('mailto:', 'javascript:')) or href in processed_hrefs: continue
            
            processed_hrefs.add(href)
            link_text = clean_filename(link.get_text(strip=True)) or f"isimsiz_link_{time.time():.0f}"
            full_url = urljoin(base_url, href)

            if any(href.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS):
                print(f"{indent}    [BELGE] Bulundu: {link_text}")
                file_ext = os.path.splitext(urlparse(href).path)[1]
                file_path = os.path.join(current_dir, f"{link_text}{file_ext}")
                download_file(full_url, file_path)
            elif full_url.startswith(base_url):
                print(f"{indent}    [SİTE İÇİ LİNK] Takip ediliyor: {link_text}")
                next_path_context = path_context + [link_text]
                process_page(full_url, base_url, next_path_context, visited_urls)
            else:
                print(f"{indent}    [HARİCİ LİNK] İçerik taranıyor: {link_text}")
                external_docs = scan_external_page_for_docs(full_url)
                if external_docs:
                    print(f"{indent}    Harici sayfada {len(external_docs)} belge bulundu.")
                    for doc in external_docs:
                        filename = f"{link_text} - {doc['title']}{doc['extension']}"
                        file_path = os.path.join(current_dir, filename)
                        download_file(doc['download_url'], file_path)

        # 2. Sayfa içeriğini (__content içindeki) PDF olarak arşivle
        content_for_pdf = zone_div.select_one('div.__content') # <-- DEĞİŞİKLİK: __zone içindeki __content'i bul
        if content_for_pdf and content_for_pdf.get_text(strip=True, separator=' '):
            pdf_path = os.path.join(current_dir, f"_Sayfa_İçeriği - {path_context[-1]}.pdf")
            save_content_as_pdf(content_for_pdf, pdf_path)

    except requests.exceptions.RequestException as e:
        print(f"{indent}HATA: Sayfa alınamadı ({url}): {e}")
    except Exception as e:
        print(f"{indent}HATA: Beklenmedik hata ({url}): {e}")


# --- ANA ÇALIŞMA AKIŞI (Değişiklik Yok) ---
if __name__ == "__main__":
    BASE_URL = "https://ticaret.gov.tr/"
    MAIN_HUB_PAGE = urljoin(BASE_URL, "/tuketici/tuketici-bilgi-rehberi")
    visited_urls = set()

    print("--- 1. Adım: Ana Kategoriler Alınıyor ---")
    main_categories = get_main_category_links(MAIN_HUB_PAGE, BASE_URL)

    if not main_categories:
        print("Hiç ana kategori bulunamadı. İşlem sonlandırılıyor.")
    else:
        print("\n--- 2. Adım: Her Kategori İçin Özyinelemeli Tarama Başlatılıyor ---")
        for cat_name, cat_url in main_categories.items():
            process_page(
                url=cat_url,
                base_url=BASE_URL,
                path_context=[clean_filename(cat_name)],
                visited_urls=visited_urls
            )

    print("\n✅ Tüm işlemler tamamlandı.")