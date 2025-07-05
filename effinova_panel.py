# EFFINOVA PANEL - MODERNIZE VE OPTIMIZE EDİLMİŞ VERSİYON
# Veritabanı kodları config.py'e taşındı

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

# CONFIG MODÜLÜNDEN VERİTABANI KODLARINI İMPORT ET
import config

# Harici modüllerimizi import ediyoruz
try:
    import excel_to_db   # Excel import mantığı burada
    import employees     # Çalışan yönetimi fonksiyonları burada
except ImportError as e:
    print(f"⚠️ Modül import hatası: {e}")
    excel_to_db = None
    employees = None

# STREAMLIT CONFIG - EN BAŞTA OLMALI!
st.set_page_config(page_title="EFFINOVA Panel", layout="wide", page_icon="⭐")

# CONFIG'DEN VERİTABANI YAPILARINI AL
DATABASE_TYPE = config.DATABASE_TYPE
SQLITE_DB_PATH = config.SQLITE_DB_PATH
MYSQL_AVAILABLE = config.MYSQL_AVAILABLE
SQLALCHEMY_AVAILABLE = config.SQLALCHEMY_AVAILABLE

# Veritabanı yöneticisi ve yardımcı fonksiyonlar
db_manager = config.db_manager
get_connection = config.get_connection
execute_query = config.execute_query
get_dataframe = config.get_dataframe
log_action = config.log_action
initialize_database = config.initialize_database
check_and_migrate_data = config.check_and_migrate_data
insert_default_data = config.insert_default_data
test_connection = config.test_connection
sqlalchemy_manager = config.sqlalchemy_manager

# --- GLOBAL BAYRAKLAR VE BAŞLANGIÇ DEĞERLERİ ---
DB_SYSTEM_CONFIGURED = False
total_users = 0

# --- LOGGING SETUP (BU DOSYADA) ---
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

# PERFORMANS BOOST AYARLARI
if "performance_mode" not in st.session_state:
    st.session_state.performance_mode = True

# SAFE IMPORTS - Hata olursa devam et
def safe_import(module_name):
    try:
        return __import__(module_name)
    except ImportError as e:
        st.sidebar.warning(f"⚠️ {module_name} modülü yüklenemedi: {e}")
        logger.warning(f"Modül yüklenemedi: {module_name}: {e}")
        return None

# Diğer modül importları
badges_module = safe_import('badges')
employees_module = safe_import('employees')
users_module = safe_import('users')
pdf_utils_module = safe_import('pdf_utils')
permissions_module = safe_import('permissions')
project_panel_module = safe_import('enhanced_project_management')

# İNOVASYON MODÜLÜ
try:
    from enhanced_innovation import manage_innovation as _manage_innovation_func
    innovation_module_available = True
    st.sidebar.success("💡 Enhanced Innovation modülü yüklendi!")
except ImportError as e:
    innovation_module_available = False
    st.sidebar.warning(f"⚠️ Enhanced Innovation modülü yüklenemedi: {e}")
    logger.warning(f"Enhanced Innovation modülü yüklenemedi: {e}")

# YAŞAYAN SÜREÇ EKOSİSTEMİ MODÜLÜ
try:
    from yasayan_surec_ekosistemi import YasayanSurecEkosistemi
    yasayan_surec_available = True
    st.sidebar.success("🧬 Yaşayan Süreç Ekosistemi modülü yüklendi!")
except ImportError as e:
    yasayan_surec_available = False
    st.sidebar.warning(f"⚠️ Yaşayan Süreç Ekosistemi modülü yüklenemedi: {e}")
    logger.warning(f"Yaşayan Süreç Ekosistemi modülü yüklenemedi: {e}")

# --- PERFORMANCE PATCH FONKSİYONLARI ---
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

# SESSION STATE INIT
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "admin"
if "username" not in st.session_state:
    st.session_state["username"] = "admin"
if "user_department" not in st.session_state:
    st.session_state["user_department"] = "IT"

# UYGULAMA BAŞLATMA
if __name__ == "__main__":
    # Veritabanını başlat
    DB_SYSTEM_CONFIGURED = initialize_database()
    
    # Kullanıcı sayısını güncelle
    if DB_SYSTEM_CONFIGURED:
        try:
            user_count_result = execute_query("SELECT COUNT(*) as total FROM users")
            total_users = user_count_result[0]['total'] if user_count_result and user_count_result[0] else 0
        except:
            total_users = 0
    
    if DB_SYSTEM_CONFIGURED:
        try:
            st.title("⭐ EFFINOVA | Admin Paneli")
            st.markdown(f"### ✅ Sistem başarıyla yüklendi! 🚀 ({total_users} kullanıcı)")
            st.success("🎉 Uygulama başarıyla başlatıldı!")
            st.info("💡 Ana fonksiyonlar yükleniyor...")
        except Exception as e:
            st.error(f"❌ Uygulama genel hatası: {e}")
            logger.critical(f"Ana uygulama beklenmeyen hata: {e}")
    else:
        st.error("❌ Uygulama başlatılamadı: Veritabanı sistemi yapılandırılamadı.")
        logger.critical("Uygulama başlatılamadı: Veritabanı sistemi yapılandırılamadı.")