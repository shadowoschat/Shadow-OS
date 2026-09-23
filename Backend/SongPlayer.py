import subprocess
import time
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# ==============================
# CONFIG
# ==============================
MUSIC_FOLDER = Path(__file__).parent.parent / "Frontend" / "Music"
SUPPORTED_FORMATS = ['*.mp3', '*.wav', '*.m4a', '*.mp4']
MUSIC_FOLDER.mkdir(parents=True, exist_ok=True)

# ==============================
# CLEAN PRINT (NO DUPLICATE)
# ==============================
def log(text="", end="\n"):
    print(text, end=end, flush=True)

# ==============================
# SMOOTH TYPING EFFECT
# ==============================
def type_line(text):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(0.02)
    print()  # newline

# ==============================
# QUERY CLEAN
# ==============================
def extract_song_name(query):
    remove_words = ["play", "song", "music"]
    words = query.lower().split()
    clean_words = [w for w in words if w not in remove_words]
    return " ".join(clean_words)

# ==============================
# LOCAL SEARCH
# ==============================
def search_local_song(song_name):
    try:
        words = song_name.split()
        if not words:
            return None

        all_files = []
        for fmt in SUPPORTED_FORMATS:
            all_files.extend(MUSIC_FOLDER.glob(f'**/{fmt}'))

        log(f"[SEARCHING] {len(all_files)} songs for '{song_name}'")

        for file in all_files:
            name = file.stem.lower()
            if all(w in name for w in words):
                log(f"[FOUND] {file.name}")
                return file

        return None
    except Exception as e:
        log(f"Search error: {e}")
        return None

# ==============================
# PLAY AUDIO
# ==============================
def play_audio(file_path):
    subprocess.Popen(f'start "" "{file_path}"', shell=True)
    log(f">>> Playing {file_path.name}")

# ==============================
# DOWNLOAD SONG
# ==============================
def download_song(query):
    if not yt_dlp:
        log("yt-dlp not installed")
        return None

    try:
        safe_name = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_'))
        output_path = MUSIC_FOLDER / f"{safe_name}.%(ext)s"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "noplaylist": True,
        }

        log(f">>> Downloading {query}...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])

        for f in MUSIC_FOLDER.glob(f"{safe_name}*.mp3"):
            log(f">>> Downloaded {f.name}")
            return f

        return None

    except Exception as e:
        log(f"Download error: {e}")
        return None

# ==============================
# TIME CONVERT
# ==============================
def time_to_seconds(t):
    if isinstance(t, (int, float)):
        return float(t)

    if isinstance(t, str):
        parts = [float(p) for p in t.split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]

    return 0

# ==============================
# LYRICS PLAYER
# ==============================
def play_with_lyrics(song_name, lyrics):
    song_file = search_local_song(song_name)

    if not song_file:
        log(">>> Song not found locally")
        return False

    log(f">>> 🎵 {song_name} with lyrics")
    play_audio(song_file)

    start_time = time.time()

    for t, line in lyrics:
        target_time = time_to_seconds(t)

        while (time.time() - start_time) < target_time:
            time.sleep(0.05)

        if line.strip():
            type_line(line)

    return True

# ==============================
# LYRICS DATABASE
# ==============================
def get_lyrics(song_name):
    song = song_name.lower()

    if "sahiba" in song:
        return [
            ("0:11", "Sahiba.."),
            ("0:13", "Aaya ghar kaahe na..."),
            ("0:18", "Dekhu tujhko chain aata hai..."),
            ("0:21", "Sahiba neendein-veendein aayein na..."),
            ("0:26", "Rastein kaati jaatein na..."),
            ("0:29", "Tera hi khayaal din rain aata hai..."),
            ("0:33", "Rastein kaati jaatein na..."),
            ("0:36", "Tera hi khayaal din rain aata hai..."),
            ("0:39", "Sahiba, samundar..."),
            ("0:42", "Meri aankhon mein reh gaye..."),
            ("0:46", "Hum aate-aate jaana..."),
            ("0:49", "Teri yaadon mein reh gaye..."),
            ("0:52", "Yeh palkein gawaahi hain..."),
            ("0:55", "Hum raaton mein reh gaye..."),
            ("0:58", "Jo waade mein reh gaye..."),
            ("1:01", "Bas baaton mein reh gaye..."),
            ("1:04", "Baaton baaton mein hi..."),
            ("1:07", "Khwabon khwabon mein hi..."),
            ("1:10", "Mere qareeb hai tu..."),
            ("1:13", "Teri talab mujhko, teri talab jaana..."),
            ("1:16", "Ho tu kabhi roo ba roo...")
        ]


    return [
        (1, f"🎵 Playing: {song_name}"),
        (3, "Enjoy the song 🎶")
    ]

# ==============================
# MAIN FUNCTION
# ==============================
def main(query):
    try:
        song_name = extract_song_name(query)

        if not song_name:
            log(">>> Invalid song")
            return False

        log(f">>> 🎵 SongPlayer: {song_name}")

        lyrics = get_lyrics(song_name)

        # STEP 1: local + lyrics
        if play_with_lyrics(song_name, lyrics):
            return True

        # STEP 2: download
        song_file = download_song(song_name)
        if song_file:
            play_audio(song_file)
            return True

        # STEP 3: YouTube fallback
        try:
            from pywhatkit import playonyt
            playonyt(song_name)
            log(f">>> Streaming on YouTube: {song_name}")
            return True
        except:
            pass

        log(">>> Failed to play song")
        return False

    except Exception as e:
        log(f">>> System Error: {e}")
        return False

# ==============================
# TEST MODE
# ==============================
if __name__ == "__main__":
    log("🎵 SHADOWAI - Ultimate Player\n")

    while True:
        q = input("Enter song: ")
        main(q)