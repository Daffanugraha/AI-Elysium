import streamlit as st
import pandas as pd
import altair as alt
import io
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import base64
import json # <-- Diperlukan jika Anda ingin menampilkan JSON mentah

# Import modul yang telah direfaktor
from components.auth_manager import (
    load_all_cookies, start_manual_google_login, 
    get_active_cookies_data, get_cookies_by_id, get_current_reporter_email_key,
    generate_review_key
)
from components.scraper import get_low_rating_reviews
from components.reporter import (
    auto_report_review,
    load_report_history, # <-- Import untuk persistensi
    save_report_history, # <-- Import untuk persistensi
    load_submitted_log, # <-- Import untuk persistensi
    save_submitted_log  # <-- Import untuk persistensi
)
from utils.helpers import classify_report_category, generate_review_key, get_validation_details # <-- Import kunci dinamis
from utils.constants import REPORT_CATEGORIES, CATEGORY_DEFINITIONS


# 1. Base64 Getter Function
@st.cache_data
def get_img_as_base64(file_path):
    """Membaca file gambar dan mengembalikannya sebagai string Base64."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# 2. Injector Function
def inject_background_base64(img_path):
    img_base64 = get_img_as_base64(img_path) 
    
    if img_base64 is None:
        st.markdown("<style>.stApp { background-color: #05060A; }</style>", unsafe_allow_html=True)
        return

    # CSS yang menggunakan Pseudo-element untuk mengatur Opacity gambar saja
    page_bg_css = f"""
    <style>
    /* 1. Menyiapkan .stApp (Kontainer Utama) */
    .stApp {{
        position: relative;
        background-color: transparent !important; 
        min-height: 100vh;
        /* TAMBAHAN PENTING: Menjamin lapisan .stApp lebih tinggi dari background */
        z-index: 1; 
    }}

    /* 2. Pseudo-element untuk Background (Tetap di belakang) */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.9)), 
                          url("data:image/jpeg;base64,{img_base64}");
        
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        
        /* Opsi 1: Atur Opacity pada Pseudo-element (agar gambar transparan) */
        opacity: 1; /* SEDIKIT LEBIH TERANG DARI 0.15 agar terlihat */
        
        z-index: -1000; /* Jauhkan ke belakang */
    }}

    /* 3. Menjamin Konten Utama Streamlit (.main) berada di lapisan atas */
    .main {{
        z-index: 100; /* Paksa lapisan konten utama di depan */
        position: relative; /* Wajib ada untuk z-index bekerja */
    }}
    </style>
    """
    st.markdown(page_bg_css, unsafe_allow_html=True)


# --- Konfigurasi Streamlit Halaman & Styling ---
st.set_page_config(page_title="AI Elysium Report Tool", layout="wide", initial_sidebar_state="collapsed")

# ⚠️ GANTI "logo.jpg" dengan path yang benar jika file tidak di root
inject_background_base64("static\Background.jpg") 


# Memuat CSS kustom untuk styling komponen (diambil dari main.css)
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("styles/main.css") # Muat CSS utama


# --- TEKS JUDUL DI SIDEBAR (Sesuai permintaan Anda) ---
with st.sidebar:
    st.markdown("<h4 style='color: #FFD700;'>AI ELYSIUM</h4>", unsafe_allow_html=True)
    st.markdown("<p style='color: #A9E4D7; font-size: small;'>Pure Intelligence. Think Beyond. Think Elysium.</p>", unsafe_allow_html=True)

# --- Inisialisasi Session State & Cookies + JSON Persistensi ---
load_all_cookies() # Memuat cookies dari disk

# --- MUAT DATA PERSISTENSI JSON KE SESSION STATE ---
if "report_history" not in st.session_state:
    st.session_state.report_history = load_report_history() # Kunci: Email Reporter
if "reported" not in st.session_state:
    st.session_state["reported"] = load_submitted_log() # Log untuk tampilan UI
# --------------------------------------------------------

if "user_cookies" not in st.session_state:
    st.session_state.user_cookies = {}
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = None
if "google_logged" not in st.session_state:
    st.session_state.google_logged = bool(st.session_state.user_cookies)
if "gmaps_link_input" not in st.session_state:
    st.session_state.gmaps_link_input = ""
if "report_user_id" not in st.session_state and st.session_state.active_user_id:
    st.session_state.report_user_id = st.session_state.active_user_id
if "df_reviews" not in st.session_state:
    st.session_state.df_reviews = pd.DataFrame()
if "place_name" not in st.session_state:
    st.session_state.place_name = ""
if "is_reporting" not in st.session_state:
    st.session_state.is_reporting = False 
if "report_index_start" not in st.session_state:
    st.session_state.report_index_start = 0 
if "report_start_idx" not in st.session_state:
    st.session_state.report_start_idx = 0



# --- UI: Login dan Manajemen Akun ---
col_spacer, col_image = st.columns([5, 1]) 
# 2. Tampilkan Judul Login di Baris Baru (SECARA OTOMATIS DI BAWAH GAMBAR)
# Kita tidak perlu menggunakan kolom untuk judul lagi, karena kita ingin dia full-width.

st.markdown("## 🔑 Google Account Login ")
    
with st.container(border=True):
    col_status, col_add = st.columns([3, 1])

    with col_status:
        if not st.session_state.user_cookies:
            st.info("No saved accounts found. Please log in with the button on the right.")
        else:
            active_user_data = get_active_cookies_data()
            if active_user_data:
                st.success(f"Scraping User: **{active_user_data.get('email', 'Unknown User')}** is active.")
                st.caption(f"Cookies saved at: {active_user_data.get('timestamp').strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.warning("No active scraping user selected. Please check saved accounts.")

    with col_add:
        if st.button("➕ Login / Add New Account", key="add_new_login_btn", type="primary"):
            if "login_status" not in st.session_state:
                st.session_state.login_status = "Not started."
            
            with st.spinner("Opening browser... Please log in manually."):
                new_user_id = start_manual_google_login() # Tanpa argumen timeout
                
            if new_user_id:
                st.success(st.session_state.login_status)
                st.session_state.google_logged = True
                st.session_state.active_user_id = new_user_id
                st.session_state.report_user_id = new_user_id
                st.rerun()
            else:
                st.error(st.session_state.login_status)

# Jika belum ada user, hentikan aplikasi
if not st.session_state.google_logged:
    st.info("Please log in with at least one Google account to continue.")
    st.stop()
    
st.divider()

# --- UI: Input Link & Kolom Utama ---
st.markdown("## 🔍 Analyze Comment in Google Maps")
st.session_state.gmaps_link_input = st.text_input(
    "🔗 InputGoogle Maps Link", 
    value=st.session_state.gmaps_link_input
)
gmaps_link = st.session_state.gmaps_link_input

col_main, col_sidebar = st.columns([2, 1])

# --- KOLOM UTAMA: Scraping dan Hasil ---
with col_main:
    
    # 1. Tombol Start Scraping
    if st.button("🚀 Start Analyze", type="primary"):
        if gmaps_link:
            with st.spinner("Collecting data low-rating reviews... please wait a few minutes."):
                try:
                    df, place_name = get_low_rating_reviews(gmaps_link)
                except Exception as e:
                    st.error(f"Failed to scrape: {e}")
                    df = pd.DataFrame()
                    place_name = ""
                    
            if not df.empty:
                st.session_state.df_reviews = df
                st.session_state.place_name = place_name

                st.session_state.df_reviews['Place'] = place_name
                st.success(f"✅ Collected **{len(df)}** low-rating reviews from **{place_name}**")
                
                # Reset state terkait report saat data baru
                st.session_state.current_page = 1
                # st.session_state["reported"] TIDAK DIRESET agar log permanen terlihat
                st.session_state.is_reporting = False 
                st.session_state.report_index_start = 0
                for key in list(st.session_state.keys()):
                    # Hapus pilihan kategori lama
                    if key.startswith("choice_"):
                        del st.session_state[key]
                    # Hapus status tombol disabled yang nyangkut
                    if key.startswith("disabled_report_"):
                        del st.session_state[key]
                
                st.rerun()
                st.rerun()
            else:
                st.warning("No 1★ or 2★ reviews found.")
        else:
            st.error("Please input a valid Google Maps link.")

    df = st.session_state.df_reviews
    
    if not df.empty:
        st.divider()
        st.subheader(f"📊 Reviews to Report from: {st.session_state.place_name}")

        
# --- PENGATURAN TIGA FILTER DALAM SATU BARIS (MENGGUNAKAN st.columns) ---
        col_status, col_ai, col_page = st.columns([1, 1, 0.5]) # Sesuaikan rasio lebar kolom

        # 1. Filter Status Report (di kolom 1)
        with col_status:
            report_status_options = ["All Reviews", "Only Unreported Reviews"]
            selected_report_status = st.selectbox(
                "Filter by Report Status:",
                report_status_options,
                key="filter_report_status",
                label_visibility="visible" # Pastikan label terlihat
            )

        # 2. Filter Prediksi AI (di kolom 2)
        with col_ai:
            ai_categories = ["All Categories"] + sorted(list(REPORT_CATEGORIES))
            selected_ai_category = st.selectbox(
                "Filter by AI Prediction Category:",
                ai_categories,
                key="filter_ai_category",
                label_visibility="visible"
            )
        
        df_filtered = df.copy()
        
        # Logika Filter Report Status
        if selected_report_status == "Only Unreported Reviews":
            reporter_email_key = get_current_reporter_email_key()
            if reporter_email_key in st.session_state.report_history:
                reported_keys = set(st.session_state.report_history[reporter_email_key].keys())
                
                # Tambahkan kolom sementara 'is_reported'
                df_filtered['review_key'] = df_filtered.apply(generate_review_key, axis=1)
                df_filtered = df_filtered[~df_filtered['review_key'].isin(reported_keys)]
                df_filtered = df_filtered.drop(columns=['review_key'])
            else:
                # Jika tidak ada history report, tidak perlu filter (semua belum direport)
                pass

        # Logika Filter Prediksi AI
        if selected_ai_category != "All Categories":
            
            # Catatan: Karena 'category_ai' tidak ada di df asli (hanya dihitung saat iterasi), 
            # kita perlu menghitung/menyimpan prediksinya terlebih dahulu untuk filtering.
            
            # --- Perhitungan Kategori AI (Hanya dilakukan jika filternya aktif) ---
            # Idealnya ini dilakukan saat scraping, tapi karena tidak, kita hitung ulang.
            
            # Memastikan kolom 'category_ai_temp' ada untuk filtering
            if 'category_ai_temp' not in df_filtered.columns:
                # Menggunakan @st.cache_data untuk mempercepat jika data sama
                @st.cache_data
                def compute_ai_categories(df_input):
                    df_copy = df_input.copy()
                    categories = []
                    for index, row in df_copy.iterrows():
                        category_ai, _, _ = classify_report_category(row["Review Text"])
                        categories.append(category_ai)
                    df_copy['category_ai_temp'] = categories
                    return df_copy
                
                df_filtered = compute_ai_categories(df_filtered)
            
            df_filtered = df_filtered[df_filtered['category_ai_temp'] == selected_ai_category]
            
        # Gunakan df_filtered yang baru untuk paginasi dan tampilan selanjutnya
        df = df_filtered # Ganti referensi df ke df_filtered

        # --- 2. Logika Paginasi & Display ---
        with col_page:
            per_page_option = st.selectbox(
                "Show reviews per page:", 
                [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, "All"], 
                key="per_page_select",
                label_visibility="visible"
            )

        start_idx = 0
        end_idx = len(df)
        df_show = df

        # --- 3. Report Massal Section ---
        st.subheader("🤖 Automatic Report (This Page Only)")
        
        selected_report_category = st.selectbox(
            "Select Category:",
            REPORT_CATEGORIES,
            key="report_all_category_select"
        )
        
        confirmation_placeholder = st.empty()

        col_set, col_exec = st.columns([1, 1])

        def set_global_category_action():
            """Mengubah kategori report untuk semua review di halaman saat ini."""
            
            df_full = st.session_state.df_reviews
            
            # Ambil setting dari state
            per_page_option = st.session_state.get("per_page_select", 10) # Ambil nilai dari selectbox paginasi
            page = st.session_state.get("current_page", 1)
            target_category = st.session_state.report_all_category_select

            if df_full.empty:
                st.session_state.set_success = False 
                return

            # Hitung Indeks Halaman
            if per_page_option == "All":
                start_idx = 0
                end_idx = len(df_full)
            else:
                try:
                    per_page = int(per_page_option)
                except ValueError:
                    per_page = 10 # Default jika ada kesalahan
                    
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
            
            # Ambil subset DataFrame untuk halaman saat ini (menggunakan index ASLI)
            df_current_page = df_full.iloc[start_idx:min(end_idx, len(df_full))]
            
            if df_current_page.empty:
                st.session_state.set_success = False 
                return
                
            # Lakukan perubahan state pada INDEX ASLI (global_idx) yang digunakan oleh selectbox
            for global_idx in df_current_page.index: 
                st.session_state[f"choice_{global_idx}"] = target_category
                
            st.session_state.set_success = True

        # Tombol Set Kategori Default
        with col_set:
            if st.button(f"🔄 Set All Categories to '{selected_report_category}'", key="trigger_set_global_category"):
                with confirmation_placeholder.container():
                    st.info("ℹ️ Confirmation Change Category")
                    st.markdown(f"Are you sure you want to change the category for **{len(df_show)}** reviews on this page to: **{selected_report_category}**?")
                    
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Yes, Change Category", key="confirm_set_category", type="primary", on_click=set_global_category_action):
                            if st.session_state.get("set_success", False):
                                st.success(f"✅ Successfully set categories for all reviews on this page.")
                            else:
                                st.warning("No reviews found on this page.")
                            confirmation_placeholder.empty() 
                            st.rerun() 
                    with col_no:
                        if st.button("❌ Cancel", key="cancel_set_category"):
                            confirmation_placeholder.empty() 
                            st.info("Category change cancelled.")
                            
        if per_page_option != "All":
            per_page = int(per_page_option)
            total_pages = (len(df) - 1) // per_page + 1

            if "current_page" not in st.session_state:
                st.session_state.current_page = 1
            
            if st.session_state.get("prev_per_page") != per_page:
                st.session_state.current_page = 1
                st.session_state.prev_per_page = per_page

            def set_page(p):
                st.session_state.current_page = p

            page = st.session_state.current_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            df_show = df.iloc[start_idx:end_idx]
            
            st.write(f"Showing {start_idx+1}–{min(end_idx, len(df))} of {len(df)} total reviews.")

            # Tombol navigasi paginasi
            page_start = max(1, page - 4)
            page_end = min(total_pages, page + 5)
            page_nums = list(range(page_start, page_end + 1))
            
            page_cols = st.columns(min(len(page_nums), 10))
            
            for i, page_num in enumerate(page_nums):
                if i < len(page_cols):
                    with page_cols[i]:
                        if st.button(str(page_num), key=f"page_btn_{page_num}", type="primary" if page_num == page else "secondary"):
                            set_page(page_num)
                            st.rerun()
        
                

        # Tombol Eksekusi / Stop / Resume
# Tombol Eksekusi / Stop / Resume
# Pastikan semua fungsi pembantu diimport (time, pd, st, dll.)

# ... (Kode di atas col_exec tidak berubah)

        with col_exec:
            # Gunakan df_show, yang sudah difilter untuk halaman ini
            df_to_report_page = df_show

            # Label sekarang mencerminkan jumlah review di halaman saat ini
            report_button_label = f"🚨 Start Page Report ({len(df_to_report_page)} Reviews)"

            if st.session_state.is_reporting:
                # --- BLOK A: SEDANG MELAPOR (Loop Biasa) ---
                
                # 1. Tombol Stop
                if st.button("🚫 Stop Report Page", key="stop_report_all", type="secondary"):
                    st.session_state.is_reporting = False # 🛑 Set flag stop
                    st.warning("Page Report process stopping...")
                    
                    # 🔑 LOGIKA DRIVER QUIT SAAT KLIK STOP
                    if 'driver' in st.session_state and st.session_state.driver is not None:
                        try:
                            st.session_state.driver.quit()
                            del st.session_state.driver
                            st.success("✅ WebDriver (Chrome) successfully closed.")
                        except:
                            pass
                    
                    st.rerun() # RERUN untuk refresh UI

                st.info(f"Reporting in progress... ({len(df_to_report_page)} reviews)")
                
                reported_count = 0
                success_in_run = False
                status_container = st.empty()

                for global_idx, row in df_to_report_page.iterrows(): 
                    
                    # --- Perbaikan 2: Cek Stop di setiap iterasi ---
                    if not st.session_state.is_reporting:
                        st.warning(f"Process manually stopped after {reported_count} reports.")
                        break # Keluar dari loop

                    # --- Perbaikan 3: Mengambil Kategori yang Benar (Menggunakan Prediksi AI sebagai Default) ---
                    current_report_choice = st.session_state.get(f"choice_{global_idx}") 
                    
                    if current_report_choice is None:
                        # Jika Selectbox belum pernah disentuh/diinisialisasi, ambil prediksi AI
                        category_ai, _, _ = classify_report_category(row["Review Text"])
                        current_report_choice = category_ai 
                    
                    # Cek Anti-Double Report
                    reporter_email_key = get_current_reporter_email_key() 
                    review_key = generate_review_key(row)
                    already_reported = (
                        reporter_email_key and
                        reporter_email_key in st.session_state.report_history and
                        review_key in st.session_state.report_history[reporter_email_key]
                    )

                    if already_reported:
                        status_container.info(f"Skipping review from {row['User']}: Already reported.")
                        continue 

                    try:
                        status_container.text(f"Reporting {reported_count + 1}/{len(df_to_report_page)}: {row['User']} as '{current_report_choice}'...")
                        report_result = auto_report_review(row, current_report_choice)
                        
                        if report_result.startswith("✅"):
                            reported_count += 1
                            success_in_run = True
                            
                            # --- Perbaikan 1: LOGGING EKSPLISIT untuk sinkronisasi disable ---
                            if reporter_email_key not in st.session_state.report_history:
                                st.session_state.report_history[reporter_email_key] = {}
                                
                            st.session_state.report_history[reporter_email_key][review_key] = {
                                "Category": current_report_choice,
                                "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            save_report_history(st.session_state.report_history) # Simpan ke disk
                            
                            status_container.success(f"✅ Success reporting {row['User']} as '{current_report_choice}'.")
                            time.sleep(1) # Jeda antar report
                        else:
                            status_container.warning(f"Failed to report review from {row['User']}. Stopping page report. Details: {report_result}")
                            #st.session_state.is_reporting = False
                            continue
                            
                            # 🔑 LOGIKA DRIVER QUIT SAAT GAGAL REPORT
                            #if 'driver' in st.session_state and st.session_state.driver is not None:
                                #try:
                                    #st.session_state.driver.quit()
                                    #del st.session_state.driver
                                #except:
                                    #pass
                                    
                            break 
                    
                    except Exception as e:
                        st.error(f"❌ Error reporting review from {row['User']}. Skipping. Error: {e}")
                        #st.session_state.is_reporting = False
                        continue
                        
                        # 🔑 LOGIKA DRIVER QUIT SAAT EXCEPTION
                        #if 'driver' in st.session_state and st.session_state.driver is not None:
                            #try:
                                #st.session_state.driver.quit()
                                #del st.session_state.driver
                            #except:
                                #pass

                        break
                
                # --- Setelah loop selesai (Baik karena break, stop, atau selesai normal) ---
                status_container.empty()

                st.session_state.is_reporting = False # Reset state reporting
                
                # 🔑 LOGIKA DRIVER QUIT SAAT SELESAI NORMAL
                if 'driver' in st.session_state and st.session_state.driver is not None:
                    try:
                        st.session_state.driver.quit()
                        del st.session_state.driver
                        st.success("✅ Report Finished. WebDriver closed.")
                    except:
                        pass

                if success_in_run: 
                    # Tombol disable terjadi di sini setelah log di atas sukses
                    st.success(f"✅ Successfully reported {reported_count} reviews on this page!")
                    st.balloons()
                    
                st.rerun() # RERUN wajib untuk memuat ulang UI dengan log baru (tombol disable)
                    
            else:
                # --- BLOK B: TIDAK MELAPOR (TOMBOL START) ---
                
                if st.button(report_button_label, key="execute_report_all", type="primary", disabled=st.session_state.report_user_id is None):
                    if not st.session_state.get("report_user_id"):
                        st.error("Please select a report account in the right column first.")
                        st.stop()
                    
                    st.session_state.is_reporting = True 
                    
                    if df_to_report_page.empty:
                        st.warning("No reviews found on this page to report.")
                        st.session_state.is_reporting = False
                        st.rerun()
                    else:
                        # 🔑 CATATAN: Sebelum RERUN, pastikan driver sudah dibuat dan disimpan 
                        # di st.session_state.driver (Logika ini harus ada di tempat lain)
                        st.rerun() 

# ... (Sisa kode Report Tunggal dan Tampilan Log tidak berubah)
        # --- 4. Tampilan Review Perorangan (dengan SelectBox & Button) ---
        reporter_email_key = get_current_reporter_email_key()

        for idx, row in df_show.iterrows():
            review_key = generate_review_key(row)

            # Cek Anti-Double Report berdasarkan Kunci Permanen
            reporter_email_key = get_current_reporter_email_key()
            already_reported = (
                reporter_email_key and
                reporter_email_key in st.session_state.report_history and
                review_key in st.session_state.report_history[reporter_email_key]
            )
            
            category_ai, score, reason_tokens = classify_report_category(row["Review Text"])

            validation_details = get_validation_details(
                    review_text=row['Review Text'] or "", 
                    category_ai=category_ai, 
                    score=score, 
                    key_tokens_str=reason_tokens
                )
    
            policy_reason = validation_details['PolicyReason']
            context_sentence = validation_details['ContextSentence']
            key_concepts_str = validation_details['KeyConcepts']
            choice_key = f"choice_{idx}"
            
            if choice_key not in st.session_state:
                st.session_state[choice_key] = category_ai
            
            # Tampilan Review dengan Custom Container (Tidak diubah)
            with st.container(border=True):
                st.markdown(f"**👤 {row['User']}** — ⭐ **{row['Rating']}**")
                st.markdown(f"🕒 {row['Date (Parsed)']}  |  Reviews: {row['Total Reviews']}")
                st.markdown(f"💬 {row['Review Text'] or '*No text comment provided.*'}")
                st.markdown(f"**🔖 AI Prediction:** `{category_ai}` ({score}% confidence)")
                st.markdown(f"**📜 Policy Violation Reason:** {policy_reason}")
                st.markdown(f"**🔍 Key Concepts:** *{reason_tokens}*") # <-- Tampilan alasan
                st.markdown(f"**📝 Contextual Sentence:** *{context_sentence}*")


                report_choice = st.selectbox(
                    f"📑 Override Report Category for {row['User']}",
                    REPORT_CATEGORIES,
                    key=choice_key 
                )

                if already_reported:
                    # Cari info reporter dari log submitted
                    reported_info = st.session_state.report_history[reporter_email_key][review_key]
                    st.button(
                        f"✅ Reported by **You** ({reporter_email_key}) as '{reported_info['Category']}'", 
                        key=f"reported_{idx}", 
                        disabled=True
                    )
                else:
                    # 🟢 CODE BARU (Paste ini menggantikan blok else yang lama)
                    
                    # Cek sederhana: Matikan tombol jika sedang ada proses reporting apapun
                    if st.button("🚨 Single Automatic Report", 
                                 key=f"report_{idx}", 
                                 disabled=st.session_state.is_reporting): 
                        
                        if st.session_state.get("report_user_id"):
                            try:
                                # 1. Kunci UI agar tidak bisa klik 2x
                                st.session_state.is_reporting = True 
                                
                                # 2. Jalankan Report ke Google
                                report_result = auto_report_review(row, report_choice)
                                
                                if report_result.startswith("✅"):
                                    # 3. Update Memory Sementara (Session State)
                                    if reporter_email_key not in st.session_state.report_history:
                                        st.session_state.report_history[reporter_email_key] = {}
                                        
                                    st.session_state.report_history[reporter_email_key][review_key] = {
                                        "Category": report_choice,
                                        "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                    
                                    # 4. 💾 SIMPAN KE HARDDISK (Supaya aman dari restart/logout)
                                    save_report_history(st.session_state.report_history)
                                    # save_submitted_log(st.session_state["reported"])
                                    
                                    st.success(f"✅ Review from **{row['User']}** successfully reported!")
                                    
                                    # 5. Reset status dan Refresh halaman
                                    st.session_state.is_reporting = False 
                                    st.rerun()
                                    
                                else:
                                    # Jika Gagal Report (Misal error selenium)
                                    st.session_state.is_reporting = False
                                    st.error(f"Report failed: {report_result}")
                                
                            except Exception as e:
                                # Jika Error Code
                                st.session_state.is_reporting = False
                                st.error(f"Failed Report: {e}")
                        else:
                            st.error("Please select a report account in the right column first.")


        # Log Submitted Permanen (Tidak diubah)
        if "reported" in st.session_state and st.session_state["reported"]:
            st.divider()
            st.markdown("### 🧾 Successfully Reported Reviews")
            st.dataframe(pd.DataFrame(st.session_state["reported"]), use_container_width=True, hide_index=True)

            
        # Download Button
        if not df.empty:
            place_filename = st.session_state.place_name.replace(" ", "_").replace("/", "_")
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            st.download_button(
                "💾 Download Reviews (Excel)",
                buffer,
                file_name=f"low_rating_reviews_{place_filename}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# --- KOLOM SIDEBAR: Kontrol Multi-User dan Visualisasi ---
with col_sidebar:
    
    st.markdown("## ⚙️ Report Account Selector")
    
    # Pilih user untuk REPORT
    user_options = {
        user_id: user_data.get('email', f"User ID: {user_id}")
        for user_id, user_data in st.session_state.user_cookies.items()
    }
    
    try:
        default_index = list(user_options.keys()).index(st.session_state.report_user_id)
    except:
        default_index = 0

    if user_options:
        selected_user_id = st.selectbox(
            "Select Account for **REPORT**",
            options=list(user_options.keys()),
            format_func=lambda uid: user_options[uid],
            index=default_index,
            key="report_user_selector"
        )
        st.session_state.report_user_id = selected_user_id
        st.success(f"Reporting will use: **{user_options[selected_user_id]}**")
    else:
        st.warning("No Google accounts saved for reporting.")
    
    st.divider()
    
    # --- Bagian Visualisasi Rating & Map ---
    if gmaps_link and st.session_state.place_name:
        # ... (Logika visualisasi map dan rating distribution tetap sama) ...
        st.markdown("### 🗺️ Google Maps View")
        place_name = st.session_state.place_name or "Lokasi Tidak Diketahui"
        query = urllib.parse.quote_plus(place_name)
        embed_url = f"https://maps.google.com/maps?q={query}&output=embed"
        st.markdown(f"📍 **{place_name}**")
        st.components.v1.iframe(embed_url, height=400)

        # --- Visualisasi Rating Distribution (Menggunakan Selenium) ---
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(gmaps_link)
            time.sleep(5) 
            
            rows = driver.find_elements(By.CSS_SELECTOR, "tr.BHOKXe")
            distribusi = {}
            for r in rows:
                label = r.get_attribute("aria-label") 
                if label:
                    try:
                        bintang = int(label.split()[0])
                        jumlah = int(label.split(",")[1].split()[0])
                        distribusi[bintang] = jumlah
                    except Exception:
                        continue
            
            driver.quit()

            if distribusi:
                st.markdown("### 📊 Rating Distribution")
                df_dist = (
                    pd.Series(distribusi)
                    .reindex([5, 4, 3, 2, 1], fill_value=0)
                    .rename_axis("Rating")
                    .reset_index(name="Total Reviews")
                )
                
                warna = {5: "#4CAF50", 4: "#8BC34A", 3: "#FFC107", 2: "#FF9800", 1: "#F44336"}
                df_dist["Warna"] = df_dist["Rating"].map(warna)

# Di dalam bagian "Visualisasi Rating & Map"
# ...

                chart = (
                    alt.Chart(df_dist)
                    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                    .encode(
                        x=alt.X("Rating:O", sort="descending", axis=alt.Axis(title="Stars")),
                        y=alt.Y("Total Reviews:Q", axis=alt.Axis(title="Count")),
                        color=alt.Color("Warna:N", scale=None, legend=None),
                        tooltip=["Rating", "Total Reviews"]
                    )
                    .properties(height=400)
                    .configure_axis(
                        grid=False, 
                        titleColor='#E8F0FF', # Warna Judul Sumbu
                        labelColor='#A7C7FF', # Warna Label Sumbu
                        domainColor='#1A1F33' # Warna Garis Sumbu
                    )
                    .configure_view(
                        strokeWidth=0, # Hilangkan border pada view
                        stroke='transparent', 
                        fill='transparent'
                    )
                    .configure_title(
                        color='#00BFFF' # Warna Judul Grafik
                    )
                    .configure_text(
                        fill='#E8F0FF' # Warna Teks di dalam Grafik (jika ada)
                    )
                )

                st.altair_chart(chart, use_container_width=True, theme=None)

                
                total_review = df_dist["Total Reviews"].sum()
                if total_review > 0:
                    avg_rating = (df_dist["Rating"] * df_dist["Total Reviews"]).sum() / total_review
                    st.markdown(f"<h4 style='color:#FFD700;'>⭐ Average Rating: {avg_rating:.2f}</h4>", unsafe_allow_html=True)

            if not df.empty:
                st.markdown("### 💢 Negative Review Distribution")
                rating_counts = (
                    df["Rating"].value_counts().reindex([2, 1], fill_value=0)
                )
                summary_df = rating_counts.rename_axis("Rating").reset_index(name="Total Reviews")
                warna_neg = {2: "#FF9800", 1: "#F44336"}
                summary_df["Warna"] = summary_df["Rating"].map(warna_neg)
                
                pie_chart = (
                    alt.Chart(summary_df)
                    .mark_arc(outerRadius=80, innerRadius=30)
                    .encode(
                        theta="Total Reviews:Q",
                        color=alt.Color("Warna:N", scale=None, legend=None),
                        order=alt.Order("Total Reviews", sort="descending"),
                        tooltip=["Rating", "Total Reviews"]
                    )
                    .properties(height=450)
                )
                st.altair_chart(pie_chart, use_container_width=True)
                st.markdown(f"**Total Low-Rating Reviews: {rating_counts.sum()}**")


        except Exception as e:
            st.warning(f"Failed to load map or rating distribution: {e}")