# components/auth_manager.py

import streamlit as st
import os
import pickle
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.constants import COOKIES_DIR, COOKIE_EXPIRY_MINUTES, LOGIN_TIMEOUT_SECONDS

# --- Helper Cookies ---
def get_cookie_file_path(user_id):
    """Mendapatkan path file cookie untuk user_id tertentu."""
    return os.path.join(COOKIES_DIR, f"{user_id}.pkl")

def save_cookies(cookies, user_id, email=None):
    """Menyimpan cookies ke file dan session state."""
    data = {
        "cookies": cookies,
        "timestamp": datetime.now(),
        "email": email or f"user_{user_id}",
    }
    path = get_cookie_file_path(user_id)
    with open(path, "wb") as f:
        pickle.dump(data, f)
    
    # Update session state
    st.session_state.user_cookies[user_id] = data
    st.session_state.active_user_id = user_id # Set sebagai user aktif (untuk scraping)

def load_all_cookies():
    """Memuat semua cookies dari disk ke session state, menghapus yang kadaluarsa."""
    if "user_cookies" not in st.session_state:
        st.session_state.user_cookies = {}
    if "active_user_id" not in st.session_state:
        st.session_state.active_user_id = None
        
    if not os.path.exists(COOKIES_DIR):
        return

    st.session_state.user_cookies = {}
    for filename in os.listdir(COOKIES_DIR):
        if filename.endswith(".pkl"):
            user_id = filename.replace(".pkl", "")
            path = get_cookie_file_path(user_id)
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                
                timestamp = data.get("timestamp")
                # Cek kadaluarsa
                if timestamp and datetime.now() - timestamp > timedelta(minutes=COOKIE_EXPIRY_MINUTES):
                    os.remove(path)
                    print(f"⚠️ Cookies untuk {data.get('email', user_id)} kadaluarsa dan dihapus.")
                    continue

                st.session_state.user_cookies[user_id] = data
            except Exception as e:
                print(f"Gagal memuat cookies dari {filename}: {e}")
                
    # Sinkronisasi user aktif
    if st.session_state.active_user_id not in st.session_state.user_cookies:
        if st.session_state.user_cookies:
            st.session_state.active_user_id = list(st.session_state.user_cookies.keys())[0]
        else:
            st.session_state.active_user_id = None
        
def get_active_cookies_data():
    """Mendapatkan data cookies dari user yang aktif saat ini."""
    if st.session_state.active_user_id and st.session_state.active_user_id in st.session_state.user_cookies:
        return st.session_state.user_cookies[st.session_state.active_user_id]
    return None

def get_cookies_by_id(user_id):
    """Mendapatkan data cookies dari user_id tertentu."""
    return st.session_state.user_cookies.get(user_id)

def apply_cookies_to_driver(driver, cookies):
    """Menambahkan cookies ke instance Selenium WebDriver."""
    driver.get("https://www.google.com")
    driver.delete_all_cookies()
    for c in cookies:
        cookie = {}
        # Filter atribut yang dibutuhkan dan hindari 'expiry' jika tidak valid
        for k in ("name", "value", "path", "domain", "secure", "httpOnly", "expiry"):
            if k in c:
                cookie[k] = c[k]
        try:
            driver.add_cookie(cookie)
        except Exception:
            try:
                # Coba lagi tanpa 'expiry' jika gagal
                cookie2 = {k: cookie[k] for k in cookie if k != "expiry"}
                driver.add_cookie(cookie2)
            except Exception:
                pass
    driver.refresh()
    time.sleep(2)

def get_current_reporter_email_key():
    """Mendapatkan kunci email permanen (atau fallback ID) dari user report yang dipilih."""
    report_user_id = st.session_state.get("report_user_id")
    if not report_user_id:
        # Fallback ke user aktif jika user report tidak diset
        report_user_id = st.session_state.get("active_user_id")
        if not report_user_id:
            return None
        
    user_data = get_cookies_by_id(report_user_id)
    # Ini adalah kunci yang digunakan di JSON history
    return user_data.get("email", report_user_id) if user_data else report_user_id

def check_logged_in_via_driver(driver, timeout=10):
    """Mendeteksi apakah user sudah login di Google."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            # Cari avatar atau tombol sign out
            avatars = driver.find_elements(By.XPATH, "//img[contains(@alt,'Google Account') or contains(@aria-label,'Profile') or contains(@alt,'Foto profil')]")
            if avatars:
                return True
            signout = driver.find_elements(By.XPATH, "//*[contains(text(),'Sign out') or contains(text(),'Keluar')]")
            if signout:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

# --- Login Utama ---
def start_manual_google_login(timeout=LOGIN_TIMEOUT_SECONDS):
    """Buka browser non-headless untuk login manual dan ambil cookies/email."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    new_user_id = str(int(time.time()))

    try:
        driver.get("https://accounts.google.com/signin/v2/identifier")
        st.info("Browser terbuka. Silakan **login** di jendela yang muncul.")
        
        st.session_state.login_status = "Waiting for user login..."
        
        start = time.time()
        while time.time() - start < timeout:
            current_url = driver.current_url
            
            # Kriteria sukses: URL tidak lagi di accounts.google.com
            if "accounts.google.com" not in current_url:
                cookies = driver.get_cookies()
                
                # --- PENGAMBILAN EMAIL ---
                driver.get("https://myaccount.google.com/")
                time.sleep(4) 
                email = None
                
                # Heuristic untuk mencari email
                try:
                    email_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '@') and not(contains(text(), ' ')) and string-length(text()) > 5] | //*[@aria-label and contains(@aria-label, '@')]")
                    
                    for el in email_elements:
                        text = el.text.strip()
                        aria_label = el.get_attribute("aria-label")
                        
                        if re.match(r'[\w\.-]+@[\w\.-]+', text):
                            email = text
                            break
                        
                        if aria_label:
                            match = re.search(r'[\w\.-]+@[\w\.-]+', aria_label)
                            if match:
                                email = match.group(0)
                                break
                    
                    if not email:
                        # Coba ambil dari ancestor elemen profil
                        profile_img = driver.find_elements(By.XPATH, "//img[contains(@alt,'Foto profil') or contains(@aria-label,'Profile')]")
                        if profile_img:
                            ancestor = profile_img[0].find_element(By.XPATH, "./ancestor::div[4]")
                            match = re.search(r'[\w\.-]+@[\w\.-]+', ancestor.text)
                            if match:
                                email = match.group(0)
                        
                except Exception:
                    pass
                
                # Fallback email
                if not email or len(email) < 5 or "settings" in str(email).lower() or "pengaturan" in str(email).lower():
                    email = f"Account-{new_user_id[:6]}"
                
                save_cookies(cookies, new_user_id, email)
                driver.quit()
                st.session_state.login_status = f"Login berhasil. Cookies saved for: {email}"
                return new_user_id
            
            time.sleep(1)
        
        # Timeout
        driver.quit()
        st.session_state.login_status = "Login failed or timeout."
        return None
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        st.error(f"Gagal membuka browser untuk login: {e}")
        st.session_state.login_status = f"Browser failed to open: {e}"
        return None