import os
import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from components.auth_manager import get_cookies_by_id, apply_cookies_to_driver, check_logged_in_via_driver, generate_review_key, get_current_reporter_email_key
from utils.helpers import classify_report_category
from utils.constants import HISTORY_FILE, SUBMITTED_LOG_FILE, REPORT_CATEGORIES, REPORT_FILE
import json
from selenium.webdriver.common.action_chains import ActionChains
import random

# --- Fungsi Persistensi JSON ---
def load_report_history():
    """Memuat riwayat laporan dari file JSON (Permanen, kunci: Email)."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Gagal memuat history: File JSON rusak. Membuat history baru.")
            return {}
    return {}

def save_report_history(history):
    """Menyimpan riwayat laporan ke file JSON (Permanen)."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4, sort_keys=True)
    except IOError as e:
        print(f"❌ Gagal menyimpan history: {e}")

def load_submitted_log():
    """Memuat log laporan yang sudah disubmit untuk tampilan UI."""
    if os.path.exists(SUBMITTED_LOG_FILE):
        try:
            with open(SUBMITTED_LOG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Gagal memuat submitted log: File JSON rusak.")
            return []
    return []

def save_submitted_log(log):
    """Menyimpan log laporan yang sudah disubmit."""
    try:
        with open(SUBMITTED_LOG_FILE, 'w') as f:
            json.dump(log, f, indent=4)
    except IOError as e:
        print(f"❌ Gagal menyimpan submitted log: {e}")

def already_reported_by_current_user(review_data, reporter_email_key):
    """
    Memeriksa apakah review tertentu sudah dilaporkan oleh akun reporter aktif.

    Args:
        review_data (dict/pd.Series): Data review dari DataFrame.
        reporter_email_key (str): Email akun reporter yang sedang aktif.

    Returns:
        bool: True jika sudah dilaporkan oleh akun ini, False jika belum.
    """
    if not reporter_email_key:
        return False

    review_key = generate_review_key(review_data)
    report_history = load_report_history()
    
    # Cek apakah email reporter ada di history, dan apakah review_key ada di log email tersebut
    return (
        reporter_email_key in report_history and
        review_key in report_history[reporter_email_key]
    )


def auto_report_review(row, report_type=None):
    user_id_to_report = st.session_state.report_user_id
    user_data = get_cookies_by_id(user_id_to_report)
    
    if not user_data:
        st.error("Tidak ada akun yang dipilih atau cookies report tidak ditemukan!")
        return
    
    cookies = user_data["cookies"]
    report_email = user_data.get("email", user_id_to_report)
    reporter_email_key = get_current_reporter_email_key() # Kunci permanen untuk history

    # Inisialisasi Options untuk uc
    options = uc.ChromeOptions()
# 1. Opsi Bahasa (Memaksa ke English untuk Konsistensi Locator)
    options.add_argument("--lang=en-US")
    options.add_argument("--accept-lang=en-US,en;q=0.9") 
    
    # 2. Opsi Stabilitas dan Efisiensi (Penambahan Anda)
    
    # Menonaktifkan ekstensi dan pop-up (mengurangi beban)
    options.add_argument("--disable-extensions") 
    options.add_argument("--disable-popup-blocking")
    
    # Mengurangi penggunaan GPU rendering (sering menyebabkan Stacktrace pada server headless)
    options.add_argument("--disable-gpu") 
    
    #options.add_argument("--start-maximized") # Tetap pertahankan ini untuk kompatibilitas
    options.add_argument("--window-size=1200,800")
    options.add_argument("--window-position=-1800,0")

    
    # 3. Opsi Undetected-Chromedriver & Security (Wajib)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") # Penting untuk lingkungan Linux/Docker
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows") # <-- Tambahkan ini
    options.add_argument("--force-device-scale-factor=1") # <-- Tambahkan ini untuk konsistensi UI

    try:
        # Gunakan undetected-chromedriver
        driver = uc.Chrome(options=options)
    except Exception as e:
        st.error(f"❌ Gagal inisialisasi Undetected-Chromedriver: {e}")
        return
        
    
    try:
        apply_cookies_to_driver(driver, cookies)
        # Jeda acak untuk apply cookies
        time.sleep(random.uniform(1, 3))
        driver.get("https://www.google.com/maps")
        if not check_logged_in_via_driver(driver, timeout=3):
            st.warning(f"Invalid cookies for {report_email} — login may need to be repeated")
        else:
            st.info(f"Reporting using an account: **{report_email}**")
    except Exception as e:
        st.warning(f"Fail apply cookies or initial navigation for report user: {e}")
        driver.quit()
        return

    try:
        if not report_type:
            category, _ = classify_report_category(row["Review Text"])
            report_type = category if category in REPORT_CATEGORIES else REPORT_CATEGORIES[-1]

        gmaps_link_for_report = st.session_state.gmaps_link_input

        try:
            if gmaps_link_for_report and gmaps_link_for_report.strip():
                driver.get(gmaps_link_for_report.strip())
            else:
                search_url = f"https://www.google.com/maps/search/{row['Place'].replace(' ', '+')}"
                driver.get(search_url)
        except Exception as e:
            st.warning(f"Gagal membuka link Google Maps: {e}")

        time.sleep(random.uniform(1, 3)) # Jeda acak yang lebih panjang untuk loading halaman

        try:
            tab = driver.find_element(By.XPATH, "//button[contains(., 'Reviews') or contains(., 'Ulasan')]")
            ActionChains(driver).move_to_element(tab).click().perform() 
            time.sleep(random.uniform(1, 3)) # Jeda yang diperpanjang
        except Exception:
            st.error("tidak bisa buka tab review")
            driver.quit()
            return

        # urutkan peringkat terendah
        try:
            sort_button = driver.find_element(By.XPATH, "//button[contains(., 'Sort') or contains(., 'Urutkan')]")
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(random.uniform(1, 3))
            lowest = driver.find_elements(By.XPATH, "//*[contains(text(), 'Lowest rating') or contains(text(), 'Peringkat terendah')]")
            for opt in lowest:
                try:
                    driver.execute_script("arguments[0].click();", opt)
                    break
                except:
                    continue
            time.sleep(random.uniform(1, 3))
        except Exception:
            pass

        users = []
        target = None
        
        # --- Logika Scroll dan Pencarian Dioptimalkan ---
# --- Logika Scroll dan Pencarian Dioptimalkan ---
        try:
            scroll_area = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'m6QErb') and contains(@class,'DxyBCb')]"))
            )
            target = None
            scroll_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
            

            # Loop hingga target ditemukan atau mencapai batas scroll
            for i in range(500):
                users = driver.find_elements(By.CSS_SELECTOR, ".d4r55")
                for u in users:
                    if row["User"].lower() in u.text.lower():
                        target = u
                        break 
                
                if target:
                    break

                current_scroll_pos = driver.execute_script("return arguments[0].scrollTop", scroll_area)
                
                # ✅ PERBAIKAN: Konversi ke Integer secara eksplisit
                current_scroll_pos_int = int(current_scroll_pos) # Pastikan current_scroll_pos adalah integer
                
                # Scroll dalam langkah kecil (lebih manusiawi)
                new_scroll_pos_int = current_scroll_pos_int + 400 
                
                # ✅ PERBAIKAN: Gunakan nilai integer yang sudah dikonversi
                for step in range(current_scroll_pos_int, new_scroll_pos_int, 100): # 50px per langkah
                    driver.execute_script(f"arguments[0].scrollTop = {step}", scroll_area)
                    time.sleep(0.3) # Jeda per langkah scroll ditingkatkan sedikit
                
                # ... (Logika pengecekan scroll_height dan break tetap sama)
                new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
                
                # Perlu diingat, scroll_height juga bisa jadi float, sebaiknya konversi di sini juga
                if int(new_scroll_height) == int(scroll_height) and new_scroll_pos_int >= int(new_scroll_height):
                    break
                
                scroll_height = new_scroll_height
                
            if not target:
                st.info(f"User {row['User']} not found.")

        except Exception as e:
            # Error ini seharusnya sudah tidak muncul lagi dengan perbaikan di atas
            st.error(f"Terjadi error saat scrolling atau pencarian: {e}") 
        # --- Akhir Logika Scroll dan Pencarian Dioptimalkan ---

        
        
        if not target:
            st.warning(f"❌ User {row['User']} not found")
            driver.quit()
            return

        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", target)
        time.sleep(random.uniform(1, 3))

        # klik titik tiga
        try:
            menu_el = target.find_element(By.XPATH, "./ancestor::div[contains(@class,'jftiEf')]//div[@class='zjA77']")
            ActionChains(driver).move_to_element(menu_el).click().perform()
            time.sleep(random.uniform(1, 3))
        except Exception:
            driver.quit()
            return

        js_click_report = """
        const keywords = ['Report review','Laporkan ulasan','Report','Laporkan'];
        let found = false;
        document.querySelectorAll('*').forEach(el => {
            const txt = (el.innerText || '').trim();
            if (keywords.some(k => txt.includes(k))) {
                try { el.click(); found = true } catch(e) {}
            }
        });
        return found;
        """
        clicked = driver.execute_script(js_click_report)
        if not clicked:
            driver.quit()
            return

        st.toast(f"✅ click ‘report review’ to {row['User']}")
        time.sleep(random.uniform(3, 4)) # Jeda diperpanjang sebelum klik kategori

        tabs = driver.window_handles
        if len(tabs) > 1:
            driver.switch_to.window(tabs[-1])
        else:
            st.warning("⚠️ New tab not detected, popup may be in iframe")

        # ... (Logika klik kategori tidak berubah, tetapi disarankan mengganti JS sleep di dalamnya) ...
        js_click_category = f"""
        const reportType = "{report_type}".toLowerCase().trim();

        let category_map = {{
            // --- Kategori Konsisten ---
            "profanity": ["profanity"],
            "bullying or harassment": ["bullying or harassment"],
            "discrimination or hate speech": ["discrimination or hate speech"],
            
            // --- Kategori Fleksibel ---
            "off topic": ["off topic", "low quality information"], 
            "conflict of interest": ["conflict of interest", "fake or deceptive"], 
            
            "harmful": ["harmful"], 
            "personal information": ["personal information"],
            "not helpful": ["not helpful"] 
        }};

        // Dapatkan semua kemungkinan target dari category_map
        const targets = category_map[reportType] || [reportType];

        function sleep(ms) {{
            return new Promise(resolve => setTimeout(resolve, ms));
        }}

        
        function highlight(el) {{
        el.style.transition = "all 0.3s ease";
        el.style.border = "3px solid red";
        el.style.backgroundColor = "yellow";
        el.scrollIntoView({{behavior:'smooth', block:'center'}});
        }}

        function simulateClick(el) {{
        ['pointerdown','mousedown','mouseup','click'].forEach(evt => {{
            el.dispatchEvent(new MouseEvent(evt, {{ bubbles: true, cancelable: true, view: window }}));
        }});
        }}

        async function runCategoryClick(doc) {{
        const candidates = doc.querySelectorAll('[role="button"], div[role="link"], a, div');

        for (let el of candidates) {{
            let text = (el.innerText || "").toLowerCase().trim();

            // Cek apakah teks mengandung salah satu target
            const isMatch = targets.some(target => text.includes(target));

            // pastikan elemennya hanya mengandung satu kategori, bukan seluruh popup
            if (isMatch && text.length < 60) {{
                highlight(el);
                await sleep(3000); // delay 3 detik
                simulateClick(el);
                return "✅ Clicked category: " + text + " (Matched target: " + targets.find(target => text.includes(target)) + ")";
            }}
        }}
        return null;
        }}

        async function start() {{
        let res = await runCategoryClick(document);
        if (res) return res;

        // cek iframe jika ada
        for (let frame of document.querySelectorAll('iframe')) {{
            try {{
            let doc = frame.contentDocument || frame.contentWindow.document;
            res = await runCategoryClick(doc);
            if (res) return res + " (inside iframe)";
            }} catch(e) {{
            continue;
            }}
        }}
        return "⚠️ Category not found. Searched targets: " + targets.join(", ");
        }}

        return await start();
        """


        res_cat = driver.execute_script(js_click_category)
        
        if not res_cat.startswith("✅"):
            st.warning(res_cat)
            driver.quit()
            return

        time.sleep(random.uniform(1, 3)) # Jeda panjang setelah memilih kategori

        # --- KLIK FINAL MENGGUNAKAN ACTIONCHAINS ---
        try:
            # Tunggu tombol submit muncul (menggunakan XPath umum)
            submit_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(., 'Submit') or contains(., 'Laporkan') or contains(., 'Kirim') or contains(., 'Report') or contains(., 'Done') or contains(., 'Selesai')]"))
            )
        except Exception as e:
            st.error(f"❌ Tombol Submit tidak ditemukan. Error: {e}")
            driver.quit()
            return
            
        ActionChains(driver).move_to_element(submit_button).perform() 
        time.sleep(random.uniform(1, 3)) # Jeda manusiawi sebelum klik
        ActionChains(driver).click().perform()

        # --- TUNGGU RESPON SERVER (TITIK KRITIS: JEDA EKSTREM) ---
        res_submit = ""
        # Kita tunggu antara 15 hingga 25 detik untuk memberi waktu Google memproses dan merespons.
        time.sleep(random.uniform(1, 3)) 
        
 # 6. Pengecekan Status Sukses/Gagal
        res_submit = "⚠️ UNKNOWN"
        try:
            # Pengecekan konfirmasi sukses
            WebDriverWait(driver, 3).until( 
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Report received') or contains(text(), 'Laporan diterima')]"))
            )
            res_submit = "✅ SUCCESS" 
            
        except Exception:
            # Pengecekan kegagalan server/URL
            if "error=1" in driver.current_url or "Your report wasn't submitted" in driver.page_source:
                res_submit = "❌ SERVER REJECTED"
            else:
                res_submit = "⚠️ UNKNOWN"

        # 7. LOGGING HANYA JIKA SUKSES
        if res_submit == "✅ SUCCESS":
            
            reporter_email = reporter_email_key
            
            # ⚠️ Memastikan kolom 'Place' ada, atau set dari session state
            if 'Place' not in row or not row['Place']:
                row['Place'] = st.session_state.get('place_name', 'Unknown Place')
            
            # Gunakan generate_review_key dengan format string yang Anda minta
            review_key = generate_review_key(row)

            
            # a. Update Report History (Per-Akun)
            history = load_report_history()
            if reporter_email not in history:
                history[reporter_email] = {}
                
            history[reporter_email][review_key] = { 
                'Reported Time': time.strftime("%Y-%m-%d %H:%M:%S"),
                'Category': report_type
            }
            save_report_history(history)
            
            # b. Update Submitted Log (Global/Visual)
            submitted_log = load_submitted_log()
            log_entry = {
                "Place": row["Place"],
                "User": row["User"],
                "Review Text": row["Review Text"],
                "Date": row["Date (Parsed)"],
                "Kategori Report": report_type,
                "Reported By": reporter_email,
                "Review Key": review_key,
                'Reported Time': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            submitted_log.append(log_entry)
            save_submitted_log(submitted_log)

            # Update Streamlit session state (penting agar UI di main.py terupdate)
            st.session_state.report_history = history
            st.session_state["reported"] = submitted_log

            # Return success
            return f"✅ Review dari {row['User']} dilaporkan oleh {reporter_email_key}."
            
        else:
            # Jika gagal/UNKNOWN, raise Exception untuk ditangkap di main.py
            raise Exception(f"Submit Failed. Status: {res_submit}")

    except Exception as e:
        # Jika ada error Selenium atau exception lain
        raise Exception(f"Failed to submit report for {row['User']}. Error: {e}")
        
    finally:
        try:
            driver.quit()
        except:
            pass # Pastikan driver ditutup