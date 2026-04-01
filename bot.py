import feedparser
import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
from deep_translator import GoogleTranslator

# 1. SETUP EMAIL
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")

# 2. SUMBER BERITA
RSS_URL = "https://www.bavarianfootballworks.com/rss/current.xml"

def ambil_data_lengkap(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # AMBIL FOTO UTAMA (Mencari di OpenGraph Meta)
        foto = soup.find("meta", property="og:image")
        url_foto = foto["content"] if foto else ""

        # AMBIL ISI BERITA
        paragraphs = soup.find_all('p')
        isi_berita = "\n\n".join([p.get_text() for p in paragraphs[:-3]])
        return isi_berita, url_foto
    except:
        return None, ""

def jalankan_bot():
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    feed = feedparser.parse(RSS_URL)
    translator = GoogleTranslator(source='en', target='id')

    for entry in feed.entries[:3]:
        if entry.link in posted_links:
            continue

        try:
            teks_asli, url_foto = ambil_data_lengkap(entry.link)
            if not teks_asli: teks_asli = entry.summary

            judul_indo = translator.translate(entry.title)
            isi_indo = translator.translate(teks_asli[:4000]).replace("\n\n", "<br><br>")
            
            # FORMAT HTML (Agar Foto & Link Shopee muncul)
            html_content = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                <img src="{url_foto}" style="width: 100%; max-width: 600px; border-radius: 8px;" /><br><br>
                {isi_indo}<br><br>
                <hr>
                <b>Sumber Berita:</b> <a href="{entry.link}">{entry.link}</a><br><br>
                <div style="background: #f8f8f8; padding: 15px; border-radius: 5px; text-align: center;">
                    <p>🔴⚪ <b>Dukung Bayern Munich!</b> 🔴⚪</p>
                    <p>Dapatkan Jersey & Aksesoris Bayern terbaru di Shopee:</p>
                    <a href="GANTI_DENGAN_LINK_SHOPEE_KAMU" style="background: #ee4d2d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">BELI DI SHOPEE</a>
                </div>
                <br>
                <p><i>Mia San Mia! - Admin Indobayern</i></p>
            </div>
            """
            
            msg = EmailMessage()
            msg['Subject'] = judul_indo
            msg['From'] = EMAIL_SENDER
            msg['To'] = BLOGGER_EMAIL
            msg.add_alternative(html_content, subtype='html') # Mengirim sebagai HTML

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)

            with open(file_memori, "a") as f:
                f.write(entry.link + "\n")
            
            print(f"Berhasil: {judul_indo} (Dengan Foto)")
            return

        except Exception as e:
            print(f"Gagal: {e}")

if __name__ == "__main__":
    jalankan_bot()
