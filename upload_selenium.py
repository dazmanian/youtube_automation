import sqlite3
import os
import time
import pyperclip
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
    # MODIFICARE: Căutăm 'pending' (așa le pune generatorul)
    cursor.execute("SELECT * FROM videos WHERE status='pending' ORDER BY RANDOM() LIMIT 1")
    video = cursor.fetchone()
    conn.close()
    return video

def mark_as_uploaded(video_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET status='uploaded', uploaded_at=CURRENT_TIMESTAMP WHERE id=?", (video_id,))
    conn.commit()
    conn.close()
    print(f"✅ [DB]: Video ID {video_id} marcat ca UPLOADED.")

def mark_as_error(video_id, eroare):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Încercăm să scriem și logul
    try:
        cursor.execute("UPDATE videos SET status='error', error_log=? WHERE id=?", (str(eroare), video_id))
    except:
        cursor.execute("UPDATE videos SET status='error' WHERE id=?", (video_id,))
    conn.commit()
    conn.close()
    print(f"❌ [DB]: Video ID {video_id} marcat cu EROARE.")
   
def force_write(driver, element_xpath, text, field_name="Necunoscut"):
    """Metoda ta robustă de scriere via JS"""
    try:
        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, element_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)
        # Curățare înainte de scriere
        driver.execute_script("arguments[0].innerText = '';", element) 
        driver.execute_script("arguments[0].innerText = arguments[1];", element, text)
        time.sleep(0.5)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
        print(f"✅ [{field_name}]: Scris OK via JS.")
        return True
    except Exception:
        return False

def upload_selenium():
    video_data = get_video_ready()
    
    if not video_data:
        print("💤 [DATABASE]: Nu sunt videoclipuri 'pending' în coadă.")
        return

    print(f"🎯 [DATABASE]: Procesez ID: {video_data['id']} - {video_data['titlu_video']}")
    cale_video = os.path.abspath(video_data['cale_fisier'])
    
    if not os.path.exists(cale_video):
        print(f"❌ [EROARE]: Fișierul nu există fizic: {cale_video}")
        mark_as_error(video_data['id'], "Fisier lipsa pe disk")
        return
    
    # --- PRELUARE DATE DIN BAZĂ (AICI E SCHIMBAREA) ---
    # Nu mai generăm descrierea, o luăm pe cea gata făcută!
    titlu_final = video_data['titlu_video']
    descriere_finala = video_data['descriere'] # <--- Asta vine din Generator

    # Fallback dacă descrierea e goală (siguranță)
    if not descriere_finala:
        descriere_finala = f"{titlu_final} #shorts"

    # --- CONFIGURARE CHROME ---
    options = Options()
    options.add_argument(f"--user-data-dir={PATH_PROFILE}")
    # options.add_argument(f"--profile-directory=Profile 1") # Decomentează dacă ai profil specific
    options.add_argument("--no-first-run")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    print(f"🤖 [SELENIUM]: Deschid Chrome...")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"❌ [CRASH INITIAL]: Verifică dacă ai Chrome închis! {e}")
        return

    try:
        print("⏳ [NAVIGARE]: YouTube Upload...")
        driver.get("https://studio.youtube.com")
        time.sleep(5)
        
        # Navigare către Upload (Metoda simplificată URL direct uneori nu merge la Studio, folosim butoane)
        driver.get("https://youtube.com/upload") 
        time.sleep(5)

        print(f"📂 [UPLOAD]: Trimit fișierul...")
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(cale_video)

        wait = WebDriverWait(driver, 60)
        print("⏳ [ASTEPTARE]: Aștept procesarea inițială...")
        
        # Așteptăm titlul să apară
        wait.until(EC.presence_of_element_located((By.ID, "textbox")))
        time.sleep(3)

        # --- 1. TITLU ---
        print("📝 [TITLU]: Scriem titlul...")
        # Metoda ta cu XPaths multiple e bună
        xpaths_titlu = [
            "//div[@id='title-textarea']//div[@id='textbox']",
            "(//div[@contenteditable='true'])[1]"
        ]
        
        titlu_ok = False
        for xpath in xpaths_titlu:
            if force_write(driver, xpath, titlu_final, "TITLU"):
                titlu_ok = True
                break
        
        if not titlu_ok:
            print("⚠️ Nu am putut scrie titlul via JS, încerc fallback keys...")
            box = driver.find_element(By.ID, "textbox")
            box.send_keys(Keys.CONTROL + "a")
            box.send_keys(Keys.BACKSPACE)
            box.send_keys(titlu_final)

        # --- 2. DESCRIERE (Metoda Clipboard - Cea mai bună pentru Emojis) ---
        print("📝 [DESCRIERE]: Scriem descrierea...")
        
        # Identificăm boxa de descriere (de obicei a doua cutie editabilă)
        boxes = driver.find_elements(By.ID, "textbox")
        if len(boxes) > 1:
            desc_box = boxes[1]
            desc_box.click()
            time.sleep(1)
            
            # Curățare
            desc_box.send_keys(Keys.CONTROL + "a")
            desc_box.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            
            # PASTE din baza de date
            pyperclip.copy(descriere_finala)
            desc_box.send_keys(Keys.CONTROL + "v")
            print("✅ [DESCRIERE]: Paste efectuat!")
        else:
            print("⚠️ Nu găsesc căsuța de descriere!")

        time.sleep(2)

        # --- 3. NOT FOR KIDS ---
        print("👶 [SETARI]: Not for kids...")
        try:
            driver.find_element(By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MADE_FOR_KIDS").click()
        except:
            pass # Uneori e selectat deja

        # --- NEXT, NEXT, NEXT ---
        print("➡️ [NAVIGARE]: Next x3...")
        for i in range(3):
            try:
                driver.find_element(By.ID, "next-button").click()
                time.sleep(2)
            except: pass

        # --- PUBLIC ---
        print("🌍 [PUBLICARE]: Public...")
        try:
            public_btn = driver.find_element(By.NAME, "PUBLIC")
            driver.execute_script("arguments[0].click();", public_btn)
        except:
            # Fallback XPath
            driver.find_element(By.XPATH, "//*[@name='PUBLIC']").click()
            
        time.sleep(2)
        
        # --- DONE ---
        print("🚀 [LANSARE]: DONE!")
        done_btn = driver.find_element(By.ID, "done-button")
        done_btn.click()
        
        # Așteptăm confirmarea
        time.sleep(5)
        
        print("✅ [SUCCES]: Video a fost trimis!")
        mark_as_uploaded(video_data['id'])

    except Exception as e:
        print(f"\n❌ [EROARE FATALĂ]: {e}")
        mark_as_error(video_data['id'], str(e))
        
    finally:
        print("👋 Închid în 5 secunde...")
        time.sleep(5)
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    upload_selenium()