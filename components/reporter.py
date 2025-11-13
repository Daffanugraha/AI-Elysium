# components/reporter.py
import os
import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from components.auth_manager import get_cookies_by_id, apply_cookies_to_driver, check_logged_in_via_driver
from utils.helpers import classify_report_category
from utils.constants import HISTORY_FILE, SUBMITTED_LOG_FILE, REPORT_CATEGORIES, REPORT_FILE
import json


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
    # Ambil cookies dari user yang sedang dipilih untuk report
    user_id_to_report = st.session_state.report_user_id
    user_data = get_cookies_by_id(user_id_to_report)
    
    if not user_data:
        st.error("Tidak ada akun yang dipilih atau cookies report tidak ditemukan!")
        return
    
    cookies = user_data["cookies"]
    report_email = user_data.get("email", user_id_to_report)

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        apply_cookies_to_driver(driver, cookies)
        time.sleep(2)
        driver.get("https://www.google.com/maps")
        if not check_logged_in_via_driver(driver, timeout=5):
            st.warning(f"Invalid cookies for {report_email} — login may need to be repeated")
        else:
            st.info(f"Reporting menggunakan akun: **{report_email}**")
    except Exception as e:
        st.warning(f"Fail apply cookies for report user: {e}")
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

        time.sleep(3)

        try:
            tab = driver.find_element(By.XPATH, "//button[contains(., 'Reviews') or contains(., 'Ulasan')]")
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(2)
        except Exception:
            st.error("tidak bisa buka tab review")
            driver.quit()
            return

        # urutkan peringkat terendah
        try:
            sort_button = driver.find_element(By.XPATH, "//button[contains(., 'Sort') or contains(., 'Urutkan')]")
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(1)
            lowest = driver.find_elements(By.XPATH, "//*[contains(text(), 'Lowest rating') or contains(text(), 'Peringkat terendah')]")
            for opt in lowest:
                try:
                    driver.execute_script("arguments[0].click();", opt)
                    break
                except:
                    continue
            time.sleep(1)
        except Exception:
            pass

        users = []
        target = None
        
        # --- Logika Scroll dan Pencarian Dioptimalkan ---
        try:
            # Elemen area scroll
            scroll_area = driver.find_element(By.XPATH, "//div[contains(@class,'m6QErb') and contains(@class,'DxyBCb')]")
            target = None
            
            # Dapatkan tinggi area scroll saat ini
            scroll_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
            

            # Loop maksimum 50 kali atau sampai target ditemukan
            for i in range(50): 
                # 1. Coba cari target di ulasan yang sudah termuat
                users = driver.find_elements(By.CSS_SELECTOR, ".d4r55")
                for u in users:
                    # Mencocokkan nama user
                    if row["User"].lower() in u.text.lower():
                        target = u
                        break 
                
                if target:
                    break # Target ditemukan, berhenti total scrolling

                current_scroll_pos = driver.execute_script("return arguments[0].scrollTop", scroll_area)
                
                new_scroll_pos = current_scroll_pos + 500 # Jumlah piksel per langkah scroll (bisa disesuaikan)
                
                for step in range(current_scroll_pos, new_scroll_pos, 100): 
                    driver.execute_script(f"arguments[0].scrollTop = {step}", scroll_area)
                    time.sleep(0.05) # Penundaan sangat singkat (50ms) untuk efek animasi
                

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
        time.sleep(1)

        # klik titik tiga
        try:
            menu_el = target.find_element(By.XPATH, "./ancestor::div[contains(@class,'jftiEf')]//div[@class='zjA77']")
            driver.execute_script("arguments[0].click();", menu_el)
            time.sleep(2)
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
        time.sleep(2)

        tabs = driver.window_handles
        if len(tabs) > 1:
            driver.switch_to.window(tabs[-1])
        else:
            st.warning("⚠️ New tab not detected, popup may be in iframe")

        try:
            WebDriverWait(driver,2).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='dialog' or contains(@class,'popup') or contains(@class,'overlay')]")
                )
            )
            st.info("✅ Popup dialog terdeteksi")
        except:
            time.sleep(1)
        
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
        if res_cat.startswith("✅"):
            st.success(res_cat)
        else:
            st.warning(res_cat)
            with open("last_report_popup_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

        # --- klik tombol submit ---
        # --- tunggu popup muncul sebelum klik submit ---
        try:
            WebDriverWait(driver,2).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='dialog' or contains(@class,'popup') or contains(@class,'overlay')]")
                )
            )
            st.info("✅ Popup dialog terdeteksi, siap klik tombol submit")
        except:
            time.sleep(1)

        # --- klik tombol submit / laporkan ---
        js_click_submit = """
        async function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        function highlight(el) {
            el.style.transition = "all 0.3s ease";
            el.style.border = "3px solid red";
            el.style.backgroundColor = "yellow";
            el.scrollIntoView({behavior:'smooth', block:'center'});
        }

        function simulateClick(el) {
            ['pointerdown','mousedown','mouseup','click'].forEach(evt => {
                el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
            });
        }

        async function findAndClickSubmit(root) {
            const keywords = ['submit', 'laporkan', 'send', 'report', 'kirim', 'done', 'selesai'];
            const selectors = [
                'button',
                'div[role="button"]',
                '.VfPpkd-LgbsSe',
                '.VfPpkd-dgl2Hf-ppHlrf-sM5MNb',
                '.VfPpkd-LgbsSe-OWXEXe',
                '.VfPpkd-LgbsSe-OWXEXe-nzrxxc'
            ];

            for (const sel of selectors) {
                const els = root.querySelectorAll(sel);
                for (const el of els) {
                    const txt = (el.innerText || el.ariaLabel || '').toLowerCase().trim();
                    if (keywords.some(k => txt.includes(k))) {
                        highlight(el);
                        await sleep(1000);

                        // --- klik ala user sungguhan ---
                        el.focus();
                        simulateClick(el);

                        // --- coba panggil form handler kalau ada ---
                        const form = el.closest('form');
                        if (form) {
                            try { form.requestSubmit ? form.requestSubmit() : form.submit(); } catch(e) {}
                        }

                        // --- trigger tambahan untuk Google ripple handler ---
                        el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }));
                        el.dispatchEvent(new Event('click', { bubbles: true }));
                        
                        await sleep(3500);
                    }
                }
            }

            // recursive shadowRoot
            for (const el of root.querySelectorAll('*')) {
                if (el.shadowRoot) {
                    const res = await findAndClickSubmit(el.shadowRoot);
                    if (res) return res + " (shadowRoot)";
                }
            }

            // cek iframe
            for (const frame of root.querySelectorAll('iframe')) {
                try {
                    const doc = frame.contentDocument || frame.contentWindow.document;
                    const res = await findAndClickSubmit(doc);
                    if (res) return res + " (iframe)";
                } catch(e) {}
            }

            return null;
        }

        async function start() {
            let res = await findAndClickSubmit(document);
            if (res) return res;
            return "⚠️ Tombol submit tidak ditemukan";
        }

        return await start();
        """


        res_submit = driver.execute_script(js_click_submit)
        
        if res_submit and res_submit.startswith("✅"):
            st.success(res_submit)
            
            # Ensure report_email from earlier is used and session keys exist
            reporter_email = report_email  # reuse email obtained from user cookies
            if "report_history" not in st.session_state:
                st.session_state.report_history = load_report_history()
            if "reported" not in st.session_state:
                st.session_state["reported"] = load_submitted_log()

            # Build a stable review key to prevent duplicates
            review_key = f"{row.get('Place','')}|{row.get('User','')}|{row.get('Date (Parsed)','')}"

            # --- LOGIKA PENYIMPANAN REPORT HISTORY PERMANEN ---
            if reporter_email not in st.session_state.report_history:
                st.session_state.report_history[reporter_email] = {}
            
            st.session_state.report_history[reporter_email][review_key] = True 
            save_report_history(st.session_state.report_history) # <-- SAVE HISTORY PERMANEN

            # --- LOG SUBMITTED DENGAN DATA LENGKAP ---
            log_entry = {
                "Place": row["Place"],
                "User": row["User"],
                "Review Text": row["Review Text"],
                "Date": row["Date (Parsed)"],
                "Kategori Report": report_type,
                "Reported By": reporter_email
            }
            st.session_state["reported"].append(log_entry)
            save_submitted_log(st.session_state["reported"]) # <-- SAVE LOG SUBMITTED PERMANEN

        else:
            st.warning(res_submit or "Submit failed.")

    finally:
        try:
            driver.quit()
        except:
            pass
