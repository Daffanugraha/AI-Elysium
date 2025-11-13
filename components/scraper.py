# components/scraper.py

import streamlit as st
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from components.auth_manager import get_active_cookies_data, apply_cookies_to_driver, check_logged_in_via_driver
from utils.helpers import clean_review_text_en, parse_relative_date

def get_low_rating_reviews(gmaps_link, max_scrolls=10000):
    """
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    active_user_data = get_active_cookies_data()
    if active_user_data:
        try:
            apply_cookies_to_driver(driver, active_user_data["cookies"])
            time.sleep(2)
            # Cek login di domain maps agar cookies terpakai
            driver.get("https://www.google.com/maps")
            if not check_logged_in_via_driver(driver, timeout=3):
                st.warning("Cookies ditemukan tapi sepertinya tidak valid atau sudah kadaluarsa. Silakan login ulang.")
            else:
                st.success(f" successfully logged in as {active_user_data['email']}.")
        except Exception as e:
            st.warning(f"Gagal apply cookies: {e}")
            
    try:
        driver.get(gmaps_link)
        time.sleep(5)

        # --- Auto-detect place name ---
        try:
            place_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'DUwDvf')]").text.strip()
        except Exception:
            place_name = "Unknown_Place"

        # --- Click Reviews tab ---
        try:
            review_tab = driver.find_element(By.XPATH, "//button[contains(., 'Reviews') or contains(., 'Ulasan')]")
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)
        except Exception:
            pass

        # --- Sort by lowest rating ---
        try:
            sort_button = driver.find_element(By.XPATH, "//button[contains(., 'Sort') or contains(., 'Urutkan')]")
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(1)
            lowest = driver.find_elements(By.XPATH, "//*[contains(text(), 'Lowest rating') or contains(text(), 'Peringkat terendah')]")
            for opt in lowest:
                try:
                    driver.execute_script("arguments[0].click();", opt)
                    break
                except Exception:
                    continue
            time.sleep(2)
        except Exception:
            pass

        # --- Scroll efficiently ---
        try:
            scrollable_div = driver.find_element(By.XPATH, "//div[contains(@class,'m6QErb') and contains(@class,'DxyBCb')]")
        except Exception:
            scrollable_div = None

        if scrollable_div:
            last_height = 0
            same_count = 0
            for i in range(max_scrolls):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(0.5)
                new_height = driver.execute_script("return arguments[0].scrollTop", scrollable_div)
                if new_height == last_height:
                    same_count += 1
                    if same_count >= 2:
                        break
                else:
                    same_count = 0
                last_height = new_height
                if i % 50 == 0 and i != 0:
                     st.info(f"Scrolled {i} times. Found so far: {len(driver.find_elements(By.CLASS_NAME, 'jftiEf'))} reviews.")
        else:
            st.warning("Tidak dapat menemukan elemen scroll. Mencoba scroll halaman...")
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

        # --- Extract all reviews ---
        blocks = driver.find_elements(By.CLASS_NAME, "jftiEf")
        data = []

        for rb in blocks:
            try:
                # Klik "more"
                try:
                    more_button = rb.find_element(By.CLASS_NAME, "w8nwRe")
                    driver.execute_script("arguments[0].click();", more_button)
                    time.sleep(0.2)
                except Exception:
                    pass
                
                # Ambil data
                rating_text = rb.find_element(By.CLASS_NAME, "kvMYJc").get_attribute("aria-label")
                rating = rating_text.split()[0] if rating_text else ""
                text = rb.find_element(By.CLASS_NAME, "wiI7pd").text.strip()
                clean_text = clean_review_text_en(text)
                user = rb.find_element(By.CLASS_NAME, "d4r55").text
                date_txt = rb.find_element(By.CLASS_NAME, "rsqaWe").text
                date_parsed = parse_relative_date(date_txt)
                total_reviews = rb.find_element(By.CLASS_NAME, "RfnDt").text
                rating_value = float(rating)
            except Exception:
                # Skip blok review yang gagal diekstrak
                continue

            # Hanya ambil 1★ atau 2★
            if rating_value in [1.0, 2.0]:
                data.append({
                    "Place": place_name,
                    "User": user,
                    "Total Reviews": total_reviews,
                    "Rating": rating_value,
                    "Date (Raw)": date_txt,
                    "Date (Parsed)": date_parsed,
                    "Review Text": clean_text
                })

        driver.quit()
        df = pd.DataFrame(data)
        df["Place"] = place_name
        return df, place_name

    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        st.error(f"Error saat scraping: {e}")
        return pd.DataFrame(), "Unknown_Place_Error"