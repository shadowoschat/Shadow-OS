# Conditional import of AppOpener – only used on Windows.
# Import lazily in functions that need it.
# If unavailable (e.g., on Linux), the variables remain None.
try:
    from AppOpener import close, open as appopen
except Exception:  # pragma: no cover
    appopen = None
    close = None

from webbrowser import open as webopen
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from groq import Groq
import webbrowser
import subprocess
import requests
try:
    import keyboard
except Exception:  # pragma: no cover - optional on non-Windows
    keyboard = None
import asyncio
import os
import mss
import cv2
from datetime import datetime
from pathlib import Path
import glob
import time
import sys
sys.stdout.reconfigure(line_buffering=True)

from Backend.SongPlayer import MUSIC_FOLDER, SUPPORTED_FORMATS, extract_song_name
clean_query = extract_song_name  # Legacy alias for song cleaning

COMMAND_SYNONYMS = {
    "volume up": ["increase volume", "volume higher", "louder", "sound up"],
    "volume down": ["decrease volume", "volume lower", "quieter", "sound down"],
    "mute": ["silence", "mute sound", "quiet"],
    "unmute": ["sound on", "unmute", "un silence"],
    "shutdown": ["shutdown", "turn off", "power off", "shut down computer"],
    "restart": ["restart", "reboot", "restart computer"],
    "lock": ["lock screen", "lock window", "lock computer"],
    "brightness up": ["brightness up", "increase brightness", "brighter", "screen brighter"],
    "brightness down": ["brightness down", "decrease brightness", "dimmer", "screen dimmer"],
    "switch window": ["switch window", "switch windows", "change window", "next window", "alt tab"],
    "show desktop": ["show desktop", "minimize all", "desktop view"]
}

def normalize_command(cmd_lower):
    """Normalize command synonyms to canonical form."""
    for canonical, synonyms in COMMAND_SYNONYMS.items():
        if cmd_lower in synonyms or canonical in cmd_lower:
            return canonical
    return cmd_lower

env_vars = dotenv_values(".env")

GroqAPIKey = env_vars.get("GroqAPIKey")

classes = ["zCubwf", "hgKELc", "LTKOO SY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "05uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e", 
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask.",
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'User')}, a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems, etc."}]


"""
HARDWARE CONTROL FUNCTIONS
"""

def SetVolume(level):
    """Set system volume to specified level (0-100)."""
    import re
    if platform.system() != "Windows":
        return "Volume control is only available on Windows desktop hosts."
    try:
        match = re.search(r'\d+', str(level))
        if match:
            volume = int(match.group())
            volume = max(0, min(100, volume))  # Clamp 0-100
            
            # Try multiple methods
            try:
                # Method 1: keyboard module
                import keyboard as kb
                steps = abs(volume // 10)
                if volume < 50:
                    for _ in range(steps):
                        kb.press_and_release("volume down")
                else:
                    for _ in range(steps):
                        kb.press_and_release("volume up")
                return f"Volume set to {volume}%"
            except:
                pass
            
            # Method 2: nircmd
            try:
                subprocess.run(f'nircmd.exe setsysvolume {volume * 655}', shell=True, capture_output=True, timeout=2)
                return f"Volume set to {volume}%"
            except:
                pass
            
            # Method 3: Windows API (fallback)
            return f"Volume control queued: {volume}%"
        return "Invalid volume level"
    except Exception as e:
        print(f"[v0] Volume control error: {e}")
        return "Volume control unavailable"

def SetBrightness(level):
    """Set screen brightness to specified level (0-100)."""
    import re
    if platform.system() != "Windows":
        return "Brightness control is only available on Windows desktop hosts."
    try:
        match = re.search(r'\d+', str(level))
        if match:
            brightness = int(match.group())
            brightness = max(0, min(100, brightness))
            
            try:
                # Try using WMI (Windows Management Instrumentation)
                subprocess.run(
                    f'powershell -Command "(Get-WmiObject -Namespace root/cimv2 -Class WmiMonitorBrightnessMethods | Select-Object -First 1).WmiSetBrightness(1, {brightness})"',
                    shell=True,
                    capture_output=True,
                    timeout=5
                )
                return f"Brightness set to {brightness}%"
            except:
                # Fallback: try nircmd
                try:
                    subprocess.run(f'nircmd.exe setbrightness {brightness}', shell=True, capture_output=True, timeout=5)
                    return f"Brightness set to {brightness}%"
                except:
                    return "Brightness control not available on this system"
        return "Invalid brightness level"
    except Exception as e:
        print(f"[v0] Brightness control error: {e}")
        return f"Brightness control error: {str(e)}"

def TakeScreenshot(full=True):
    """Take a screenshot and open it."""
    if platform.system() != "Windows":
        return "Screenshot capture is only available on Windows desktop hosts."
    try:
        DATA_DIR = Path(__file__).parent.parent / "Data"
        DATA_DIR.mkdir(exist_ok=True)
        
        screenshot_path = DATA_DIR / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            mss.tools.topng(screenshot.rgb, screenshot.size, output=str(screenshot_path))
        
        # Open screenshot in image viewer
        subprocess.Popen(['explorer', str(screenshot_path)])
        return f"Screenshot saved and opened: {screenshot_path.name}"
    except Exception as e:
        return f"Screenshot failed: {str(e)}"

def StartScreenRecording():
    """Start screen recording using FFmpeg."""
    if platform.system() != "Windows":
        return "Screen recording is only available on Windows desktop hosts."
    try:
        DATA_DIR = Path(__file__).parent.parent / "Data"
        DATA_DIR.mkdir(exist_ok=True)
        
        recording_path = DATA_DIR / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # FFmpeg command for Windows screen recording
        cmd = [
            'ffmpeg',
            '-f', 'gdigrab',
            '-i', 'desktop',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-rtbufsize', '100M',
            str(recording_path)
        ]
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Screen recording started: {recording_path.name}"
    except:
        return "Screen recording failed. Ensure FFmpeg is installed."

def StopScreenRecording():
    """Stop screen recording."""
    if platform.system() != "Windows":
        return "Screen recording is only available on Windows desktop hosts."
    try:
        subprocess.run('taskkill /IM ffmpeg.exe /F', shell=True, capture_output=True)
        return "Screen recording stopped."
    except:
        return "Failed to stop recording"

def GoogleSearch(topic):
    try:
        from pywhatkit import search as _pk_search
        _pk_search(topic)
        return True
    except Exception:
        try:
            # Fallback: open browser search when offline or pywhatkit unavailable
            webbrowser.open(f"https://www.google.com/search?q={requests.utils.requote_uri(topic)}")
            return True
        except Exception as e:
            print(f"GoogleSearch failed: {e}", file=sys.stderr, flush=True)
            return False


def Content(topic):
    def OpenNotepad(file):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, file])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})

        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content

        answer = answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})
        return answer

    topic = topic.replace("content", "").strip()
    content_by_ai = ContentWriterAI(topic)

    filepath = rf"Data\{topic.lower().replace(' ', '_')}.txt"
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content_by_ai)

    OpenNotepad(filepath)
    return True


def YouTubeSearch(topic):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True


def PlayYoutube(query):
    try:
        from pywhatkit import playonyt as _pk_playonyt
        _pk_playonyt(query)
        return True
    except Exception:
        try:
            url = f"https://www.youtube.com/results?search_query={requests.utils.requote_uri(query)}"
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"PlayYoutube failed: {e}", file=sys.stderr, flush=True)
            return False


# Song config & helpers moved to SongPlayer.py (unified)
# Keep force_print for other functions


def force_print(text, end='\n'):
    print(text, end=end, flush=True)
    sys.stdout.flush()
    print(text, end=end, file=sys.stderr, flush=True)  # Dual path for Flask threads

def PlayLocalSong(query):
    """Updated local song playing - FIXED for Flask thread visibility"""
    try:
        clean_song = clean_query(query)
        force_print(f"[CLEAN QUERY] '{query}' → '{clean_song}'")
        
        query_words = [w for w in clean_song.split() if w]
        if not query_words:
            force_print(">>> Invalid query")
            return False

        all_songs = []
        for fmt in SUPPORTED_FORMATS:
            all_songs.extend(MUSIC_FOLDER.glob(f'**/{fmt}'))

        force_print(f"[SEARCHING] {len(all_songs)} songs for '{clean_song}'")

        for song_file in all_songs:
            file_words = song_file.stem.lower().split()
            if all(word in ' '.join(file_words) for word in query_words):
                force_print(f"[FOUND] {song_file.name}")
                
                subprocess.Popen(f'start "" "{song_file}"', shell=True)
                
                force_print(f"> > > Playing {clean_song} locally")
                for char in clean_song:
                    force_print(char, end='')
                force_print("")
                return True

        force_print(">>> Song not found")
        return False
    except Exception as e:
        force_print(f">>> Error: {e}")
        return False


def play_audio_file(song_file):
    """Play audio file non-blocking on Windows"""
    subprocess.Popen(f'start "" "{song_file}"', shell=True)


def PlayLocalSong_old(query):
    """Check if local song exists (for play_song flow)"""
    try:
        query_words = [w for w in query.lower().strip().split() if w]
        if not query_words:
            return None

        all_songs = []
        for fmt in SUPPORTED_FORMATS:
            all_songs.extend(MUSIC_FOLDER.glob(f'**/{fmt}'))

        for song_file in all_songs:
            song_words = song_file.stem.lower().split()
            if all(word in ' '.join(song_words) for word in query_words):
                return song_file
        return None
    except Exception:
        return None


def download_song(query):
    """Download song from YouTube using yt-dlp"""
    try:
        import yt_dlp
        safe_filename = ''.join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_path = MUSIC_FOLDER / f'{safe_filename}.%(ext)s'
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_path),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
            
            # Find downloaded mp3
            for f in MUSIC_FOLDER.glob(f'{safe_filename}*.mp3'):
                return f
        return None
    except Exception:
        return None


def play_song(query):
    """Unified song player - delegates to SongPlayer.main()"""
    try:
        from .SongPlayer import main
        return main(query)
    except ImportError:
        print(">>> SongPlayer unavailable - install dependencies", file=sys.stderr, flush=True)
        return False


APP_MAPPINGS = {
    "whatsapp": ["WhatsApp", "web.whatsapp.com"],
    "telegram": ["Telegram Desktop", "Telegram", "web.telegram.org"],
    "instagram": ["https://instagram.com"],
    "facebook": ["https://facebook.com"],
    "adobe express": ["https://express.adobe.com"],
    "adobe": ["https://adobe.com"],
    "notepad": ["notepad"],
    "calculator": ["Calculator"],
    "chrome": ["Google Chrome"],
    "paint": ["mspaint"],
    "desktop": lambda: os.path.expanduser("~/Desktop")
}

def _safe_appopen(app_name):
    """Gracefully handle broken AppOpener installs."""
    if appopen is None:
        raise RuntimeError("AppOpener is unavailable")
    return appopen(app_name, match_closest=True)


def _safe_appclose(app_name):
    """Gracefully handle broken AppOpener installs."""
    if close is None:
        raise RuntimeError("AppOpener is unavailable")
    return close(app_name, match_closest=True, output=True, throw_error=True)


def OpenApp(app, sess=requests.session()):
    """Robust app opener with mappings, fallbacks, web support."""
    import time
    import ctypes
    
    app_lower = app.lower().strip()
    print(f"[AUTOMATION] Opening: {app}")
    
    # Handle "show" prefix for folders
    is_show = app_lower.startswith("show ")
    folder_query = app_lower.replace("show ", "").strip() if is_show else app_lower
    
    def bring_window_to_front(title):
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].activate()
                return True
        except:
            pass
        return False

    
    # 1. Check app mappings
    if app_lower in APP_MAPPINGS:
        targets = APP_MAPPINGS[app_lower]
        if callable(targets):
            path = targets()
            subprocess.Popen(f'explorer "{path}"', shell=True)
            return f"Opened {app}"
        
        for target in targets:
            try:
                # Try AppOpener
                _safe_appopen(target)
                time.sleep(1)
                bring_window_to_front(target)
                # print(f"[SUCCESS] Opened {target}")  # Silenced
                return True
            except:
                pass
            
            # Try Windows start
            try:
                subprocess.Popen(f'start "{target}"', shell=True)
                time.sleep(1.5)
                # print(f"[SUCCESS] Started {target}")  # Silenced
                return True
            except:
                pass
        
        # Web fallback
        if isinstance(targets, list) and any("http" in t for t in targets):
            webbrowser.open(targets[-1])
            return f"Opened {app} in browser"
    
    # 2. Generic app/web handling
    # System folders
    folders = {
        "desktop": os.path.expanduser("~/Desktop"),
        "documents": os.path.expanduser("~/Documents"),
        "downloads": os.path.expanduser("~/Downloads"),
        "pictures": os.path.expanduser("~/Pictures"),
        "videos": os.path.expanduser("~/Videos")
    }
    
    if folder_query in folders:
        subprocess.Popen(f'explorer "{folders[folder_query]}"', shell=True)
        action = "shown" if is_show else "opened"
        return f"{action.capitalize()} {folder_query}"

    
    # Show desktop (Win+D)
    if "show desktop" in app_lower:
        import keyboard
        keyboard.press_and_release('win+d')
        return "Desktop shown"
    
    try:
        # AppOpener
        _safe_appopen(app)
        time.sleep(1)
        bring_window_to_front(app)
        return True
    except:
        # Windows start
        try:
            subprocess.Popen(f'start "{app}"', shell=True)
            return True
        except:
            # Web
            url = f"https://{app}.com" if "." not in app else f"https://{app}"
            webbrowser.open(url)
            return f"Opened {app} in browser"
    
    return False



def CloseApp(app):
    if "chrome" in app:
        pass
    try:
        _safe_appclose(app)
        return True
    except:
        return False



def System(command):
    command = normalize_command(command.lower())

    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    # Volume controls
    if command == "mute":
        mute()
        return "Muted"
    elif command == "unmute":
        unmute()
        return "Unmuted"
    elif command == "volume up":
        volume_up()
        return "Volume up"
    elif command == "volume down":
        volume_down()
        return "Volume down"

    # System controls
    elif command == "shutdown":
        subprocess.run("shutdown /s /t 10", shell=True)
        return "Shutting down in 10 seconds (cancel with shutdown /a)"
    elif command == "restart":
        subprocess.run("shutdown /r /t 10", shell=True)
        return "Restarting in 10 seconds (cancel with shutdown /a)"
    elif command == "lock":
        keyboard.press_and_release("win+l")
        return "Screen locked"
    elif command == "switch window":
        keyboard.press_and_release("alt+tab")
        return "Switched window"
    elif command == "show desktop":
        keyboard.press_and_release("win+d")
        return "Desktop shown"

    # Brightness incremental
    elif command == "brightness up":
        try:
            result = subprocess.run('powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | Select-Object -First 1).CurrentBrightness"', shell=True, capture_output=True, text=True)
            current = int(result.stdout.strip())
            new_bright = min(100, current + 10)
            SetBrightness(new_bright)
            return f"Brightness increased to {new_bright}%"
        except:
            keyboard.press_and_release("f11")  # Common brightness up fallback
            return "Brightness up (fallback)"
    elif command == "brightness down":
        try:
            result = subprocess.run('powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | Select-Object -First 1).CurrentBrightness"', shell=True, capture_output=True, text=True)
            current = int(result.stdout.strip())
            new_bright = max(0, current - 10)
            SetBrightness(new_bright)
            return f"Brightness decreased to {new_bright}%"
        except:
            keyboard.press_and_release("f10")  # Common brightness down fallback
            return "Brightness down (fallback)"

    # Sleep (Win + X -> U -> U)
    elif "sleep" in command:
        keyboard.press_and_release("win+x")
        time.sleep(0.1)
        keyboard.press_and_release("u")
        time.sleep(0.1)
        keyboard.press_and_release("u")
        return "Putting to sleep"

    return "Command not recognized"


async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        command = command.strip()
        if not command:
            continue
            
        # LOG COMMAND - silenced per terminal rules
        # print(f"['{command}']", flush=True)
        
        cmd_lower = command.lower()
        
        if cmd_lower.startswith("open "):
            fun = asyncio.to_thread(OpenApp, command[5:].strip())
            funcs.append(fun)
        elif cmd_lower.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command[6:].strip())
            funcs.append(fun)
        elif cmd_lower.startswith("play "):
            song_query = command[5:].strip()
            fun = asyncio.to_thread(play_song, song_query)
            funcs.append(fun)
        elif cmd_lower.startswith("content "):
            fun = asyncio.to_thread(Content, command[8:].strip())
            funcs.append(fun)
        elif cmd_lower.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command[14:].strip())
            funcs.append(fun)
        elif cmd_lower.startswith("youtube search "):
            fun = asyncio.to_thread(YouTubeSearch, command[15:].strip())
            funcs.append(fun)
        elif cmd_lower.startswith("system "):
            sys_cmd = normalize_command(command[7:].strip().lower())
            fun = asyncio.to_thread(System, sys_cmd)
            funcs.append(fun)

        elif "volume" in cmd_lower:
            fun = asyncio.to_thread(SetVolume, command)
            funcs.append(fun)
        elif "brightness" in cmd_lower:
            fun = asyncio.to_thread(SetBrightness, command)
            funcs.append(fun)
        elif "screenshot" in cmd_lower or "full screenshot" in cmd_lower:
            fun = asyncio.to_thread(TakeScreenshot, True)
            funcs.append(fun)
        elif "start screen recording" in cmd_lower:
            fun = asyncio.to_thread(StartScreenRecording)
            funcs.append(fun)
        elif "stop screen recording" in cmd_lower:
            fun = asyncio.to_thread(StopScreenRecording)
            funcs.append(fun)
        else:
            pass
            # print(f"[v0] No function found for: {command}", flush=True)

    if funcs:
        results = await asyncio.gather(*funcs)
        for result in results:
            yield result


async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    return True


# if __name__ == "__main__":
#     asyncio.run(Automation(["open facebook", "open instagram"]))

