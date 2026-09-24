import os
from pathlib import Path

from dotenv import dotenv_values

try:
    import mtranslate as mt
except Exception:  # pragma: no cover - optional for browser-only mode
    mt = None


env_vars = dotenv_values(".env")
InputLanguage = (env_vars or {}).get("InputLanguage", "en")


def _build_voice_html():
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>SHADOWSpeech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''
    return str(html).replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")


def _get_browser_driver():
    """Lazy-load Selenium so Flask startup does not spawn a local ChromeDriver process."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except Exception as exc:  # pragma: no cover - optional desktop feature
        raise RuntimeError("Desktop speech capture requires Selenium + ChromeDriver, which is not available in the Render web environment.") from exc

    current_dir = os.getcwd()
    Path("Data").mkdir(exist_ok=True)
    html_path = Path(current_dir) / "Data" / "Voice.html"
    html_path.write_text(_build_voice_html(), encoding="utf-8")

    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--use-fake-ui-for-media-stream")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver, By, html_path


def SetAssistantStatus(Status):
    temp_dir = Path(os.getcwd()) / "Frontend" / "Files"
    temp_dir.mkdir(parents=True, exist_ok=True)
    astra_status = f"[Astra] {Status}"
    (temp_dir / "Status.data").write_text(astra_status, encoding="utf-8")


def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()


def UniversalTranslator(Text):
    if mt is None:
        return Text
    return mt.translate(Text, "en", "auto")


def SpeechRecognition():
    driver, By, html_path = _get_browser_driver()
    driver.get("file:///" + str(html_path))
    driver.find_element(by=By.ID, value="start").click()

    while True:
        try:
            text = driver.find_element(by=By.ID, value="output").text
            if text:
                driver.find_element(by=By.ID, value="end").click()
                if str(InputLanguage).lower() == "en" or "en" in str(InputLanguage).lower():
                    return QueryModifier(text)
                SetAssistantStatus("Translating...")
                return QueryModifier(UniversalTranslator(text))
        except Exception:
            pass


if __name__ == "__main__":
    while True:
        text = SpeechRecognition()
        print(text)