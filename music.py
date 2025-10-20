import os
import sys
import re
import shutil
import difflib
import tempfile
import subprocess
import platform


def install_system_dependencies():
    """Install system dependencies seperti PortAudio."""
    system = platform.system()
    
    if system == "Linux":
        print("📦 Installing PortAudio for Linux...")
        try:
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "portaudio19-dev"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ PortAudio installed!")
        except Exception:
            pass
    elif system == "Darwin":
        print("📦 Installing PortAudio for macOS...")
        try:
            subprocess.run(["brew", "install", "portaudio"], check=False)
        except Exception:
            pass


def install_python_packages():
    """Install Python packages yang dibutuhkan."""
    packages = ["numpy", "sounddevice", "soundfile", "requests", "pyfiglet"]
    
    print("\n📦 Installing Python packages...")
    for package in packages:
        try:
            print(f"   Installing {package}...", end=" ")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅")
        except Exception:
            print("❌")


try:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    import requests
    from pyfiglet import Figlet
except ImportError:
    print("\n" + "="*60)
    print("🚀 FIRST TIME SETUP - Installing dependencies...")
    print("="*60)
    install_system_dependencies()
    install_python_packages()
    print("\n✅ Installation complete!\n" + "="*60 + "\n")
    
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    import requests
    from pyfiglet import Figlet


AUDIO_FILE = "Christina Perri - A Thousand Years.mp3"
START_TIME = 0
BLOCKSIZE = 2048
LYRIC_OFFSET = 0.0

def fetch_lrc_from_lrclib(title: str, artist: str = ""):
    """Fetch lirik dari LRCLIB API."""
    try:
        print(f"🔍 Searching lyrics for: {title} - {artist}")
        r = requests.get(
            "https://lrclib.net/api/search",
            params={"q": f"{title} {artist}".strip()},
            timeout=10,
        )
        r.raise_for_status()
        for item in r.json():
            if item.get("syncedLyrics"):
                print("✅ Lyrics found from LRCLIB!")
                return item["syncedLyrics"]
    except Exception as e:
        print(f"❌ LRCLIB fetch failed: {e}")
    return None


def parse_lrc(lrc_content: str):
    """Parse konten LRC menjadi list (timestamp, text)."""
    pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)")
    out = []
    for line in lrc_content.split('\n'):
        m = pattern.match(line.strip())
        if m:
            mins, secs, txt = m.groups()
            t = int(mins)*60 + float(secs) + LYRIC_OFFSET
            if txt.strip():
                out.append((max(0.0, t), txt.strip()))
    return sorted(out)

def smooth(vals, window=5):
    """Smooth array untuk visualisasi lebih halus."""
    if len(vals) < window:
        return vals
    k = np.ones(window) / window
    return np.convolve(vals, k, mode="same")


def hsv_to_rgb(h, s, v):
    """Konversi HSV ke RGB."""
    i = int(h*6)
    f = h*6 - i
    p = int(255*v*(1-s))
    q = int(255*v*(1-f*s))
    t = int(255*v*(1-(1-f)*s))
    v = int(255*v)
    i = i % 6
    return [(v,t,p), (q,v,p), (p,v,t), (p,q,v), (t,p,v), (v,p,q)][i]


def colorize(text, r, g, b):
    """Beri warna RGB pada teks."""
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def dim_color(text, r, g, b, factor=0.4):
    """Beri warna RGB redup pada teks."""
    rr = int(r*factor)
    gg = int(g*factor)
    bb = int(b*factor)
    return f"\033[38;2;{rr};{gg};{bb}m{text}\033[0m"


def render_lyrics_block(idx, r, g, b, lyrics):
    figlet = Figlet(font='slant')
    has_lyric = False
    lyric_text = ""
    
    if idx < len(lyrics) and idx >= 0:
        lyric_text = lyrics[idx][1].strip()
        if lyric_text and len(lyric_text) >= 3:
            if any(c.isalpha() for c in lyric_text):
                has_lyric = True
    
    if has_lyric:
        ascii_art = figlet.renderText(lyric_text)
        colored_lines = []
        for line in ascii_art.split('\n'):
            if line.strip():
                colored_lines.append(colorize(line, r, g, b))
        return "\n".join(colored_lines)
    else:
        music_logo = [
            "                                                                    ",
            "            ♪♫♪                    ♪♫♪                             ",
            "          ♪     ♪                ♪     ♪                           ",
            "         ♪       ♪              ♪       ♪                          ",
            "        ♪    🎵   ♪            ♪   🎶    ♪                         ",
            "       ♪           ♪          ♪           ♪                        ",
            "      ♪      🎵     ♪        ♪      🎵     ♪                       ",
            "     ♪               ♪      ♪               ♪                      ",
            "    ♪                 ♪    ♪                 ♪                     ",
            "   ♪        M U S I C  ♪  ♪   P L A Y I N G  ♪                    ",
            "  ♪                     ♪♪                     ♪                   ",
            "                                                                   ",
            "              🎵  🎶  🎵  ♪♫♪  🎵  🎶  🎵                            ",
        ]
        
        colored_lines = []
        for line in music_logo:
            colored_lines.append(colorize(line, r, g, b))
        
        return "\n".join(colored_lines)


def main():
    global start_idx, lyric_index
    

    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Error: File '{AUDIO_FILE}' tidak ditemukan!")
        print(f"💡 Ganti AUDIO_FILE di baris 91 dengan path file musik Anda.")
        return
    

    base = os.path.splitext(os.path.basename(AUDIO_FILE))[0]
    artist_guess, title_guess = ("", base)
    if "-" in base:
        parts = base.split("-", 1)
        artist_guess = parts[0].strip()
        title_guess = parts[1].strip()
    
    print("\n" + "="*60)
    print("🎵 MUSIC LYRIC VISUALIZER")
    print("="*60)
    print(f"📀 File: {AUDIO_FILE}")
    print(f"🎤 Artist: {artist_guess or 'Unknown'}")
    print(f"🎼 Title: {title_guess}")
    print("="*60 + "\n")
    

    lrc_text = fetch_lrc_from_lrclib(title_guess, artist_guess)
    
    if not lrc_text:
        print("\n⚠️  No lyrics found!")
        print("💡 Rename file to: 'Artist - Song Title.mp3'")
        print("   Example: 'Christina Perri - A Thousand Years.mp3'")
        return
    
    lyrics = parse_lrc(lrc_text)
    
    if not lyrics:
        print("❌ Failed to parse lyrics!")
        return
    
    print(f"✅ Loaded {len(lyrics)} lyric lines\n")
    

    print("📂 Loading audio file...")
    data, samplerate = sf.read(AUDIO_FILE, dtype="float32")
    
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    data = data / np.max(np.abs(data))
    
    start_idx = int(START_TIME * samplerate)
    

    term_columns, _ = shutil.get_terminal_size((200, 80))
    columns = min(80, term_columns)
    center = 6
    
    lyric_index = -1
    for i, (t, _) in enumerate(lyrics):
        if t >= START_TIME:
            lyric_index = i - 1
            break
    
    print(f"✅ Ready to play!")
    if START_TIME > 0:
        print(f"⏩ Starting from {START_TIME}s")
    print("\n🎵 Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    

    def callback(outdata, frames, time_info, status):
        global start_idx, lyric_index
        
        if status:
            print(status, file=sys.stderr)
        
        chunk = data[start_idx:start_idx+frames]
        if len(chunk) < frames:
            outdata[:len(chunk), 0] = chunk
            outdata[len(chunk):] = 0
            raise sd.CallbackStop
        else:
            outdata[:, 0] = chunk
        
        play_time = start_idx / samplerate
        

        if lyrics:
            while lyric_index + 1 < len(lyrics) and play_time >= lyrics[lyric_index + 1][0]:
                lyric_index += 1
        

        step = max(1, len(chunk)//columns)
        levels = np.abs(chunk[::step])
        levels = smooth(levels, window=6)
        levels = np.interp(np.clip(levels, 0, 1), [0, 1], [0, center-1]).astype(int)
        

        hue = [0.15, 0.3, 0.6, 0.8][int((play_time*0.2) % 4)]
        r, g, b = hsv_to_rgb(hue, 0.5, 0.9)
        

        screen = []
        for row in range(center*2):
            line = []
            for lvl in levels:
                if row == center:
                    line.append(colorize("─", r, g, b))
                elif row < center and (center-row) <= lvl:
                    line.append(colorize("█", r, g, b))
                elif row > center and (row-center) <= lvl:
                    line.append(colorize("█", r, g, b))
                else:
                    line.append(" ")
            screen.append("".join(line))
        

        if lyrics:
            screen.append("")
            screen.append(render_lyrics_block(lyric_index, r, g, b, lyrics))
        

        sys.stdout.write("\033[H\033[J" + "\n".join(screen))
        sys.stdout.flush()
        start_idx += frames
    

    try:
        with sd.OutputStream(channels=1, samplerate=samplerate,
                           callback=callback, blocksize=BLOCKSIZE, latency="low"):
            sd.sleep(int((len(data) - start_idx) / samplerate * 1000))
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user.")
    
    print("\n" + "="*60)
    print("🎵 Thank you for listening!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
