import os
import time
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear_screen()
    print("╔════════════════════════════════════════╗")
    print("║   🚀 YOUTUBE EMPIRE AUTOMATION V2.0    ║")
    print("║        (Miliardar Mode Active)         ║")
    print("╚════════════════════════════════════════╝")

def main_menu():
    while True:
        banner()
        print("\n🎛️  PANOU DE CONTROL:")
        print("1. 📥 [DOWNLOADER]: Descarcă video brut")
        print("2. 🏭 [GENERATOR]:  Crează 5 variante (Split/AI/Text)")
        print("3. 🚀 [UPLOADER]:   Postează pe YouTube")
        print("4. 📊 [DATABASE]:   Vezi Statistici & Coada")
        print("5. ❌ Ieșire")
        
        choice = input("\nComanda ta > ")
        
        if choice == "1":
            print("\n🚀 Pornesc Downloader...")
            os.system("python downloader.py")
            input("\n✅ Apasă Enter să revii la meniu...")
            
        elif choice == "2":
            print("\n🏭 Pornesc Fabrica Video...")
            os.system("python video_generator.py")
            input("\n✅ Apasă Enter să revii la meniu...")
            
        elif choice == "3":
            print("\n🌍 Pornesc Distribuția (Upload)...")
            # Atenționare pentru Chrome
            print("⚠️ ATENȚIE: Închide toate ferestrele Chrome înainte să continui!")
            input("Apasă Enter dacă ai închis Chrome...")
            os.system("python upload_selenium.py")
            input("\n✅ Apasă Enter să revii la meniu...")

        elif choice == "4":
            os.system("python database.py")
            
        elif choice == "5":
            print("Succes, CEO! 👋")
            break
        else:
            print("Comandă invalidă.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()