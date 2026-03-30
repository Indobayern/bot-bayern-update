import tweepy
import feedparser
import os
import re
import google.generativeai as genai

# 1. SETUP AKSES KE X & GEMINI
def get_x_client():
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )

# Konfigurasi AI Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# 2. SUMBER BERITA (RSS)
# Kita pakai Bavarian Football Works sebagai sumber utama
RSS_URL = "https://www.bavarianfootballworks.com/rss/current.xml"

# 3. PENYARING: MENGABAIKAN UPDATE PERTANDINGAN (CONTOH: 45')
def is_live_match_update(text):
    # Mengabaikan jika ada tanda menit (12', 90', dll)
    if re.search(r"\d+'|\d+\+\d+'", text):
        return True
    # Mengabaikan kejadian teknis di lapangan
    blacklist = ["Substitution", "Yellow Card", "Red Card", "Kick-off", "Half-time"]
    return any(word.lower() in text.lower() for word in blacklist)

# 4. TERJEMAHAN PAKAI AI (GAYA SASTRA & TWITTER)
def terjemah_gemini(teks_en):
    prompt = f"Terjemahkan judul berita Bayern Munich ini ke Bahasa Indonesia yang santai tapi tepat untuk fans di Twitter: {teks_en}. Balas dengan hasil terjemahannya saja tanpa tanda petik."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return teks_en # Jika AI gagal, pakai teks asli

# 5. TUGAS UTAMA SI ROBOT
def jalankan_bot():
    client = get_x_client()
    file_memori = "last_links.txt"

    # Buat file catatan jika belum ada
    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    feed = feedparser.parse(RSS_URL)
    
    for entry in feed.entries[:5]:
        link = entry.link
        judul_en = entry.title

        # CEK: Link belum pernah diposting & bukan update menit pertandingan
        if link in posted_links or is_live_match_update(judul_en):
            continue

        # Proses terjemah dengan Gemini
        judul_indo = terjemah_gemini(judul_en)

        # Format Tweet: Judul + Link
        tweet_text = f"{judul_indo}\n\n{link}"

        try:
            client.create_tweet(text=tweet_text)
            # Catat link agar tidak diposting ulang
            with open(file_memori, "a") as f:
                f.write(link + "\n")
            print(f"Berhasil posting: {judul_indo}")
            return # Selesai, posting 1 saja setiap robot "bangun"
        except Exception as e:
            print(f"Gagal posting: {e}")

if __name__ == "__main__":
    jalankan_bot()
