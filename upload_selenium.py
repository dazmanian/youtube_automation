import sqlite3
import os
import time
from selenium import webdriver
import pyperclip
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

def salveaza_descrierea_finala(video_id, text_descriere):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET descriere=? WHERE id=?", (text_descriere, video_id))
    conn.commit()
    conn.close()
    print(f"💾 [DB]: Descrierea generată a fost salvată pentru ID {video_id}.")

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
    
    # 1. Pregătim Titlul (Scurt și Impactant)
    titlu_final = video_data['titlu_video']
    if len(titlu_final) > 90:
        titlu_final = titlu_final[:90] + "..."

    # 2. Pregătim Link-ul (Dacă nu există, punem unul generic sau de canal)
    '''
    link_afiliere = video_data['affiliate_link']
    if not link_afiliere or link_afiliere == "None":
        link_afiliere = "https://www.youtube.com/@CanalulTau" # Fallback
    '''

    # 3. CONSTRUIM DESCRIEREA "SEO BOMBER"
    # Aceasta este structura care aduce vizualizări organice
    descriere = f"""{titlu_final} 🤯

🛒 BUY HERE:
👉 {video_data['affiliate_link']}
👉 {video_data['affiliate_link']}

🌟 Why you need this gadget:
This is one of the best Amazon finds of 2026! If you love cool gadgets, tech reviews, and home hacks, this video is for you. Don't forget to subscribe for daily product hunting!

🔍 Search Tags:
#shorts #amazonfinds #gadgets #tech #musthaves #tiktokmademebuyit #giftideas #productreview

🛑 Disclaimer:
As an Amazon Associate, I earn from qualifying purchases. This helps support the channel!

🎥 Video Credit: {video_data['sursa_url']}
"""
    # --- PASUL CRUCIAL: Salvăm în DB să nu mai vedem NULL ---
    try:
        salveaza_descrierea_finala(video_data['id'], descriere)
    except Exception as e:
        print(f"⚠️ Nu am putut salva descrierea în DB, dar continuăm upload-ul: {e}")

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
        print("📝 [DESCRIERE]: Încerc scrierea prin metoda Clipboard...")
        # Lista de metode pentru DESCRIERE
        xpaths_descriere = [
           # Metoda ID-ul nou (cel mai sigur acum)
           "//ytcp-social-suggestions-textbox[@id='description-textarea']//div[@id='textbox']",
           # Metoda bazată pe rolul de accesibilitate
           "//div[@aria-label='Tell viewers about your video' or @aria-label='Descrieți videoclipul']",
           # Metoda generică de fallback
           "//div[@id='description-textarea']//div[@contenteditable='true']"
        ]

        desc_ok = False
        for xpath in xpaths_descriere:
            try:
                  # 1. Așteptăm elementul să fie gata
                  element_desc = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        
                  # 2. Click forțat pentru a activa cursorul
                  driver.execute_script("arguments[0].click();", element_desc)
                  time.sleep(1)
        
                  # 3. Curățăm ce era înainte (opțional, dar sigur)
                  element_desc.send_keys(Keys.CONTROL + 'a')
                  element_desc.send_keys(Keys.BACKSPACE)
        
                  # 4. Punem textul în Clipboard și dăm PASTE
                  pyperclip.copy(descriere) # 'descriere' este variabila ta din DB
                  time.sleep(0.5)
                  element_desc.send_keys(Keys.CONTROL + 'v')
        
                  # 5. Verificăm dacă s-a scris ceva
                  time.sleep(1.5)
                  text_introdus = element_desc.get_attribute("innerText") or ""
                  if len(text_introdus.strip()) > 5:
                       print(f"✅ [DESCRIERE]: Scrisă cu succes ({len(text_introdus)} caractere)!")
                       desc_ok = True
                       break
            except Exception as e:
                  print(f"❌ Metoda XPath a eșuat, încerc următoarea...")
                  continue
        
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