import feedparser
import os
import smtplib
from email.message import EmailMessage
from deep_translator import GoogleTranslator

# 1. SETUP EMAIL (Ambil dari GitHub Secrets)
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")

# 2. SUMBER BERITA
RSS_URL = "https://www.bavarianfootballworks.com/rss/current.xml"

def jalankan_bot():
    # File untuk mencatat berita yang sudah diposting
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    feed = feedparser.parse(RSS_URL)
    translator = GoogleTranslator(source='en', target='id')

    for entry in feed.entries[:3]: # Ambil 3 berita terbaru
        if entry.link in posted_links:
            continue

        try:
            # Terjemahkan Judul dan Ringkasan secara polos
            judul_indo = translator.translate(entry.title)
            isi_indo = translator.translate(entry.summary)
            
            # Susun Format Email untuk Blogger
            konten_email = f"{isi_indo}\n\nSumber: {entry.link}\n\nCek Jersey Bayern di Shopee: [LINK_SHOPEE_KAMU]"
            
            # PROSES KIRIM EMAIL
            msg = EmailMessage()
            msg.set_content(konten_email)
            msg['Subject'] = judul_indo
            msg['From'] = EMAIL_SENDER
            msg['To'] = BLOGGER_EMAIL

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)

            # Catat link agar tidak posting ulang
            with open(file_memori, "a") as f:
                f.write(entry.link + "\n")
            
            print(f"Berhasil: {judul_indo}")
            return # Posting satu dulu untuk tes

        except Exception as e:
            print(f"Gagal karena: {e}")

if __name__ == "__main__":
    jalankan_bot()
