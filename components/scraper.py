# components/scraper.py

import streamlit as st
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random
import traceback
from typing import List, Tuple, Dict, Any

# --- Impor yang Diminta ---
from components.auth_manager import get_active_cookies_data, apply_cookies_to_driver, check_logged_in_via_driver
from utils.helpers import clean_review_text_en, parse_relative_date


def get_low_rating_reviews(gmaps_link, max_scrolls=4000) -> Tuple[pd.DataFrame, str]:
    """
    Main function to extract low-rated reviews (1 and 2 stars) from a Google Maps link.
    It attempts two methods: Lowest Rating (priority) and Default Sort (fallback).
    """
    
    # --- NESTED FUNCTIONS (Helper functions) ---

    def _attempt_sort(driver: webdriver.Chrome, attempt_type: str) -> bool:
        """Attempts to click the 'Lowest Rating' sort button using JS."""
        if attempt_type != "lowest":
             st.error("Internal Error: _attempt_sort should only be called for 'lowest' in this configuration.")
             return False
             
        option_text = "Lowest rating"
        success_message = "✅ Successfully sorted by **Lowest Rating**."

        try:
            sort_button = None
            sort_candidates = driver.find_elements(By.XPATH, "//button[contains(., 'Sort') or contains(., 'Urutkan') or @aria-label='Sort reviews' or @aria-label='Urutkan ulasan']")
            for btn in sort_candidates:
                if btn.is_displayed():
                    sort_button = btn
                    break
            
            if not sort_button:
                st.warning("⚠️ Failed to find the Sort button.")
                return False
                
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(random.uniform(0.3, 0.6)) 
            
            options = driver.find_elements(By.XPATH, f"//*[contains(text(), '{option_text}') or contains(text(), 'Peringkat terendah')]")
            
            clicked = False
            for opt in options:
                is_target_option = (option_text in opt.text) or ("Peringkat terendah" in opt.text)
                                     
                if opt.is_displayed() and is_target_option:
                    driver.execute_script("arguments[0].click();", opt)
                    clicked = True
                    break
            
            if clicked:
                time.sleep(random.uniform(1.0, 2.0)) 
                return True
            else:
                st.warning(f"⚠️ Failed to find option '{option_text}'.")
                return False
                
        except Exception as e:
            st.error(f"❌ Error while attempting to sort {attempt_type}: {e}")
            return False

    def _get_reviews_from_driver_and_scroll(driver: webdriver.Chrome, place_name: str, is_second_run: bool, scroll_attempt_number: int) -> List[Dict[str, Any]]:
        """Performs scrolling on the review list, then performs extraction."""
        
        data = []
        skipped_count_critical = 0 
        
        # --- HUMAN-SMOOTH SCROLLING PARAMS ---
        MIN_SCROLL_STEP = 700  
        MAX_SCROLL_STEP = 1000  
        MIN_SLEEP = 0.03       
        MAX_SLEEP = 0.07       
        READING_INTERVAL = 3
        LONG_PAUSE_MIN = 0.2  
        LONG_PAUSE_MAX = 0.4 
        
        # --- Find scrollable reviews element ---
        scrollable_div = None
        candidates = [
            "//div[@role='list' and @aria-label]",
            "//div[contains(@class,'m6QErb') and contains(@class,'DxyBCb')]",
            "//div[contains(@class,'section-scrollbox')]",
            "//div[contains(@aria-label,'Reviews') or contains(@aria-label,'Ulasan')]"
        ]
        for sel in candidates:
            try:
                scrollable_div = driver.find_element(By.XPATH, sel)
                if scrollable_div:
                    break
            except Exception:
                continue

        if scrollable_div:
            last_scroll_pos = -1
            same_pos_count = 0
            total_scroll_attempts = 0
            last_review_count = 0

            # --- Logic: Reset Scroll Position ---
            if is_second_run or scroll_attempt_number > 1:
                try:
                    driver.execute_script("arguments[0].scrollTop = 0", scrollable_div)
                    time.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    st.warning(f"Failed to reset scroll position: {e}")
            # --- End Logic ---

            while total_scroll_attempts < max_scrolls:
                scroll_step = random.randint(MIN_SCROLL_STEP, MAX_SCROLL_STEP)
                sleep_duration = random.uniform(MIN_SLEEP, MAX_SLEEP)

                driver.execute_script(f"arguments[0].scrollBy(0, {scroll_step});", scrollable_div)
                time.sleep(sleep_duration)

                total_scroll_attempts += 1
                
                try:
                    current_scroll_pos = driver.execute_script("return arguments[0].scrollTop", scrollable_div)
                except Exception:
                    current_scroll_pos = -1

                if total_scroll_attempts % READING_INTERVAL == 0:
                    long_pause = random.uniform(LONG_PAUSE_MIN, LONG_PAUSE_MAX)
                    time.sleep(long_pause)

                # Detect stuck scroll (mentok logic)
                if current_scroll_pos == last_scroll_pos and last_scroll_pos != -1:
                    same_pos_count += 1
                    
                    if same_pos_count >= 2: 
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                        time.sleep(random.uniform(0.5, 1.0)) 

                        new_pos = driver.execute_script("return arguments[0].scrollTop", scrollable_div)
                        
                        if new_pos > last_scroll_pos:
                            same_pos_count = 0
                            last_scroll_pos = new_pos
                        
                        elif same_pos_count >= 5: 
                            break
                        else:
                            driver.execute_script("arguments[0].scrollBy(0, -50);", scrollable_div) 
                            time.sleep(0.05)
                            driver.execute_script("arguments[0].scrollBy(0, 100);", scrollable_div)
                            time.sleep(random.uniform(0.1,0.3)) 
                    
                elif current_scroll_pos != -1:
                    same_pos_count = 0
                    last_scroll_pos = current_scroll_pos

                current_review_count = len(driver.find_elements(By.CLASS_NAME, 'jftiEf'))

                if current_review_count > last_review_count:
                    time.sleep(random.uniform(0.2, 0.5)) 

                last_review_count = current_review_count

            # Final ensure bottom
            try:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            except Exception:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
            time.sleep(0.5) 
        else:
            st.warning("Could not find scrollable element. Skipping scrolling/extraction.")
            time.sleep(0.2) 


        # --- EXTRACT ALL AVAILABLE REVIEWS ---
        blocks = driver.find_elements(By.CLASS_NAME, "jftiEf")
        # st.info(f"Found **{len(blocks)}** review blocks to extract.") # Dihapus

        for i, rb in enumerate(blocks):
            review_data = {}
            fail_reason = []
            
            try:
                # Expand "more"
                try:
                    more_button = rb.find_element(By.CLASS_NAME, "w8nwRe")
                    driver.execute_script("arguments[0].click();", more_button)
                    time.sleep(0.03) 
                except Exception:
                    pass

                # Extract data 
                try:
                    review_data["User"] = rb.find_element(By.CLASS_NAME, "d4r55").text.strip()
                except Exception:
                    review_data["User"] = f"UNKNOWN USER ({i+1})"
                    fail_reason.append("Username")

                try:
                    rating_text = rb.find_element(By.CLASS_NAME, "kvMYJc").get_attribute("aria-label")
                    review_data["Rating"] = float(rating_text.split()[0]) if rating_text else 0.0
                except Exception:
                    try:
                        rating_attr = rb.find_element(By.XPATH, ".//span[contains(@aria-label,'stars') or contains(@class,'stars')]").get_attribute("aria-label")
                        review_data["Rating"] = float(rating_attr.split()[0]) if rating_attr else 0.0
                    except Exception:
                        review_data["Rating"] = 0.0
                        fail_reason.append("Rating")

                try:
                    review_text = rb.find_element(By.CLASS_NAME, "wiI7pd").text.strip()
                    review_data["Review Text"] = clean_review_text_en(review_text) if review_text else ""
                except Exception:
                    review_data["Review Text"] = ""
                    fail_reason.append("Review Text")

                try:
                    date_txt = rb.find_element(By.CLASS_NAME, "rsqaWe").text.strip()
                    review_data["Date (Raw)"] = date_txt
                    review_data["Date (Parsed)"] = parse_relative_date(date_txt)
                except Exception:
                    review_data["Date (Raw)"] = ""
                    review_data["Date (Parsed)"] = None
                    fail_reason.append("Date")

                try:
                    review_data["Total Reviews"] = rb.find_element(By.CLASS_NAME, "RfnDt").text
                except Exception:
                    review_data["Total Reviews"] = None

                # --- SAVE LOGIC: SAVE EVEN WITH PARTIAL FAILURES ---
                
                # 1. Only save low-rated reviews (1 or 2 stars)
                if review_data["Rating"] in [1.0, 2.0]:
                    data.append({
                        "Place": place_name,
                        **review_data
                    })
                    
                    # 2. Log minor failure after data is added
                    if fail_reason:
                        # st.warning(...) # Dihapus
                        pass
                # else: Skip reviews with rating > 2.0
                
            except Exception as e:
                # This block handles CRITICAL failure (review block cannot be processed at all)
                skipped_count_critical += 1
                st.error(f"❌ Block #{i+1} **CRITICALLY skipped**. Possible XPATH 'jftiEf' change or corrupted element. Error: {e}")
                continue

        
        st.info(f"Extraction attempt #{scroll_attempt_number} finished. Total 1 & 2 star reviews retrieved: **{len(data)}**. Total Critical Blocks Skipped: **{skipped_count_critical}**.")
        return data

    # --- START OF MAIN FUNCTION LOGIC ---

    # --- 1. WebDriver Options Configuration ---
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--headless=new")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_low_reviews = []
    place_name = "Unknown_Place"
    
    try:
        # --- 2. Cookies/Login Handling ---
        active_user_data = get_active_cookies_data()
        if active_user_data:
            try:
                driver.get("https://www.google.com")
                apply_cookies_to_driver(driver, active_user_data["cookies"])
                time.sleep(random.uniform(0.3, 0.7)) 
                driver.get("https://www.google.com/maps")
                if check_logged_in_via_driver(driver, timeout=2): 
                    st.success(f"**SUCCESS:** Successfully logged in as **{active_user_data['email']}**.")
                else:
                    st.warning("Cookies found but seem invalid or expired.")
            except Exception as e:
                st.warning(f"Failed to apply cookies: {e}")

        # --- 3. Navigation and Place Name Retrieval ---
        driver.get(gmaps_link)
        time.sleep(random.uniform(1.0, 2.0)) 

        try:
            place_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'DUwDvf')]").text.strip()
        except Exception:
            place_name = "Unknown_Place"
        st.info(f"Starting collecting data for place: **{place_name}**")

        # --- 4. Click Reviews tab ---
        review_tab_clicked = False
        try:
            review_tab = driver.find_element(By.XPATH, "//button[contains(., 'Reviews') or contains(., 'Ulasan')]|//a[contains(., 'Reviews') or contains(., 'Ulasan')]")
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(random.uniform(1.0, 2.0)) 
            review_tab_clicked = True
        except Exception:
            st.warning("Failed to find Reviews tab. Attempting sort/scroll on current page.")

        # ==========================================================
        #           EXECUTE METHOD 1 & METHOD 2
        # ==========================================================

        if review_tab_clicked:
            # --- METHOD 1: SORT BY LOWEST RATING (Priority) ---
            sorted_success = _attempt_sort(driver, "lowest")
            
            if sorted_success:
                low_reviews_method1 = []
                for attempt in range(1, 3): 
                    reviews = _get_reviews_from_driver_and_scroll(driver, place_name, False, attempt)
                    low_reviews_method1.extend(reviews)
                    
                all_low_reviews.extend(low_reviews_method1)
                st.success(f"Method 1 (Lowest Rating) finished. Total retrieved: **{len(low_reviews_method1)}** 1 & 2 star reviews.")
            else:
                st.warning("Sorting by Lowest Rating failed. Proceeding to Method 2.")

            # --- METHOD 2: FALLBACK TO DEFAULT RATING (Always Executed, NO UI SORT) ---
            
            low_reviews_method2 = []
            for attempt in range(1, 2): 
                 reviews = _get_reviews_from_driver_and_scroll(driver, place_name, True, attempt) 
                 low_reviews_method2.extend(reviews)

            all_low_reviews.extend(low_reviews_method2)
            st.success(f"Method 2 (Default Sort) finished. Total retrieved: **{len(low_reviews_method2)}** 1 & 2 star reviews.")

        # ==========================================================
        #           5. Final Processing (Dedup)
        # ==========================================================
        
        df_raw = pd.DataFrame(all_low_reviews)
        
        if df_raw.empty:
            driver.quit()
            st.warning("No 1 or 2 star reviews were successfully extracted from both methods.")
            return pd.DataFrame(), place_name

        # Remove Duplicates
        initial_count = len(df_raw)
        df_final = df_raw.drop_duplicates(subset=['User', 'Review Text'], keep='first').reset_index(drop=True)
        dedup_count = len(df_final)

        st.success(f"**FINAL:** Extraction complete.")
        st.info(f"Total 1 & 2 star reviews before deduplication: {initial_count}.")
        st.info(f"Total duplicate reviews removed: {initial_count - dedup_count}.")
        st.success(f"Total **unique 1 & 2 star reviews** retrieved: **{dedup_count}**.")
        
        driver.quit()
        return df_final, place_name

    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        st.error(f"❌ CRITICAL ERROR: Error during scraping: {e}")
        st.text(traceback.format_exc())
        return pd.DataFrame(), "Unknown_Place_Error"