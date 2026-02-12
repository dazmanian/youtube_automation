import sqlite3
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

# --- CONFIGURARE ---
DB_NAME = "youtube_empire.db"
# ⚠️ VERIFICĂ CALEA SĂ FIE CORECTĂ!
PATH_PROFILE = r"D:\youtube_automation\chrome_profiles\profile_gadgets"

def get_video_ready():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE status IN ('processed', 'ready_to_upload') ORDER BY id ASC LIMIT 1")
    video = cursor.fetchone()
    conn.close()
    return video

def mark_as_uploaded(video_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET status='uploaded', uploaded_at=CURRENT_TIMESTAMP WHERE id=?", (video_id,))
    conn.commit()
    conn.close()

def force_write(driver, element_xpath, text, field_name="Necunoscut"):
    """
    Încearcă să scrie textul într-un element dat de XPath.
    Returnează True dacă a reușit, False dacă nu.
    """
    try:
        # Așteptăm doar 5 secunde per tentativă ca să nu pierdem timpul
        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, element_xpath)))
        
        # Scroll și Focus
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)
        
        # Scriem direct via JS
        driver.execute_script("arguments[0].innerText = arguments[1];", element, text)
        time.sleep(0.5)
        
        # Activăm butonul Save
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
        
        print(f"✅ [{field_name}]: REUȘITĂ cu metoda: {element_xpath}")
        return True
    except Exception:
        # Nu printăm eroarea completă ca să nu speriem utilizatorul, doar zicem că încercăm alta
        return False

def upload_selenium():
    video_data = get_video_ready()
    
    if not video_data:
        print("💤 [DATABASE]: Nu am găsit niciun video gata de upload.")
        return

    print(f"🎯 [DATABASE]: Procesez ID: {video_data['id']} - {video_data['titlu_video']}")
    cale_video = os.path.abspath(video_data['cale_fisier'])
    
    if not os.path.exists(cale_video):
        print(f"❌ [EROARE]: Fișierul nu există: {cale_video}")
        return

    descriere = f"""{video_data['titlu_video']}

🔥 GET IT HERE:
👉 {video_data['affiliate_link']}

#shorts #gadgets #tech"""

    # --- CONFIGURARE CHROME ---
    options = Options()
    options.add_argument(f"--user-data-dir={PATH_PROFILE}")
    options.add_argument("--no-first-run")
    options.add_argument("--remote-debugging-port=9222") 
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    print(f"🤖 [SELENIUM]: Deschid Chrome...")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"❌ [CRASH INITIAL]: {e}")
        return

    try:
        print("⏳ [NAVIGARE]: YouTube Upload...")
        driver.get("https://www.youtube.com/upload")
        time.sleep(5)

        print(f"📂 [UPLOAD]: Trimit fișierul...")
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(cale_video)

        wait = WebDriverWait(driver, 60)
        print("⏳ [ASTEPTARE]: Aștept să apară formularul...")
        
        # Așteptăm orice element editabil
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[@contenteditable='true']")))
        time.sleep(3)

        # --- 1. TITLU ---
        print("📝 [TITLU]: Încerc scrierea...")
        # Lista de metode pentru TITLU
        xpaths_titlu = [
            "//div[@id='title-textarea']//div[@id='textbox']", # Oficial
            "(//div[@contenteditable='true'])[1]",             # Brut (Primul element)
            "//div[contains(@aria-label, 'Title') or contains(@aria-label, 'Titlu')]//div[@contenteditable='true']" # Semantic
        ]
        
        titlu_ok = False
        for xpath in xpaths_titlu:
            if force_write(driver, xpath, video_data['titlu_video'], "TITLU"):
                titlu_ok = True
                break
        
        if not titlu_ok:
            print("❌ EROARE CRITICĂ: Nu am reușit să scriu Titlul cu nicio metodă!")

        # --- 2. DESCRIERE ---
        print("📝 [DESCRIERE]: Încerc scrierea...")
        # Lista de metode pentru DESCRIERE
        xpaths_descriere = [
            "//div[@id='description-textarea']//div[@id='textbox']", # Oficial
            "(//div[@contenteditable='true'])[2]",                   # Brut (Al doilea element)
            "//div[contains(@aria-label, 'Tell viewers') or contains(@aria-label, 'Descriere')]//div[@contenteditable='true']" # Semantic
        ]

        desc_ok = False
        for xpath in xpaths_descriere:
            if force_write(driver, xpath, descriere, "DESCRIERE"):
                desc_ok = True
                break
        
        if not desc_ok:
            print("⚠️ ATENȚIE: Nu am putut scrie descrierea. Video va fi urcat fără descriere.")

        time.sleep(1)

        # --- SETĂRI COPII ---
        print("👶 [SETARI]: Not for kids...")
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        try:
            driver.find_element(By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK").click()
        except:
            # Fallback click
            element = driver.find_element(By.XPATH, "//*[contains(text(), 'not made for kids')]")
            driver.execute_script("arguments[0].click();", element)

        # --- NEXT x3 ---
        print("➡️ [NAVIGARE]: Next x3...")
        for i in range(3):
            btn = driver.find_element(By.ID, "next-button")
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)

        # --- PUBLIC ---
        print("🌍 [PUBLICARE]: Public...")
        public_btn = wait.until(EC.presence_of_element_located((By.NAME, "PUBLIC")))
        driver.execute_script("arguments[0].click();", public_btn)
        time.sleep(2)
        
        print("🚀 [LANSARE]: DONE!")
        done_btn = driver.find_element(By.ID, "done-button")
        driver.execute_script("arguments[0].click();", done_btn)
        
        print("⏳ [ASTEPTARE]: Confirmare upload...")
        time.sleep(5)
        
        print("✅ [SUCCES]: Video a fost trimis!")
        mark_as_uploaded(video_data['id'])

    except Exception as e:
        print(f"\n❌ [EROARE FATALĂ]: {e}")
        # Rămânem deschiși pentru debug
        while True:
            time.sleep(10)
        
    finally:
        print("👋 Închid în 5 secunde...")
        time.sleep(5)
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    upload_selenium()