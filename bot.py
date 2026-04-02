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

LINK_SHOPEE = "https://shope.ee/MASUKKAN_LINK_KAMU"

# DAFTAR KATA KUNCI YANG AKAN DIBUANG (FILTER SAMPAH)
BLACKLIST = [
    "Bavarian Podcast Works", "Acast", "Spotify", "Apple Podcasts", 
    "follow us", "Check out the latest episodes", "leading podcast distributor",
    "Twitter", "Facebook", "Instagram", "Threads", "TikTok"
]

# ==========================================
# 2. FUNGSI PEMBERSIH & PENYAMBUNG ARTIKEL
# ==========================================
def ambil_data_lengkap(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ambil Foto Utama
        foto = soup.find("meta", property="og:image")
        url_foto = foto["content"] if foto else ""

        # Ambil Paragraf & Filter Tweet/Boilerplate
        konten_mentah = []
        for tag in soup.find_all(['p', 'blockquote', 'h3']):
            teks = tag.get_text(strip=True)
            
            # CEK APAKAH PARAGRAF MENGANDUNG KATA BLACKLIST
            if any(word.lower() in teks.lower() for word in BLACKLIST):
                continue # Skip paragraf ini
            
            # Deteksi Tweet (Ubah jadi format kutipan sederhana)
            if tag.name == 'blockquote' and 'twitter-tweet' in tag.get('class', []):
                konten_mentah.append(f"<div style='border-left: 4px solid #dc052d; padding: 10px; font-style: italic;'>Kutipan X (Twitter): {teks}</div>")
            else:
                konten_mentah.append(teks)
        
        # Gabungkan maksimal 12 paragraf agar tidak kepanjangan
        isi_berita = "\n\n".join(konten_mentah[:12])
        return isi_berita, url_foto
    except:
        return None, ""

# ==========================================
# 3. PROSES TRANSLASI & POSTING
# ==========================================
def jalankan_bot():
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    translator = GoogleTranslator(source='en', target='id')

    for rss_url in RSS_SOURCES:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:2]:
            if entry.link in posted_links:
                continue

            try:
                teks_asli, url_foto = ambil_data_lengkap(entry.link)
                if not teks_asli: continue

                # Terjemahkan (Google Translate stabil & cepat)
                judul_id = translator.translate(entry.title)
                isi_id = translator.translate(teks_asli[:4000]) # Batas 4rb karakter
                
                # Format HTML (Tetap dengan gaya Indobayern)
                html_content = f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.8; color: #333;">
                    <img src="{url_foto}" style="width: 100%; border-radius: 8px;" />
                    <h2 style="color: #dc052d;">{judul_id}</h2>
                    <div style="text-align: justify;">{isi_id.replace('. ', '.<br><br>')}</div>
                    <br><hr>
                    <p style="font-size: 11px; color: #777;">Sumber Berita: {entry.link}</p>
                    <div style="background: #dc052d; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <h3 style="margin: 0;">🔴⚪ Mia San Mia! 🔴⚪</h3>
                        <p>Dapatkan Jersey Bayern Munich terbaru di Shopee:</p>
                        <a href="{LINK_SHOPEE}" style="display: inline-block; background: white; color: #dc052d; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">BELI DI SHOPEE</a>
                    </div>
                </div>
                """

                # Kirim ke Blogger
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
                
                print(f"Sukses Posting: {judul_id}")
                return # Posting satu per satu per 3 jam

            except Exception as e:
                print(f"Eror: {e}")

if __name__ == "__main__":
    jalankan_bot()
