import tweepy
import feedparser
import os
import google.generativeai as genai

# 1. SETUP API
def get_x_client():
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# 2. SUMBER BERITA
RSS_URL = "https://www.bavarianfootballworks.com/rss/current.xml"

def jalankan_bot():
    client = get_x_client()
    file_memori = "last_links.txt"

    if not os.path.exists(file_memori):
        with open(file_memori, "w") as f: f.write("")

    with open(file_memori, "r") as f:
        posted_links = f.read().splitlines()

    feed = feedparser.parse(RSS_URL)
    
    # Ambil 3 berita terbaru saja
    for entry in feed.entries[:3]:
        link = entry.link
        
        # Cek apakah sudah pernah diposting
        if link in posted_links:
            continue

        # Terjemahkan judul pakai Gemini
        prompt = f"Terjemahkan judul berita Bayern Munich ini ke Bahasa Indonesia yang luwes untuk fans Twitter: {entry.title}. Hasilnya saja, tanpa tanda petik."
        try:
            response = model.generate_content(prompt)
            judul_indo = response.text.strip()
        except:
            judul_indo = entry.title

        # POSTING
        tweet_text = f"{judul_indo}\n\n{link}"
        
        # Kita hapus 'try-except' di sini agar kalau gagal, GitHub langsung jadi MERAH
        # Jadi kita tahu pasti apa erornya.
        client.create_tweet(text=tweet_text)
        
        # Catat link
        with open(file_memori, "a") as f:
            f.write(link + "\n")
        
        print(f"Berhasil posting: {judul_indo}")
        return 

if __name__ == "__main__":
    jalankan_bot()
