import feedparser
import os
import smtplib
from email.message import EmailMessage
import google.generativeai as genai

# 1. SETUP API & EMAIL
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# 2. SUMBER BERITA (BFW & Official)
RSS_SOURCES = [
    "https://www.bavarianfootballworks.com/rss/current.xml",
    "https://fcbayern.com/en/news/rss"
]

def jalankan_bot():
    file_memori = "posted_blogs.txt"
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]: # Ambil 2 terbaru dari tiap sumber
            if entry.link in posted_links:
                continue

            # PROMPT GEMINI (Gaya Sastra & Santai)
            prompt = (
                f"Kamu adalah admin Indobayern, fans berat Bayern Munich. "
                f"Terjemahkan dan ceritakan kembali berita ini ke Bahasa Indonesia yang seru: '{entry.title}'. "
                f"Isi berita: '{entry.summary}'. "
                f"Buat judul yang menarik dan isi berita minimal 3 paragraf. "
                f"Akhiri dengan 'Mia San Mia!' dan ajakan beli jersey di Shopee: https://shope.ee/contoh-link"
            )

            try:
                response = model.generate_content(prompt)
                konten_indo = response.text
                judul_indo = konten_indo.split('\n')[0].replace('Judul: ', '')
            except:
                continue

            # KIRIM KE BLOGGER
            msg = EmailMessage()
            msg.set_content(konten_indo)
            msg['Subject'] = judul_indo
            msg['From'] = EMAIL_SENDER
            msg['To'] = BLOGGER_EMAIL

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)

            # CATAT AGAR TIDAK DUPLIKAT
            with open(file_memori, "a") as f:
                f.write(entry.link + "\n")
            
            print(f"Berhasil post: {judul_indo}")
            return # Post satu-satu saja agar tidak dianggap spam

if __name__ == "__main__":
    jalankan_bot()
