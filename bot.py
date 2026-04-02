import feedparser
import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import google.generativeai as genai

# ==========================================
# 1. KONFIGURASI (AMBIL DARI GITHUB SECRETS)
# ==========================================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# DAFTAR SUMBER BERITA
RSS_SOURCES = [
    "https://fcbayern.com/en/news/rss", 
    "https://www.bavarianfootballworks.com/rss/current.xml"
]

# GANTI LINK DI BAWAH INI DENGAN LINK SHOPEE AFFILIATE KAMU
LINK_SHOPEE = "https://shope.ee/MASUKKAN_LINK_KAMU_DISINI"

# ==========================================
# 2. FUNGSI SCRAPING (AMBIL DATA LENGKAP)
# ==========================================
def ambil_data_lengkap(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari Foto Utama
        foto = soup.find("meta", property="og:image")
        url_foto = foto["content"] if foto else ""

        # Cari Teks & Tweet
        konten_mentah = []
        # Mengambil paragraf, sub-judul, dan blockquote (untuk tweet)
        for tag in soup.find_all(['p', 'blockquote', 'h3', 'h2']):
            if tag.name == 'blockquote' and 'twitter-tweet' in tag.get('class', []):
                link_tweet = tag.find('a', href=True)
                url_t = link_tweet['href'] if link_tweet else ""
                konten_mentah.append(f"[TWEET_DITEMUKAN: {tag.get_text(strip=True)} | Link: {url_t}]")
            else:
                konten_mentah.append(tag.get_text(strip=True))
        
        teks_asli = "\n\n".join(konten_mentah)
        return teks_asli, url_foto
    except Exception as e:
        print(f"Gagal mengambil data dari {url}: {e}")
        return None, ""

# ==========================================
# 3. JALANKAN PROSES BOT
# ==========================================
def jalankan_bot():
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    for rss_url in RSS_SOURCES:
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries[:2]: # Cek 2 berita terbaru per sumber
            if entry.link in posted_links:
                continue

            try:
                teks_mentah, url_foto = ambil_data_lengkap(entry.link)
                if not teks_mentah or len(teks_mentah) < 300:
                    continue

                # INSTRUKSI GEMINI (Gaya Sastra & Editor Senior)
                prompt = (
                    f"Kamu adalah Editor Senior blog Indobayern. Tugasmu:\n"
                    f"1. Terjemahkan berita ini ke Bahasa Indonesia yang seru, luwes, dan emosional bagi fans Bayern.\n"
                    f"2. Hapus semua teks yang tidak relevan (iklan podcast, Spotify, follow medsos luar, dsb).\n"
                    f"3. Jika ada tanda [TWEET_DITEMUKAN: ...], buatkan format HTML blockquote yang cantik untuk isi tweet tersebut dan sertakan link aslinya.\n"
                    f"4. Gunakan diksi Sastra Indonesia yang baik, bukan sekadar translasi mesin.\n"
                    f"5. Judul harus menarik (Clickbait tapi elegan).\n\n"
                    f"Teks Asli: {teks_mentah[:4500]}"
                )

                response = model.generate_content(prompt)
                hasil_ai = response.text
                
                # Memisahkan Judul dan Isi
                baris = hasil_ai.split('\n')
                judul_indo = baris[0].replace('Judul:', '').replace('**', '').strip()
                isi_indo = "<br><br>".join(baris[1:]).strip()

                # TEMPLATE TAMPILAN BLOG (HTML)
                html_content = f"""
                <div style="font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; line-height: 1.8; max-width: 700px; margin: auto;">
                    <img src="{url_foto}" style="width: 100%; border-radius: 12px; margin-bottom: 20px;" />
                    <h1 style="color: #dc052d; font-size: 28px;">{judul_indo}</h1>
                    <div style="font-size: 17px; text-align: justify;">{isi_indo}</div>
                    <br><hr>
                    <p style="font-size: 12px; color: #999;">Sumber asli: <a href="{entry.link}">{entry.link}</a></p>
                    
                    <div style="background: #dc052d; color: white; padding: 25px; border-radius: 15px; text-align: center; margin-top: 30px;">
                        <h2 style="margin: 0; font-size: 22px;">🔴⚪ Mia San Mia! 🔴⚪</h2>
                        <p style="margin: 10px 0 20px;">Dapatkan Jersey & Aksesoris Bayern Munich terbaru di Shopee:</p>
                        <a href="{LINK_SHOPEE}" style="display: inline-block; background: #fff; color: #dc052d; padding: 15px 35px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">BELI SEKARANG DI SHOPEE</a>
                    </div>
                    <p style="text-align: center; color: #666; font-style: italic; margin-top: 20px;">Admin Indobayern - Salam Satu Nyali!</p>
                </div>
                """
                
                # KIRIM EMAIL KE BLOGGER
                msg = EmailMessage()
                msg['Subject'] = judul_indo
                msg['From'] = EMAIL_SENDER
                msg['To'] = BLOGGER_EMAIL
                msg.add_alternative(html_content, subtype='html')

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    smtp.send_message(msg)

                # Simpan agar tidak diposting ulang
                with open(file_memori, "a") as f:
                    f.write(entry.link + "\n")
                
                print(f"Sukses Posting: {judul_indo}")
                return # Posting satu per satu agar lebih rapi

            except Exception as e:
                print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    jalankan_bot()
