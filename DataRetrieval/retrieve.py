import requests
from bs4 import BeautifulSoup
import os
import fitz  # PyMuPDF
from urllib.parse import urljoin, urlparse, unquote, quote
import time
import re
from pathlib import Path

# ========== Ayarlar ==========
TARGET_URL = "https://ticaret.gov.tr/tuketici/mevzuat/6502-sayili-tuketicinin-korunmasi-mevzuati"
OUTPUT_FILE = "consumer_law_links.txt"
DOWNLOAD_DIR = "consumer_law_documents"
VALID_EXTENSIONS = (".pdf", ".docx", ".htm", ".html", ".doc", ".xls", ".xlsx")
VALID_DOMAINS = ("mevzuat.gov.tr", "resmigazete.gov.tr", "tbmm.gov.tr")  # Yasal mevzuat siteleri

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

from urllib.parse import urlparse, urlunparse, quote, unquote

def normalize_url(url, alternative=False):
    """URL'yi normalize eder, uzantıyı opsiyonel olarak değiştirir ve encoding sorunlarını çözer"""
    try:
        # Decode edilmemiş karakterleri çözüyoruz
        decoded_url = unquote(url)
        
        # Parçala
        parsed = urlparse(decoded_url)
        path = parsed.path
        
        # Opsiyonel: Uzantıyı tahminle değiştir (.pdf <-> .docx)
        if alternative:
            if path.endswith('.pdf'):
                path = path[:-4] + '.docx'
            elif path.endswith('.docx'):
                path = path[:-5] + '.pdf'
        
        # Tekrar encode et: Türkçe karakter, boşluk vs.
        encoded_path = quote(path, safe='/')
        encoded_query = quote(parsed.query, safe='=&')
        encoded_fragment = quote(parsed.fragment, safe='')

        # Yeni URL oluştur
        normalized_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            encoded_path,
            '',  # params kısmını boş bırak
            encoded_query,
            encoded_fragment
        ))

        return normalized_url
    
    except Exception as e:
        print(f"⚠️ URL normalizasyon hatası: {e}")
        return url


# ========== Güvenli Dosya Adı ==========
def safe_filename(filename):
    """Dosya adını güvenli hale getirir"""
    # Windows ve Linux için geçersiz karakterleri temizle
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip()
    # Çok uzun dosya adlarını kısalt
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename

# ========== Basit Dosya Adı Üretimi ==========
def generate_simple_filename(pdf_path):
    """PDF dosyasından basit bir dosya adı üretir"""
    try:
        # Dosyanın var olduğunu ve okunabilir olduğunu kontrol et
        if not os.path.exists(pdf_path):
            print(f"⚠️ Dosya bulunamadı: {pdf_path}")
            return os.path.basename(pdf_path)
        
        # Dosya boyutunu kontrol et
        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            print(f"⚠️ Dosya boş: {pdf_path}")
            return os.path.basename(pdf_path)
        
        # PDF'i açmaya çalış
        try:
            with fitz.open(pdf_path) as doc:
                # PDF'in geçerli olduğunu kontrol et
                if len(doc) == 0:
                    print(f"⚠️ PDF boş veya geçersiz: {pdf_path}")
                    return os.path.basename(pdf_path)
                
                # İlk sayfadan metin çek
                try:
                    text = doc[0].get_text()
                except Exception as e:
                    print(f"⚠️ PDF metin çıkarma hatası: {e}")
                    return os.path.basename(pdf_path)
                
                # İlk 100 karakteri al ve temizle
                if text.strip():
                    # İlk satırı al
                    lines = text.split('\n')
                    first_line = ""
                    for line in lines:
                        if line.strip():
                            first_line = line.strip()
                            break
                    
                    if first_line:
                        # Özel karakterleri temizle
                        filename = re.sub(r'[<>:"/\\|?*]', '_', first_line)
                        # Uzunluğu sınırla
                        if len(filename) > 50:
                            filename = filename[:50]
                        # Boşlukları alt çizgi ile değiştir
                        filename = filename.replace(' ', '_')
                        # Çoklu alt çizgileri tek alt çizgi yap
                        filename = re.sub(r'_+', '_', filename)
                        # Başındaki ve sonundaki alt çizgileri kaldır
                        filename = filename.strip('_')
                        
                        if filename:
                            return filename + ".pdf"
                
        except Exception as pdf_error:
            print(f"⚠️ PDF açma hatası: {pdf_error}")
            # PDF açılamazsa, dosya adından çıkarmaya çalış
            return generate_filename_from_path(pdf_path)
            
        return os.path.basename(pdf_path)
        
    except Exception as e:
        print(f"📛 Dosya adı üretiminde hata: {e}")
        return os.path.basename(pdf_path)

# ========== Dosya Yolundan Ad Üretimi ==========
def generate_filename_from_path(file_path):
    """Dosya yolundan anlamlı bir ad üretir"""
    try:
        # Dosya adını al
        filename = os.path.basename(file_path)
        
        # Eğer temp_download ile başlıyorsa, timestamp kullan
        if filename.startswith('temp_download_'):
            return f"belge_{int(time.time())}.pdf"
        
        # Dosya adından uzantıyı çıkar
        name_without_ext = os.path.splitext(filename)[0]
        
        # URL decode et
        decoded_name = unquote(name_without_ext)
        
        # Özel karakterleri temizle
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', decoded_name)
        
        # Uzunluğu sınırla
        if len(clean_name) > 50:
            clean_name = clean_name[:50]
        
        # Boşlukları alt çizgi ile değiştir
        clean_name = clean_name.replace(' ', '_')
        
        # Çoklu alt çizgileri tek alt çizgi yap
        clean_name = re.sub(r'_+', '_', clean_name)
        
        # Başındaki ve sonundaki alt çizgileri kaldır
        clean_name = clean_name.strip('_')
        
        if clean_name:
            return clean_name + ".pdf"
        else:
            return f"belge_{int(time.time())}.pdf"
            
    except Exception as e:
        print(f"⚠️ Dosya yolu adlandırma hatası: {e}")
        return f"belge_{int(time.time())}.pdf"

# ========== Link Doğrulama ==========
def is_valid_link(href):
    """Linkin geçerli bir belge veya mevzuat linki olup olmadığını kontrol eder"""
    if not href:
        return False
    
    href_lower = href.lower()
    
    # Dosya uzantısı kontrolü
    if any(ext in href_lower for ext in VALID_EXTENSIONS):
        return True
    
    # Mevzuat sitesi kontrolü
    if any(domain in href_lower for domain in VALID_DOMAINS):
        return True
    
    # Mevzuat parametresi kontrolü (mevzuat.gov.tr benzeri)
    if 'mevzuat' in href_lower and ('mevzuatno=' in href_lower or 'kanunno=' in href_lower):
        return True
    
    return False

# ========== Gelişmiş Link Toplama ==========
def collect_document_links(url):
    """Sayfadan belge linklerini toplar - tablo odaklı ve web sitesi linkleri dahil"""
    try:
        print(f"🌐 Sayfa analiz ediliyor: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        all_links = set()  # Tekrar eden linkleri önle
        
        # Önce tabloları kontrol et
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            table_link_count = 0
            a_tags = table.find_all('a', href=True)
            
            print(f"📊 Tablo {i+1} analiz ediliyor...")
            
            for tag in a_tags:
                href = tag.get('href')
                if is_valid_link(href):
                    full_url = urljoin(url, href)
                    # URL'yi normalize et
                    normalized_full_url = normalize_url(full_url)
                    all_links.add(normalized_full_url)
                    table_link_count += 1
                    
                    # Link tipini belirle
                    link_type = "Dosya"
                    if any(domain in href.lower() for domain in VALID_DOMAINS):
                        link_type = "Mevzuat Sitesi"
                    
                    print(f"  ✅ {link_type}: {tag.get_text(strip=True)[:50]}...")
            
            if table_link_count > 0:
                print(f"📊 Tablo {i+1}: {table_link_count} link bulundu")
            else:
                print(f"📊 Tablo {i+1}: Link bulunamadı")
        
        # Eğer tablolarda yeterli link yoksa, tüm sayfayı tara
        if len(all_links) < 3:
            print("🔍 Tüm sayfa taranıyor...")
            all_a_tags = soup.find_all('a', href=True)
            
            for tag in all_a_tags:
                href = tag.get('href')
                if is_valid_link(href):
                    full_url = urljoin(url, href)
                    # URL'yi normalize et
                    normalized_full_url = normalize_url(full_url)
                    all_links.add(normalized_full_url)
        
        filtered_links = list(all_links)
        
        # Link tiplerini kategorize et
        file_links = []
        web_links = []
        
        for link in filtered_links:
            if any(ext in link.lower() for ext in VALID_EXTENSIONS):
                file_links.append(link)
            else:
                web_links.append(link)
        
        print(f"🔗 Toplam {len(filtered_links)} benzersiz link bulundu:")
        print(f"  📄 Dosya linkleri: {len(file_links)}")
        print(f"  🌐 Web site linkleri: {len(web_links)}")
        
        return filtered_links

    except Exception as e:
        print(f"🌐 Sayfa okunurken hata: {e}")
        return []

# ========== HTML'den PDF Linki Çıkarma ==========
def extract_pdf_from_html_page(url):
    """HTML sayfasından PDF linkini çıkarır"""
    try:
        print(f"🔍 PDF linki aranıyor: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Direkt PDF linklerini ara
        pdf_links = soup.find_all('a', href=lambda href: href and href.endswith('.pdf'))
        if pdf_links:
            pdf_href = pdf_links[0].get('href')
            pdf_url = urljoin(url, pdf_href)
            print(f"✅ PDF bulundu (direkt link): {pdf_url}")
            return pdf_url
        
        # 2. PDF içeren herhangi bir link ara (href'te pdf geçen)
        pdf_links = soup.find_all('a', href=lambda href: href and 'pdf' in href.lower())
        if pdf_links:
            pdf_href = pdf_links[0].get('href')
            pdf_url = urljoin(url, pdf_href)
            print(f"✅ PDF bulundu (href'te pdf): {pdf_url}")
            return pdf_url
        
        # 3. onclick eventlerinde PDF ara
        onclick_links = soup.find_all('a', onclick=lambda onclick: onclick and 'pdf' in onclick.lower())
        if onclick_links:
            onclick = onclick_links[0].get('onclick')
            # onclick'ten URL çıkarmaya çalış
            import re
            pdf_match = re.search(r'["\']([^"\']*\.pdf[^"\']*)["\']', onclick)
            if pdf_match:
                pdf_url = urljoin(url, pdf_match.group(1))
                print(f"✅ PDF bulundu (onclick): {pdf_url}")
                return pdf_url
        
        # 4. Butonlarda PDF ara
        buttons = soup.find_all('button')
        for button in buttons:
            onclick = button.get('onclick', '')
            if 'pdf' in onclick.lower():
                import re
                pdf_match = re.search(r'["\']([^"\']*\.pdf[^"\']*)["\']', onclick)
                if pdf_match:
                    pdf_url = urljoin(url, pdf_match.group(1))
                    print(f"✅ PDF bulundu (button onclick): {pdf_url}")
                    return pdf_url
        
        # 5. iframe'lerde PDF ara
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'pdf' in src.lower():
                pdf_url = urljoin(url, src)
                print(f"✅ PDF bulundu (iframe): {pdf_url}")
                return pdf_url
        
        # 6. JavaScript kodlarında PDF ara
        scripts = soup.find_all('script')
        for script in scripts:
            script_content = script.get_text()
            if 'pdf' in script_content.lower():
                import re
                pdf_matches = re.findall(r'["\']([^"\']*\.pdf[^"\']*)["\']', script_content)
                if pdf_matches:
                    pdf_url = urljoin(url, pdf_matches[0])
                    print(f"✅ PDF bulundu (script): {pdf_url}")
                    return pdf_url
        
        # 7. Mevzuat.gov.tr için özel arama
        if 'mevzuat.gov.tr' in url.lower():
            # Mevzuat sayfasında genellikle "Görüntüle" veya "PDF" butonları olur
            view_buttons = soup.find_all('a', string=lambda text: text and any(word in text.lower() for word in ['görüntüle', 'pdf', 'indir', 'download']))
            if view_buttons:
                for button in view_buttons:
                    href = button.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        # Bu linke gidip PDF ara
                        try:
                            sub_response = requests.get(full_url, headers=HEADERS, timeout=10)
                            sub_soup = BeautifulSoup(sub_response.content, 'html.parser')
                            sub_pdf_links = sub_soup.find_all('a', href=lambda href: href and href.endswith('.pdf'))
                            if sub_pdf_links:
                                pdf_href = sub_pdf_links[0].get('href')
                                pdf_url = urljoin(full_url, pdf_href)
                                print(f"✅ PDF bulundu (mevzuat alt sayfa): {pdf_url}")
                                return pdf_url
                        except:
                            continue
        
        # 8. Form action'larında PDF ara
        forms = soup.find_all('form')
        for form in forms:
            action = form.get('action', '')
            if 'pdf' in action.lower():
                pdf_url = urljoin(url, action)
                print(f"✅ PDF bulundu (form action): {pdf_url}")
                return pdf_url
        
        # 9. Meta tag'lerde PDF ara
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = meta.get('content', '')
            if 'pdf' in content.lower():
                import re
                pdf_match = re.search(r'https?://[^\s]*\.pdf', content)
                if pdf_match:
                    pdf_url = pdf_match.group(0)
                    print(f"✅ PDF bulundu (meta tag): {pdf_url}")
                    return pdf_url
        
        print(f"⚠️ PDF linki bulunamadı: {url}")
        return None
            
    except Exception as e:
        print(f"❌ PDF arama hatası ({url}): {e}")
        return None

# ========== HTML'i PDF'e Dönüştürme ==========
def convert_html_to_pdf(html_content, output_path):
    """HTML içeriğini PDF'e dönüştürür (basit metin tabanlı)"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Türkçe karakter desteği için font ayarla (isteğe bağlı)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Başlık ve metin içeriğini çıkar
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Mevzuat Belgesi"
        
        # Ana içeriği çıkar (script ve style taglerini kaldır)
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        
        # PDF oluştur
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Başlık ekle
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
        )
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 12))
        
        # İçeriği paragraflar halinde ekle
        paragraphs = text_content.split('\n')
        for para in paragraphs:
            if para.strip():
                try:
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 12))
                except:
                    # Özel karakterlerle sorun olursa basit metin olarak ekle
                    continue
        
        doc.build(story)
        return True
        
    except ImportError:
        print("⚠️ ReportLab kütüphanesi bulunamadı. HTML → PDF dönüşümü yapılamıyor.")
        print("📦 Kurulum: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ HTML → PDF dönüştürme hatası: {e}")
        return False

# ========== Akıllı Mevzuat İndirme ==========
def download_mevzuat_as_pdf(url, download_dir=DOWNLOAD_DIR):
    """Mevzuat sayfasındaki PDF'i bulup indirir, bulamazsa HTML'i PDF'e çevirir"""
    try:
        print(f"🏛️ Mevzuat sayfası işleniyor: {url}")
        
        # Önce sayfadaki PDF linkini ara
        pdf_url = extract_pdf_from_html_page(url)
        
        if pdf_url:
            # PDF linki varsa direkt indir
            print(f"📄 PDF linki bulundu, indiriliyor...")
            return download_file(pdf_url, download_dir)
        else:
            # PDF linki yoksa HTML'i PDF'e çevir
            print(f"🔄 PDF bulunamadı, HTML'i PDF'e çevriliyor...")
            
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            # Dosya adını oluştur
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            if title:
                filename = safe_filename(f"{title.get_text().strip()}.pdf")
            else:
                parsed_url = urlparse(url)
                mevzuat_no = ""
                if 'mevzuatno=' in parsed_url.query.lower():
                    mevzuat_no = parsed_url.query.split('MevzuatNo=')[1].split('&')[0]
                filename = safe_filename(f"mevzuat_{mevzuat_no}.pdf")
            
            # Dosya yolu
            filepath = os.path.join(download_dir, filename)
            
            # Aynı isimde dosya varsa numara ekle
            counter = 1
            while os.path.exists(filepath):
                name, ext = os.path.splitext(filename)
                filepath = os.path.join(download_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            # HTML'i PDF'e çevir
            if convert_html_to_pdf(response.text, filepath):
                print(f"✅ PDF'e çevrildi: {filepath}")
                return filepath
            else:
                # PDF dönüştürme başarısız olursa HTML olarak kaydet
                html_path = filepath.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"⚠️ HTML olarak kaydedildi: {html_path}")
                return html_path
                
    except Exception as e:
        print(f"❌ Mevzuat indirme hatası ({url}): {e}")
        return None

# ========== Akıllı Dosya İndirme ==========
def download_file_or_webpage(url, download_dir=DOWNLOAD_DIR):
    """Dosya veya web sayfasını akıllıca indirir - hepsini PDF olarak"""
    if not url:
        print("⛔️ URL boş, indirme atlandı.")
        return None

    # Dizin oluştur
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    # Link tipini belirle
    url_lower = url.lower()
    is_direct_file = any(ext in url_lower for ext in VALID_EXTENSIONS)
    is_mevzuat_site = any(domain in url_lower for domain in VALID_DOMAINS)
    
    if is_direct_file:
        # Direkt dosya indirme
        if url_lower.endswith('.pdf'):
            return download_file(url, download_dir)
        else:
            # PDF değilse dosyayı indir ve PDF'e çevirmeyi dene
            downloaded_file = download_file(url, download_dir)
            if downloaded_file and not downloaded_file.endswith('.pdf'):
                print(f"📄 Dosya PDF formatına çevrilmeye çalışılıyor...")
                # Burada farklı dosya tiplerini PDF'e çevirme logic'i eklenebilir
                # Şimdilik olduğu gibi bırakıyoruz
            return downloaded_file
    elif is_mevzuat_site:
        # Mevzuat sitesi - PDF ara ve indir
        return download_mevzuat_as_pdf(url, download_dir)
    else:
        print(f"⚠️ Bilinmeyen link tipi: {url}")
        return None

def download_file(url, download_dir=DOWNLOAD_DIR):
    """Dosyayı indirir ve basit adlandırma yapar"""
    if not url:
        print("⛔️ URL boş, indirme atlandı.")
        return None

    # Dizin oluştur
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    try:
        # URL'yi normalize et
        normalized_url = normalize_url(url)
        if normalized_url != url:
            print(f"🔄 URL normalize edildi: {url[:50]}... -> {normalized_url[:50]}...")
        
        # URL'den dosya uzantısını al
        parsed_url = urlparse(normalized_url)
        original_filename = os.path.basename(parsed_url.path)
        ext = os.path.splitext(original_filename)[1].lower()
        
        if not ext:
            ext = '.pdf'  # Varsayılan uzantı
        
        # Geçici dosya adı
        temp_filename = f"temp_download_{int(time.time())}{ext}"
        temp_path = os.path.join(download_dir, temp_filename)

        print(f"⬇️ İndiriliyor: {normalized_url}")
        
        # Dosyayı indir
        response = requests.get(normalized_url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()
        
        # Dosya boyutunu kontrol et
        total_size = int(response.headers.get('content-length', 0))
        if total_size > 50 * 1024 * 1024:  # 50MB limit
            print(f"⚠️ Dosya çok büyük ({total_size/1024/1024:.1f}MB), atlanıyor.")
            return None
        
        # Dosyayı kaydet
        with open(temp_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r  İlerleme: {progress:.1f}%", end='')
        
        print()  # Yeni satır
        
        # Dosya adını basit şekilde belirle
        if ext == '.pdf':
            try:
                # Dosyanın tamamen yazıldığından emin ol
                time.sleep(0.5)  # Kısa bekleme
                
                # Dosya boyutunu kontrol et
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    # PDF'in açılabilir olup olmadığını kontrol et
                    try:
                        with fitz.open(temp_path) as doc:
                            if len(doc) == 0:
                                print(f"⚠️ PDF boş veya geçersiz, dosya siliniyor: {temp_path}")
                                os.remove(temp_path)
                                return None
                    except Exception as pdf_error:
                        print(f"⚠️ PDF açma hatası, dosya siliniyor: {pdf_error}")
                        os.remove(temp_path)
                        return None
                    
                    try:
                        final_filename = generate_simple_filename(temp_path)
                    except Exception as name_error:
                        print(f"⚠️ PDF adlandırma hatası, alternatif yöntem kullanılıyor: {name_error}")
                        final_filename = generate_filename_from_path(temp_path)
                else:
                    final_filename = safe_filename(original_filename) if original_filename else f"belge_{int(time.time())}.pdf"
            except Exception as e:
                print(f"⚠️ Dosya adı üretiminde hata, varsayılan ad kullanılıyor: {e}")
                final_filename = safe_filename(original_filename) if original_filename else f"belge_{int(time.time())}.pdf"
        else:
            final_filename = safe_filename(original_filename) if original_filename else f"belge_{int(time.time())}{ext}"
        
        # Final dosya yolu
        final_path = os.path.join(download_dir, final_filename)
        
        # Aynı isimde dosya varsa numara ekle
        counter = 1
        while os.path.exists(final_path):
            name, ext_part = os.path.splitext(final_filename)
            final_path = os.path.join(download_dir, f"{name}_{counter}{ext_part}")
            counter += 1
        
        # Dosyayı yeniden adlandır
        os.rename(temp_path, final_path)
        
        print(f"✅ Kaydedildi: {final_path}")
        return final_path

    except requests.exceptions.RequestException as e:
        print(f"🌐 Bağlantı hatası ({normalized_url}): {e}")
        # URL encoding sorunu olabilir, alternatif yöntem dene
        try:
            print(f"🔄 Alternatif indirme yöntemi deneniyor...")
            # URL'yi tekrar encode et
            alt_url = quote(url, safe=':/?=&')
            response = requests.get(alt_url, headers=HEADERS, timeout=30, stream=True)
            response.raise_for_status()
            
            # Aynı indirme işlemini tekrarla
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Dosya adını belirle
            final_filename = safe_filename(original_filename) if original_filename else f"belge_{int(time.time())}{ext}"
            final_path = os.path.join(download_dir, final_filename)
            
            # Aynı isimde dosya varsa numara ekle
            counter = 1
            while os.path.exists(final_path):
                name, ext_part = os.path.splitext(final_filename)
                final_path = os.path.join(download_dir, f"{name}_{counter}{ext_part}")
                counter += 1
            
            os.rename(temp_path, final_path)
            print(f"✅ Alternatif yöntemle kaydedildi: {final_path}")
            return final_path
            
        except Exception as alt_e:
            print(f"❌ Alternatif yöntem de başarısız: {alt_e}")
    except Exception as e:
        print(f"⚠️ İndirme hatası ({normalized_url}): {e}")
    
    # Geçici dosyayı temizle
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except:
        pass
    
    return None

# ========== Linkleri Dosyaya Kaydet ==========
def save_links_to_file(links, failed_downloads=None, filename=OUTPUT_FILE):
    """Linkleri detaylı şekilde dosyaya kaydeder"""
    if failed_downloads is None:
        failed_downloads = []
        
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Tüketici Hukuku Belgeleri - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Kaynak: {TARGET_URL}\n")
            f.write(f"# Toplam {len(links)} link bulundu\n")
            if failed_downloads:
                f.write(f"# {len(failed_downloads)} dosya indirme hatası nedeniyle atlandı\n")
            f.write("=" * 80 + "\n\n")
            
            for i, link in enumerate(links, 1):
                f.write(f"{i:3d}. {link}\n")
                
                # Dosya uzantısını veya link tipini belirle
                ext = os.path.splitext(urlparse(link).path)[1].lower()
                if ext in VALID_EXTENSIONS:
                    f.write(f"     Tip: {ext.upper()} Dosya\n")
                elif any(domain in link.lower() for domain in VALID_DOMAINS):
                    f.write(f"     Tip: Mevzuat Web Sayfası\n")
                else:
                    f.write(f"     Tip: Web Linki\n")
                
                # İndirme hatası olan dosyaları işaretle
                if link in failed_downloads:
                    f.write(f"     ❌ İNDİRİLEMEDİ: Dosya indirme sırasında hata oluştu\n")
                
                f.write("\n")
        
        print(f"📄 Linkler '{filename}' dosyasına kaydedildi.")
        return True
    except Exception as e:
        print(f"📄 Dosya kaydetme hatası: {e}")
        return False

# ========== Ana Akış ==========
def main():
    """Ana program akışı"""
    print("🚀 Tüketici Hukuku Belgeleri İndirici Başlatılıyor...")
    print("=" * 60)
    
    # Linkleri topla
    links = collect_document_links(TARGET_URL)
    
    if not links:
        print("❌ Hiç belge linki bulunamadı.")
        return
    
    # Linkleri dosyaya kaydet
    if not save_links_to_file(links):
        print("❌ Linkler kaydedilemedi.")
        return
    
    # Kullanıcıya seçenek sun
    print(f"\n📋 {len(links)} belge linki bulundu.")
    download_choice = "e"
    # input("Tüm dosyaları indirmek istiyor musunuz? (e/h): ").lower().strip()
    
    if download_choice in ['e', 'evet', 'y', 'yes']:
        print(f"\n⬇️ Dosya indirme başlıyor...")
        successful_downloads = 0
        failed_downloads = []
        
        for i, link in enumerate(links, 1):
            print(f"\n📥 [{i}/{len(links)}] İndiriliyor...")
            
            result = download_file_or_webpage(link)
            if result:
                successful_downloads += 1
            else:
                # İndirme başarısız oldu, listeye ekle
                failed_downloads.append(link)
            
            # Kısa bekleme (sunucuya yük vermemek için)
            time.sleep(2)
        
        # İndirme sonuçlarını dosyaya güncelle
        if failed_downloads:
            print(f"\n📝 İndirme sonuçları dosyaya güncelleniyor...")
            save_links_to_file(links, failed_downloads, OUTPUT_FILE)
        
        print(f"\n🎉 İşlem tamamlandı!")
        print(f"✅ {successful_downloads}/{len(links)} dosya başarıyla indirildi.")
        if failed_downloads:
            print(f"❌ {len(failed_downloads)} dosya indirme hatası nedeniyle atlandı.")
        print(f"📁 Dosyalar: {os.path.abspath(DOWNLOAD_DIR)}")
        print(f"📄 Tüm belgeler mümkün olduğunca PDF formatında kaydedildi.")
    else:
        print("📄 Sadece linkler kaydedildi. İndirme işlemi iptal edildi.")

if __name__ == "__main__":
    main()