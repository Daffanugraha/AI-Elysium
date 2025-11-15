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
from components.auth_manager import get_cookies_by_id, apply_cookies_to_driver, check_logged_in_via_driver
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


def auto_report_review(row, report_type=None):
    user_id_to_report = st.session_state.report_user_id
    user_data = get_cookies_by_id(user_id_to_report)
    
    if not user_data:
        st.error("Tidak ada akun yang dipilih atau cookies report tidak ditemukan!")
        return
    
    cookies = user_data["cookies"]
    report_email = user_data.get("email", user_id_to_report)

    # Inisialisasi Options untuk uc
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    try:
        # Gunakan undetected-chromedriver
        driver = uc.Chrome(options=options)
    except Exception as e:
        st.error(f"❌ Gagal inisialisasi Undetected-Chromedriver: {e}")
        return
    
    try:
        apply_cookies_to_driver(driver, cookies)
        # Jeda acak untuk apply cookies
        time.sleep(random.uniform(3, 5))
        driver.get("https://www.google.com/maps")
        if not check_logged_in_via_driver(driver, timeout=5):
            st.warning(f"Invalid cookies for {report_email} — login may need to be repeated")
        else:
            st.info(f"Reporting menggunakan akun: **{report_email}**")
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

        time.sleep(random.uniform(4, 7)) # Jeda acak yang lebih panjang untuk loading halaman

        try:
            tab = driver.find_element(By.XPATH, "//button[contains(., 'Reviews') or contains(., 'Ulasan')]")
            ActionChains(driver).move_to_element(tab).click().perform() 
            time.sleep(random.uniform(3, 5)) # Jeda yang diperpanjang
        except Exception:
            st.error("tidak bisa buka tab review")
            driver.quit()
            return

        # urutkan peringkat terendah
        try:
            sort_button = driver.find_element(By.XPATH, "//button[contains(., 'Sort') or contains(., 'Urutkan')]")
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(random.uniform(1, 2))
            lowest = driver.find_elements(By.XPATH, "//*[contains(text(), 'Lowest rating') or contains(text(), 'Peringkat terendah')]")
            for opt in lowest:
                try:
                    driver.execute_script("arguments[0].click();", opt)
                    break
                except:
                    continue
            time.sleep(random.uniform(1, 2))
        except Exception:
            pass

        users = []
        target = None
        
        # --- Logika Scroll dan Pencarian Dioptimalkan ---
        try:
            scroll_area = driver.find_element(By.XPATH, "//div[contains(@class,'m6QErb') and contains(@class,'DxyBCb')]")
            target = None
            scroll_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
            

            # Loop hingga target ditemukan atau mencapai batas scroll
            for i in range(500): # Ditingkatkan hingga 100 iterasi
                users = driver.find_elements(By.CSS_SELECTOR, ".d4r55")
                for u in users:
                    if row["User"].lower() in u.text.lower():
                        target = u
                        break 
                
                if target:
                    break

                current_scroll_pos = driver.execute_script("return arguments[0].scrollTop", scroll_area)
                
                # Scroll dalam langkah kecil (lebih manusiawi)
                new_scroll_pos = current_scroll_pos + 400 
                for step in range(current_scroll_pos, new_scroll_pos, 50): # 50px per langkah
                    driver.execute_script(f"arguments[0].scrollTop = {step}", scroll_area)
                    time.sleep(0.08) # Jeda per langkah scroll ditingkatkan sedikit
                

                new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
                
                if new_scroll_height == scroll_height and new_scroll_pos >= new_scroll_height:
                    break
                
                scroll_height = new_scroll_height
                
            if not target:
                st.info(f"User {row['User']} not found.")

        except Exception as e:
            st.error(f"Terjadi error saat scrolling atau pencarian: {e}")
        # --- Akhir Logika Scroll dan Pencarian Dioptimalkan ---
        
        
        if not target:
            st.warning(f"❌ User {row['User']} not found")
            driver.quit()
            return

        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", target)
        time.sleep(random.uniform(1, 2))

        # klik titik tiga
        try:
            menu_el = target.find_element(By.XPATH, "./ancestor::div[contains(@class,'jftiEf')]//div[@class='zjA77']")
            ActionChains(driver).move_to_element(menu_el).click().perform()
            time.sleep(random.uniform(2, 3))
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
        time.sleep(random.uniform(3, 5)) # Jeda diperpanjang sebelum klik kategori

        tabs = driver.window_handles
        if len(tabs) > 1:
            driver.switch_to.window(tabs[-1])
        else:
            st.warning("⚠️ New tab not detected, popup may be in iframe")

        # ... (Logika klik kategori tidak berubah, tetapi disarankan mengganti JS sleep di dalamnya) ...
        js_click_category = f"""
        const target = "{report_type}".toLowerCase().trim();

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

            // pastikan elemennya hanya mengandung satu kategori, bukan seluruh popup
            if (text.includes(target) && text.length < 60) {{
            highlight(el);
            await sleep(3000); // delay 3 detik
            simulateClick(el);
            return "✅ Clicked category: " + text;
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
        return "⚠️ Category not found: " + target;
        }}

        return await start();
        """
        res_cat = driver.execute_script(js_click_category)
        
        if not res_cat.startswith("✅"):
            st.warning(res_cat)
            driver.quit()
            return

        time.sleep(random.uniform(4, 7)) # Jeda panjang setelah memilih kategori

        # --- KLIK FINAL MENGGUNAKAN ACTIONCHAINS ---
        try:
            # Tunggu tombol submit muncul (menggunakan XPath umum)
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(., 'Submit') or contains(., 'Laporkan') or contains(., 'Kirim') or contains(., 'Report') or contains(., 'Done') or contains(., 'Selesai')]"))
            )
            st.info("✅ Siap klik tombol submit")
        except Exception as e:
            st.error(f"❌ Tombol Submit tidak ditemukan. Error: {e}")
            driver.quit()
            return
            
        ActionChains(driver).move_to_element(submit_button).perform() 
        time.sleep(random.uniform(2, 4)) # Jeda manusiawi sebelum klik
        ActionChains(driver).click().perform()

        # --- TUNGGU RESPON SERVER (TITIK KRITIS: JEDA EKSTREM) ---
        res_submit = ""
        # Kita tunggu antara 15 hingga 25 detik untuk memberi waktu Google memproses dan merespons.
        time.sleep(random.uniform(8, 15)) 
        
        # --- Cek hasil ---
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Report received') or contains(text(), 'Laporan diterima')]"))
            )
            st.success("✅ LAPORAN BERHASIL DITERIMA OLEH GOOGLE! (Report received)")
            res_submit = "✅ SUCCESS"
        except:
            if "error=1" in driver.current_url or "Your report wasn't submitted" in driver.page_source:
                st.error("❌ Submit berhasil diklik, TAPI SERVER GOOGLE MENOLAK (Something went wrong).")
                res_submit = "❌ SERVER REJECTED"
            else:
                st.warning("⚠️ Klik Submit berhasil, TAPI status tidak diketahui.")
                res_submit = "⚠️ UNKNOWN"


        if res_submit.startswith("✅"):
            reporter_email = report_email
            if "report_history" not in st.session_state:
                st.session_state.report_history = load_report_history()
            if "reported" not in st.session_state:
                st.session_state["reported"] = load_submitted_log()

            review_key = f"{row.get('Place','')}|{row.get('User','')}|{row.get('Date (Parsed)','')}"

            if reporter_email not in st.session_state.report_history:
                st.session_state.report_history[reporter_email] = {}
            
            st.session_state.report_history[reporter_email][review_key] = True 
            save_report_history(st.session_state.report_history)

            log_entry = {
                "Place": row["Place"],
                "User": row["User"],
                "Review Text": row["Review Text"],
                "Date": row["Date (Parsed)"],
                "Kategori Report": report_type,
                "Reported By": reporter_email
            }
            st.session_state["reported"].append(log_entry)
            save_submitted_log(st.session_state["reported"])
        else:
            st.warning(res_submit or "Submit failed.")

    finally:
        try:
            driver.quit()
        except:
            pass