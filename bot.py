import feedparser
import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import google.generativeai as genai

# ==========================================
# 1. KONFIGURASI (DIAMBIL DARI GITHUB SECRETS)
# ==========================================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")

# Konfigurasi Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Sumber Berita
RSS_SOURCES = [
    "https://fcbayern.com/en/news/rss", 
    "https://www.bavarianfootballworks.com/rss/current.xml"
]

# GANTI LINK DI BAWAH INI DENGAN LINK SHOPEE AFFILIATE ANDA
LINK_SHOPEE = "https://shope.ee/MASUKKAN_LINK_KAMU_DISINI"

# Identitas Browser agar tidak diblokir server (User-Agent)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ==========================================
# 2. FUNGSI SCRAPING (AMBIL DATA LENGKAP)
# ==========================================
def ambil_data_lengkap(url):
    try:
        # Mengambil halaman web dengan penyamaran
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari Foto Utama (Open Graph Image)
        foto = soup.find("meta", property="og:image")
        url_foto = foto["content"] if foto else ""

        # Mengambil teks paragraf dan tweet
        konten_mentah = []
        for tag in soup.find_all(['p', 'blockquote', 'h3']):
            teks = tag.get_text(strip=True)
            if tag.name == 'blockquote' and 'twitter-tweet' in tag.get('class', []):
                konten_mentah.append(f"[TWEET: {teks}]")
            else:
                konten_mentah.append(teks)
        
        # Batasi teks agar Gemini tidak overload (maksimal 10 paragraf)
        return "\n\n".join(konten_mentah[:10]), url_foto
    except Exception as e:
        print(f"Gagal mengambil data dari {url}: {e}")
        return None, ""

# ==========================================
# 3. PROSES UTAMA BOT
# ==========================================
def jalankan_bot():
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f:
            f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    for rss_url in RSS_SOURCES:
        try:
            print(f"Mengecek sumber: {rss_url}")
            # Ambil RSS Feed dengan penyamaran
            rss_response = requests.get(rss_url, headers=HEADERS, timeout=15)
            feed = feedparser.parse(rss_response.content)
            
            for entry in feed.entries[:1]: # Cek berita terbaru
                if entry.link in posted_links:
                    print(f"Berita sudah pernah dipost: {entry.title}")
                    continue

                teks_asli, url_foto = ambil_data_lengkap(entry.link)
                if not teks_asli:
                    continue

                print(f"Sedang meminta Gemini menulis ulang artikel: {entry.title}")
                
                # PROMPT EDITOR SASTRA (Instruksi khusus untuk gaya bahasa yang luwes)
                prompt = (
                    f"Kamu adalah Editor Senior portal berita Indobayern. "
                    f"Tugasmu adalah menceritakan kembali berita Bayern Munich ini dalam Bahasa Indonesia yang mengalir, "
                    f"penuh gairah fans (Mia San Mia), dan memiliki estetika bahasa yang baik (hindari gaya kaku mesin). "
                    f"Hapus bagian iklan podcast, Spotify, atau media sosial luar. "
                    f"Jika ada tanda [TWEET: ...], buatkan kutipan yang rapi di dalam teks. "
                    f"Berita: {teks_asli[:3000]}"
                )

                response = model.generate_content(prompt)
                hasil_ai = response.text
                
                # Memisahkan Judul (Baris Pertama) dan Isi
                baris_hasil = hasil_ai.split('\n')
                judul_id = baris_hasil[0].replace('**', '').replace('Judul:', '').strip()
                isi_id = "<br><br>".join(baris_hasil[1:]).strip()

                # TEMPLATE HTML UNTUK BLOGGER
                html_content = f"""
                <div style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.8; color: #333; max-width: 700px; margin: auto;">
                    <img src="{url_foto}" style="width: 100%; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);" />
                    <h1 style="color: #dc052d; font-size: 28px; border-bottom: 2px solid #dc052d; padding-bottom: 10px;">{judul_id}</h1>
                    <div style="text-align: justify; font-size: 17px;">{isi_id}</div>
                    
                    <br>
                    <p style="font-size: 12px; color: #888; font-style: italic;">
                        Sumber Asli: <a href="{entry.link}" style="color: #dc052d; text-decoration: none;">{entry.link}</a>
                    </p>
                    <hr style="border: 0; border-top: 1px solid #eee;">
                    
                    <div style="background: #dc052d; color: white; padding: 30px; border-radius: 15px; text-align: center; margin-top: 25px;">
                        <h2 style="margin: 0; font-size: 22px;">🔴⚪ Mia San Mia! 🔴⚪</h2>
                        <p style="margin: 10px 0 20px;">Dapatkan Jersey & Aksesoris Bayern Munich terbaru di Shopee:</p>
                        <a href="{LINK_SHOPEE}" style="display: inline-block; background: white; color: #dc052d; padding: 15px 35px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">BELI SEKARANG DI SHOPEE</a>
                    </div>
                    <p style="text-align: center; color: #666; font-style: italic; margin-top: 20px;">Admin Indobayern - Salam Satu Nyali!</p>
                </div>
                """

                # Mengirim Email ke Blogger
                msg = EmailMessage()
                msg['Subject'] = judul_id
                msg['From'] = EMAIL_SENDER
                msg['To'] = BLOGGER_EMAIL
                msg.add_alternative(html_content, subtype='html')

                with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20) as smtp:
                    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    smtp.send_message(msg)

                # Simpan Memori ke file teks
                with open(file_memori, "a") as f:
                    f.write(entry.link + "\n")
                
                print(f"Sukses Terbit (Versi Gemini): {judul_id}")
                return # Memproses satu berita saja per sesi

        except Exception as e:
            print(f"Terjadi kesalahan saat memproses {rss_url}: {e}")

if __name__ == "__main__":
    jalankan_bot()
