# EFFINOVA PANEL - TEMİZLENMİŞ VERSİYON
# VERİTABANI KODLARI CONFIG.PY'DE, UI KODLARI BURADA

import streamlit as st
import os
import logging
from datetime import datetime, date, timedelta
import random
import json
import uuid
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time as time_module
import hashlib
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# config.py'den import ediyoruz - TÜM VERİTABANI KODLARI ORADA
import config

# Diğer modüller
try:
    import excel_to_db
except ImportError:
    excel_to_db = None
try:
    import employees
except ImportError:
    employees = None
try:
    import badges
except ImportError:
    badges = None
try:
    import users
except ImportError:
    users = None
try:
    import pdf_utils
except ImportError:
    pdf_utils = None
try:
    import permissions
except ImportError:
    permissions = None
try:
    import enhanced_project_management
except ImportError:
    enhanced_project_management = None
try:
    from enhanced_innovation import manage_innovation as _manage_innovation_func
    innovation_module_available = True
except ImportError:
    innovation_module_available = False
    _manage_innovation_func = None
try:
    from yasayan_surec_ekosistemi import YasayanSurecEkosistemi
    yasayan_surec_available = True
except ImportError:
    yasayan_surec_available = False
    YasayanSurecEkosistemi = None

# STREAMLIT CONFIG
st.set_page_config(page_title="EFFINOVA Panel", layout="wide", page_icon="⭐")

# CONFIG'DEN ALINAN GLOBAL DEĞİŞKENLER
try:
    DATABASE_TYPE = config.DATABASE_TYPE
    MYSQL_AVAILABLE = config.MYSQL_AVAILABLE
    SQLALCHEMY_AVAILABLE = config.SQLALCHEMY_AVAILABLE
    SQLITE_DB_PATH = config.SQLITE_DB_PATH
    db_manager = config.db_manager
    execute_query = config.execute_query
    get_dataframe = config.get_dataframe
    get_connection = config.get_connection
    log_action = config.log_action
    initialize_database = config.initialize_database
    test_connection = config.test_connection
except Exception as e:
    st.error(f"❌ Config yükleme hatası: {e}")
    st.stop()

# LOGGING SETUP
BASE_DIR_FOR_LOG = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR_FOR_LOG, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "effinova_panel.log")

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GLOBAL BAYRAKLAR
DB_SYSTEM_CONFIGURED = False
total_users = 0

# PERFORMANCE PATCH
if "performance_mode" not in st.session_state:
    st.session_state.performance_mode = True

# SESSION STATE INIT
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "admin"
if "username" not in st.session_state:
    st.session_state["username"] = "admin"
if "user_department" not in st.session_state:
    st.session_state["user_department"] = "IT"

# CACHE'Lİ FONKSİYONLAR
@st.cache_data(ttl=300, max_entries=20)
def fast_get_employees():
    """Hızlı çalışan listesi - Cache'li"""
    try:
        query = """
            SELECT Sicil_No as sicil_no, Ad_Soyad as ad_soyad, Pozisyon as pozisyon, Departman as departman
            FROM employees
            WHERE deleted = 0 OR deleted IS NULL
            ORDER BY Ad_Soyad
            LIMIT 50
        """
        df = get_dataframe(query)
        return df
    except Exception as e:
        logger.error(f"Hızlı çalışan çekme hatası: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_employee_scores():
    """Çalışan skorlarını çek"""
    try:
        query = """
            SELECT employee_name as ad_soyad,
                    MAX(tarih) AS son_tarih,
                    MAX(toplam_skor) AS son_skor,
                    ROUND(AVG(toplam_skor), 2) AS ort_skor,
                    onay AS onay_durumu
            FROM process_scores
            WHERE employee_name IS NOT NULL
            GROUP BY employee_name
            ORDER BY ort_skor DESC
        """
        df = get_dataframe(query)
        return df
    except Exception as e:
        logger.error(f"Skor çekme hatası: {e}")
        return pd.DataFrame()

# YARDIMCI FONKSİYONLAR
def send_notification(message="Bildirim", notif_type="info"):
    """Basit bildirim sistemi"""
    try:
        if notif_type == "success":
            st.success(message)
        elif notif_type == "warning":
            st.warning(message)
        elif notif_type == "error":
            st.error(message)
        else:
            st.info(message)
    except Exception as e:
        logger.error(f"Bildirim hatası: {e}")

def has_access(feature, user_role, user_dept=None, target_dept=None):
    """Basit erişim kontrolü"""
    access_rules = {
        "admin": ["all"],
        "gmy": ["calisan_yonetimi", "canli_surec_yonetimi", "surec_yonetimi", "raporlar", "analitik", "liderlik_tablosu", "loglar", "excel_aktarim", "inovasyon"],
        "mudur": ["calisan_yonetimi", "canli_surec_yonetimi", "raporlar", "liderlik_tablosu", "excel_aktarim", "inovasyon"],
        "calisan": ["inovasyon", "rozetler", "canli_surec_yonetimi"]
    }

    if permissions and hasattr(permissions, 'has_access'):
        try:
            return permissions.has_access(feature, user_role, user_dept, target_dept)
        except Exception as e:
            logger.error(f"Permissions modülü hatası: {e}. Varsayılan kurallar kullanılıyor.")
            pass
    
    user_permissions = access_rules.get(user_role, [])
    if user_role == "admin":
        return True
    return "all" in user_permissions or feature in user_permissions

def add_performance_controls():
    """Performans kontrolleri - Sidebar'a eklenecek"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Performans")

    performance_mode = st.sidebar.toggle(
        "🚀 Hızlı Mod",
        value=st.session_state.get('performance_mode', True),
        key=f"perf_toggle_{st.session_state.get('username', 'guest')}_{int(time_module.time())}"
    )
    st.session_state.performance_mode = performance_mode

    if performance_mode:
        st.sidebar.success("⚡ Hızlı mod aktif")
        st.sidebar.caption("• 50 çalışan limit\n• 5dk cache\n• Hızlı yükleme")
    else:
        st.sidebar.info("🎨 Tam mod aktif")
        st.sidebar.caption("• Tüm çalışanlar\n• Tam özellikler")

    if st.sidebar.button("🧹 Cache Temizle", key=f"sidebar_cache_clear_{st.session_state.get('username', 'guest')}_{int(time_module.time())}", use_container_width=True):
        st.cache_data.clear()
        st.sidebar.success("✅ Temizlendi!")
        st.rerun()

def get_employees_from_db():
    """Çalışan listesini getir"""
    try:
        query = """
            SELECT
                Sicil_No as sicil_no,
                Ad_Soyad as ad_soyad,
                Pozisyon as pozisyon,
                Departman as departman,
                COALESCE(Yonetici_Adi, '') as yonetici,
                COALESCE(Email, '') as email,
                STRFTIME('%Y-%m-%d', Ise_Giris_Tarihi) as ise_giris,
                CASE WHEN deleted = 0 THEN 1 ELSE 0 END as aktif
            FROM employees
            WHERE deleted = 0 OR deleted IS NULL
            ORDER BY Ad_Soyad
        """
        df = get_dataframe(query)
        return df
    except Exception as e:
        logger.error(f"Çalışan listesi çekme hatası: {e}")
        st.error(f"❌ Çalışan listesi yüklenemedi: {e}")
        return pd.DataFrame()

def show_employee_details(search_value):
    """Çalışan detaylarını göster"""
    try:
        # Input validation
        if not search_value or not isinstance(search_value, str):
            st.error("❌ Geçerli bir arama değeri giriniz!")
            return
        
        # Sanitize input
        search_value = search_value.strip()
        if len(search_value) < 1 or len(search_value) > 100:
            st.error("❌ Arama değeri 1-100 karakter arasında olmalıdır!")
            return
        
        if search_value.isdigit():
            query = """
                SELECT Sicil_No, Ad_Soyad, Pozisyon, Departman, Email, Yonetici_Adi
                FROM employees
                WHERE Sicil_No = ? AND (deleted = 0 OR deleted IS NULL)
            """
            params = (search_value,)
        else:
            query = """
                SELECT Sicil_No, Ad_Soyad, Pozisyon, Departman, Email, Yonetici_Adi
                FROM employees
                WHERE LOWER(Ad_Soyad) LIKE LOWER(?) AND (deleted = 0 OR deleted IS NULL)
            """
            params = (f"%{search_value}%",)

        result = execute_query(query, params)

        if result:
            emp_data = result[0]
            sicil = emp_data['Sicil_No']
            ad_soyad = emp_data['Ad_Soyad']
            pozisyon = emp_data['Pozisyon']
            departman = emp_data['Departman']
            email = emp_data['Email']
            yonetici = emp_data['Yonetici_Adi']

            st.success(f"✅ Çalışan bulundu: **{ad_soyad}**")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("👤 Ad Soyad", ad_soyad)
                st.metric("🆔 Sicil No", sicil)

            with col2:
                st.metric("💼 Pozisyon", pozisyon or "Belirtilmemiş")
                st.metric("🏢 Departman", departman or "Belirtilmemiş")

            with col3:
                st.metric("📧 Email", email or "Belirtilmemiş")
                st.metric("👨‍💼 Yönetici", yonetici or "Belirtilmemiş")

            with col4:
                performance = random.randint(75, 95)
                projects = random.randint(2, 8)
                st.metric("📊 Performans", f"{performance}/100", delta="5")
                st.metric("🚀 Projeler", projects)

        else:
            st.error(f"❌ '{search_value}' ile eşleşen çalışan bulunamadı!")
            st.info("💡 Tam isim veya doğru sicil numarası deneyiniz.")

    except Exception as e:
        st.error(f"❌ Çalışan detay hatası: {e}")
        logger.error(f"Çalışan detaylarını gösterme hatası: {e}")

# ANA UYGULAMA
def main():
    """Ana uygulama"""
    global total_users, DB_SYSTEM_CONFIGURED

    st.title("⭐ EFFINOVA | Admin Paneli")
    st.markdown(f"### ✅ Sistem başarıyla yüklendi! 🚀 ({total_users} kullanıcı)")

    add_performance_controls()

    st.sidebar.title("🎯 Navigasyon")

    role_options = {
        "👨‍💻 Admin Paneli": "admin",
        "👔 Müdür Paneli": "mudur",
        "👤 Çalışan Paneli": "calisan",
        "🏢 GMY Paneli": "gmy"
    }

    try:
        current_index = list(role_options.values()).index(st.session_state["user_role"])
    except ValueError:
        current_index = 0

    selected_role_label = st.sidebar.selectbox(
        "Panel Seç",
        list(role_options.keys()),
        index=current_index,
        key=f"role_selector_{int(time_module.time())}"
    )

    st.session_state["user_role"] = role_options[selected_role_label]

    st.sidebar.markdown("---")
    st.sidebar.info(f"👤 **Kullanıcı:** {st.session_state['username']}")
    st.sidebar.info(f"🏷️ **Rol:** {st.session_state['user_role'].title()}")
    st.sidebar.info(f"🏢 **Departman:** {st.session_state['user_department']}")

    if st.sidebar.button("🔍 Bağlantı Test", key=f"connection_test_btn_{int(time_module.time())}"):
        if test_connection():
            st.sidebar.success("✅ Bağlantı başarılı!")
        else:
            st.sidebar.error("❌ Bağlantı başarısız!")

    st.markdown(f"## Hoş geldin, **{st.session_state['username']}**! 👋")

    col1_main_btn, col2_main_btn = st.columns(2)
    with col1_main_btn:
        if st.button("✅ Test Bildirim", key=f"test_notification_btn_main_{int(time_module.time())}"):
            send_notification("Test başarılı! 🎉", "success")
    with col2_main_btn:
        if st.button("🧹 Cache Temizle", key=f"cache_clear_btn_main_{int(time_module.time())}"):
            st.cache_data.clear()
            send_notification("Cache temizlendi!", "info")

    # TAB YÖNETİMİ (Diğer dosyalarda yapılacak)
    st.info("🚧 Sekme yönetimi ayrı dosyalara taşınacak...")

if __name__ == "__main__":
    # VERİTABANI BAŞLATMA
    try:
        DB_SYSTEM_CONFIGURED = initialize_database()
        if DB_SYSTEM_CONFIGURED:
            # Toplam kullanıcı sayısını al
            try:
                user_count_result = execute_query("SELECT COUNT(*) as total FROM users")
                total_users = user_count_result[0]['total'] if user_count_result and user_count_result[0] else 0
            except:
                total_users = 0
            
            main()
        else:
            st.error("❌ Uygulama başlatılamadı: Veritabanı sistemi yapılandırılamadı.")
    except Exception as e:
        st.error(f"❌ Uygulama genel hatası: {e}")
        logger.critical(f"Ana uygulama beklenmeyen hata: {e}")