import feedparser
import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
from deep_translator import GoogleTranslator

# ==========================================
# 1. KONFIGURASI
# ==========================================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")

RSS_SOURCES = [
    "https://fcbayern.com/en/news/rss", 
    "https://www.bavarianfootballworks.com/rss/current.xml"
]

# GANTI LINK SHOPEE ANDA DI SINI
LINK_SHOPEE = "https://shope.ee/MASUKKAN_LINK_KAMU"

# Filter teks yang tidak diinginkan (iklan podcast/sosmed luar)
BLACKLIST = [
    "Bavarian Podcast Works", "Acast", "Spotify", "Apple Podcasts", 
    "follow us", "Check out the latest episodes", "leading podcast distributor",
    "Twitter", "Facebook", "Instagram", "Threads", "TikTok"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ==========================================
# 2. FUNGSI AMBIL DATA (ANTI-BLOCK)
# ==========================================
def ambil_data_lengkap(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        foto = soup.find("meta", property="og:image")
        url_foto = foto["content"] if foto else ""

        konten_mentah = []
        for tag in soup.find_all(['p', 'blockquote', 'h3']):
            teks = tag.get_text(strip=True)
            if any(word.lower() in teks.lower() for word in BLACKLIST):
                continue
            
            if tag.name == 'blockquote' and 'twitter-tweet' in tag.get('class', []):
                konten_mentah.append(f"<div style='border-left: 4px solid #dc052d; padding: 10px; font-style: italic;'>Kutipan X: {teks}</div>")
            else:
                konten_mentah.append(teks)
        
        return "\n\n".join(konten_mentah[:12]), url_foto
    except:
        return None, ""

# ==========================================
# 3. PROSES UTAMA
# ==========================================
def jalankan_bot():
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    # Inisialisasi Translator (Google Translate via deep-translator)
    translator = GoogleTranslator(source='en', target='id')

    for rss_url in RSS_SOURCES:
        try:
            print(f"Mengecek RSS: {rss_url}")
            rss_response = requests.get(rss_url, headers=HEADERS, timeout=15)
            feed = feedparser.parse(rss_response.content)
            
            for entry in feed.entries[:1]:
                if entry.link in posted_links:
                    continue

                teks_asli, url_foto = ambil_data_lengkap(entry.link)
                if not teks_asli: continue

                # Proses Terjemahan (Cepat & Stabil)
                judul_id = translator.translate(entry.title)
                isi_id = translator.translate(teks_asli[:4500])
                
                html_content = f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.8; color: #333;">
                    <img src="{url_foto}" style="width: 100%; border-radius: 8px; margin-bottom: 20px;" />
                    <h2 style="color: #dc052d; font-size: 24px;">{judul_id}</h2>
                    <div style="text-align: justify; font-size: 16px;">{isi_id.replace('. ', '.<br><br>')}</div>
                    
                    <br>
                    <p style="font-size: 12px; color: #888; font-style: italic;">
                        Sumber Asli: <a href="{entry.link}" style="color: #dc052d; text-decoration: none;">{entry.link}</a>
                    </p>
                    <hr style="border: 0; border-top: 1px solid #eee;">
                    
                    <div style="background: #dc052d; color: white; padding: 25px; border-radius: 12px; text-align: center; margin-top: 20px;">
                        <h3 style="margin: 0; font-size: 20px;">🔴⚪ Mia San Mia! 🔴⚪</h3>
                        <p style="margin: 10px 0;">Dapatkan Jersey & Aksesoris Bayern Munich terbaru di Shopee:</p>
                        <a href="{LINK_SHOPEE}" style="display: inline-block; background: white; color: #dc052d; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">BELI DI SHOPEE</a>
                    </div>
                </div>
                """

                msg = EmailMessage()
                msg['Subject'] = judul_id
                msg['From'] = EMAIL_SENDER
                msg['To'] = BLOGGER_EMAIL
                msg.add_alternative(html_content, subtype='html')

                with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as smtp:
                    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    smtp.send_message(msg)

                with open(file_memori, "a") as f:
                    f.write(entry.link + "\n")
                
                print(f"Sukses Terbit: {judul_id}")
                return 

        except Exception as e:
            print(f"Eror pada {rss_url}: {e}")

if __name__ == "__main__":
    jalankan_bot()
