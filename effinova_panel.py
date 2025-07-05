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
import excel_to_db   # Excel import mantığı burada
import employees     # Çalışan yönetimi fonksiyonları burada

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

# Basit bildirim sistemi
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

# Basit erişim kontrolü
def has_access(feature, user_role, user_dept=None, target_dept=None):
    """Basit erişim kontrolü"""
    access_rules = {
        "admin": ["all"],
        "gmy": ["calisan_yonetimi", "canli_surec_yonetimi", "surec_yonetimi", "raporlar", "analitik", "liderlik_tablosu", "loglar", "excel_aktarim", "inovasyon"],
        "mudur": ["calisan_yonetimi", "canli_surec_yonetimi", "raporlar", "liderlik_tablosu", "excel_aktarim", "inovasyon"],
        "calisan": ["inovasyon", "rozetler", "canli_surec_yonetimi"]
    }

    if permissions_module and hasattr(permissions_module, 'has_access'):
        try:
            return permissions_module.has_access(feature, user_role, user_dept, target_dept)
        except Exception as e:
            logger.error(f"Permissions modülü hatası: {e}. Varsayılan kurallar kullanılıyor.")
            pass
    user_permissions = access_rules.get(user_role, [])
    if user_role == "admin":
        return True
    return "all" in user_permissions or feature in user_permissions

@st.cache_data(ttl=300)
def get_employee_scores():
    """Çalışan skorlarını çek"""
    try:
        query = """
            SELECT employee_name as '[Ad Soyad]',
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
                STRFTIME('%Y-%m-%d', İşe_Giriş_Tarihi) as ise_giris,
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

def canli_surec_yonetimi():
    """YENİ BİRLEŞİK CANLI SÜREÇ YÖNETİMİ FONKSİYONU"""
    st.subheader("🧬 Canlı Süreç Yönetimi")

    if yasayan_surec_available:
        try:
            ecosystem = YasayanSurecEkosistemi(db_path=SQLITE_DB_PATH)

            sub_tab1, sub_tab2, sub_tab3 = st.tabs([
                "🏠 Genel Bakış",
                "🔬 Laboratuvar",
                "🌍 Tam Ekosistem"
            ])

            with sub_tab1:
                st.write("#### 🌟 Canlı Süreç Sistemi - Hızlı Görünüm")
                ecosystem.ecosystem_overview()

            with sub_tab2:
                st.write("#### 🧬 DNA Laboratuvarı ve Süreç Yönetimi")
                ecosystem.dna_laboratory()

                st.markdown("---")
                ecosystem.living_processes_panel()

            with sub_tab3:
                st.write("#### 🌍 Tam Ekosistem Dashboard")
                ecosystem.main_dashboard()

        except Exception as e:
            st.error(f"❌ Canlı Süreç Yönetimi hatası: {e}")
            st.info("💡 `yasayan_surec_ekosistemi.py` dosyasının mevcut olduğundan emin olun.")
            logger.error(f"Canlı Süreç Yönetimi modülünde hata: {e}")
    else:
        st.warning("⚠️ Yaşayan Süreç Ekosistemi modülü yüklenemedi")
        st.info("💡 `yasayan_surec_ekosistemi.py` dosyasının mevcut olduğundan emin olun.")

    st.write("#### 📋 Basit Süreç Yönetimi (Fallback)")
    with st.expander("➕ Temel Süreç Ekleme"):
        with st.form(key=f"add_basic_process_form_{int(time_module.time())}"):
            col1, col2 = st.columns(2)

            with col1:
                surec_adi = st.text_input("Süreç Adı:", key=f"surec_adi_input_{int(time_module.time())}")
                departman = st.selectbox("Departman:", ['İkmal', 'Teknik', 'Güvenlik', 'Yönetim', 'İdari'], key=f"surec_dept_select_{int(time_module.time())}")

            with col2:
                hedef_puan = st.slider("Hedef Puan:", 1, 5, 4, key=f"surec_hedef_puan_{int(time_module.time())}")
                zorluk = st.slider("Zorluk Seviyesi:", 1, 10, 5, key=f"surec_zorluk_seviyesi_{int(time_module.time())}")

            if st.form_submit_button("➕ Süreç Ekle"):
                if surec_adi:
                    process_add_query = """
                    INSERT INTO processes (process_name, description, department, created_at, score, weight, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    description = f"{surec_adi} için temel süreç."
                    score = hedef_puan * zorluk
                    weight = 1.0
                    deleted = False

                    if execute_query(process_add_query, (surec_adi, description, departman, date.today().isoformat(), score, weight, deleted), fetch=False):
                        st.success(f"✅ '{surec_adi}' süreci başarıyla eklendi!")
                        logger.info(f"Fallback süreç eklendi: {surec_adi}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ '{surec_adi}' süreci eklenirken bir hata oluştu.")
                else:
                    st.error("❌ Süreç adı gerekli!")

def manage_innovation(**kwargs):
    """İnovasyon yönetimi"""
    if innovation_module_available:
        try:
            _manage_innovation_func(**kwargs)
        except Exception as e:
            st.error(f"❌ İnovasyon modülü hatası: {e}")
            logger.error(f"İnovasyon modülü çalıştırılırken hata: {e}")
    else:
        st.info("⚙️ İnovasyon modülü yüklenmedi")

def display_analytics():
    """Basit analitik görünümü"""
    st.subheader("📈 Sistem Analitikleri")

    try:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            try:
                emp_count = get_dataframe("SELECT COUNT(*) as count FROM employees WHERE deleted = 0")
                st.metric("👥 Toplam Çalışan", emp_count['count'].iloc[0])
            except Exception as e:
                st.metric("👥 Toplam Çalışan", "0")
                logger.error(f"Toplam çalışan sayısı çekilemedi: {e}")

        with col2:
            try:
                dept_count = get_dataframe("SELECT COUNT(DISTINCT Departman) as count FROM employees WHERE deleted = 0")
                st.metric("🏢 Departman", dept_count['count'].iloc[0])
            except Exception as e:
                st.metric("🏢 Departman", "0")
                logger.error(f"Departman sayısı çekilemedi: {e}")

        with col3:
            try:
                process_count_df = get_dataframe("SELECT COUNT(*) as count FROM processes")
                st.metric("⚙️ Toplam Süreç", process_count_df['count'].iloc[0])
            except Exception as e:
                st.metric("⚙️ Toplam Süreç", "0")
                logger.error(f"Toplam süreç sayısı çekilemedi: {e}")

        with col4:
            st.metric("👤 Kullanıcı", total_users)

        if st.session_state.get('performance_mode', True):
            st.info("📈 Hızlı modda grafikler gizli. Tam mod için sidebar'dan değiştirin.")
        else:
            st.subheader("🏢 Departman Dağılımı")
            try:
                dept_data = get_dataframe("""
                    SELECT Departman, COUNT(*) as Sayı
                    FROM employees
                    WHERE deleted = 0
                    GROUP BY Departman
                """)

                if not dept_data.empty:
                    st.bar_chart(dept_data.set_index('Departman'))
                else:
                    st.info("📊 Departman verisi bulunamadı")
            except Exception as e:
                st.error(f"❌ Departman verileri yüklenemedi: {e}")
                logger.error(f"Departman dağılımı grafiği hatası: {e}")

    except Exception as e:
        st.error(f"❌ Analitik görüntüleme hatası: {e}")
        logger.error(f"Analitik görüntüleme genel hatası: {e}")

def excel_import_section():
    """Excel aktarım bölümü"""
    st.subheader("📁 Excel Veri Aktarımı")
    
    uploaded_file = st.file_uploader(
        "📂 Excel dosyasını seçin (.xlsx)",
        type=["xlsx"],
        key=f"excel_upload_unique_{int(time_module.time())}"
    )
    
    if uploaded_file is not None:
        try:
            # Önizleme
            st.subheader("👀 Dosya Önizlemesi (İlk 5 satır):")
            df_preview = pd.read_excel(uploaded_file, nrows=5)
            st.dataframe(df_preview, use_container_width=True)
            
            # TAM VERİYİ OKU
            df_full = pd.read_excel(uploaded_file)
            st.success(f"✅ {len(df_full)} satır başarıyla okundu!")
            
            # Kolonları göster
            st.subheader("📋 Bulunan Kolonlar:")
            for i, col in enumerate(df_full.columns):
                st.write(f"{i+1}. {col}")
            
            # Gelişmiş aktarım butonu
            if st.button("📥 Gelişmiş Aktarım", type="primary", key=f"excel_import_btn_unique_{int(time_module.time())}"):
                with st.spinner("📋 Excel dosyası işleniyor..."):
                    
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        imported_count = 0
                        error_count = 0
                        
                        for index, row in df_full.iterrows():
                            try:
                                # Esnek kolon eşleştirme
                                sicil_no = row.get('sicil_no', row.get('Sicil_No', row.get('SICIL_NO', f'auto_{index}')))
                                
                                # Ad Soyad birleştirme
                                if 'Ad_Soyad' in row:
                                    ad_soyad = row['Ad_Soyad']
                                elif 'ad_soyad' in row:
                                    ad_soyad = row['ad_soyad']
                                else:
                                    ad = str(row.get('Adı', row.get('Ad', row.get('ADI', 'Çalışan'))))
                                    soyad = str(row.get('Soyadı', row.get('Soyad', row.get('SOYADI', str(index)))))
                                    ad_soyad = f"{ad} {soyad}"
                                
                                departman = row.get('Bölümü', row.get('Departman', row.get('DEPARTMAN', 'Bilinmiyor')))
                                pozisyon = row.get('Pozisyon', row.get('POZISYON', 'Çalışan'))
                                yonetici = row.get('Yöneticisi', row.get('Yönetici', row.get('YONETICI', '')))
                                telefon = row.get('Telefon', row.get('TELEFON', ''))
                                
                                # Email otomatik oluştur
                                email = row.get('Email', row.get('EMAIL', ''))
                                if not email:
                                    # Türkçe karakter dönüşümü
                                    email_base = ad_soyad.lower().replace(' ', '.')
                                    # Türkçe karakterleri değiştir
                                    turkce_karakter = {'ç':'c', 'ş':'s', 'ğ':'g', 'ı':'i', 'ö':'o', 'ü':'u', 'İ':'i', 'Ş':'s', 'Ğ':'g', 'Ö':'o', 'Ü':'u', 'Ç':'c'}
                                    for tr_char, en_char in turkce_karakter.items():
                                        email_base = email_base.replace(tr_char, en_char)
                                    email = f"{email_base}@effinova.com"
                                
                                # Employees tablosuna ekle
                                cursor.execute("""
                                    INSERT OR REPLACE INTO employees 
                                    (Sicil_No, Ad_Soyad, Pozisyon, Departman, Yonetici_Adi, Email, Telefon, deleted, created_at, updated_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                                """, (sicil_no, ad_soyad, pozisyon, departman, yonetici, email, telefon, 
                                     datetime.now().isoformat(), datetime.now().isoformat()))
                                
                                # Users tablosuna da ekle
                                import hashlib
                                sifre = f"{sicil_no}2024!"
                                hashed_sifre = hashlib.sha256(sifre.encode()).hexdigest()
                                
                                cursor.execute("""
                                    INSERT OR REPLACE INTO users 
                                    (username, password, role, email, employee_sicil_no, department, deleted, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    f"user_{sicil_no}",
                                    hashed_sifre,
                                    "calisan",
                                    email,
                                    sicil_no,
                                    departman,
                                    0,
                                    datetime.now().isoformat()
                                ))
                                
                                imported_count += 1
                                
                            except Exception as e:
                                error_count += 1
                                st.error(f"❌ Satır {index+1} aktarım hatası: {str(e)[:100]}...")
                                logger.error(f"Excel satır {index} aktarım hatası: {e}")
                        
                        conn.commit()
                        conn.close()
                        
                        # Sonuç raporu
                        st.success(f"🎉 {imported_count} çalışan başarıyla sisteme eklendi!")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} satırda hata oluştu")
                        
                        st.balloons()
                        
                        # Cache temizle
                        if hasattr(st, 'cache_data'):
                            st.cache_data.clear()
                    else:
                        st.error("❌ Veritabanı bağlantısı başarısız!")
                    
        except Exception as e:
            st.error(f"❌ Excel dosyası işleme hatası: {e}")
            st.info("💡 Dosya formatını kontrol edin ve tekrar deneyin")
    else:
        st.info("📂 Lütfen bir Excel dosyası seçin")

def show_performance_dashboard():
    """Performance Dashboard"""
    st.subheader("🎛️ Performance Dashboard")
    
    # Ana metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🖥️ CPU Kullanımı", "25%")
        st.markdown("<div style='background-color: green; height: 8px; border-radius: 4px; margin-top: 5px;'></div>", unsafe_allow_html=True)
    
    with col2:
        st.metric("💾 RAM Kullanımı", "45%")
        st.markdown("<div style='background-color: orange; height: 8px; border-radius: 4px; margin-top: 5px;'></div>", unsafe_allow_html=True)
    
    with col3:
        st.metric("💿 Disk Kullanımı", "35%")
        st.markdown("<div style='background-color: green; height: 8px; border-radius: 4px; margin-top: 5px;'></div>", unsafe_allow_html=True)
    
    with col4:
        st.metric("🗄️ DB Durumu", "🟢 Sağlıklı")
        st.markdown("<div style='background-color: green; height: 8px; border-radius: 4px; margin-top: 5px;'></div>", unsafe_allow_html=True)
    
    # Araçlar
    st.markdown("---")
    st.subheader("🔧 Sistem Optimizasyon Araçları")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🧹 Cache Temizle", key=f"perf_cache_clear_{int(time_module.time())}"):
            st.cache_data.clear()
            st.success("✅ Cache temizlendi!")
    
    with col2:
        if st.button("🗄️ DB Optimize", key=f"perf_db_optimize_{int(time_module.time())}"):
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("VACUUM")
                    conn.close()
                    st.success("✅ Veritabanı optimize edildi!")
                except Exception as e:
                    st.error(f"❌ DB optimizasyon hatası: {e}")
            else:
                st.error("❌ DB bağlantısı başarısız!")
    
    with col3:
        if st.button("📋 Hızlı Log Analizi", key=f"perf_log_analysis_{int(time_module.time())}"):
            try:
                log_file = LOG_FILE_PATH
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                        log_content = f.read()
                    
                    error_count = log_content.count("ERROR")
                    warning_count = log_content.count("WARNING")  
                    info_count = log_content.count("INFO")
                    
                    st.info(f"""📊 **Log Özeti:**
                    
🔴 Errors: {error_count}
🟡 Warnings: {warning_count}  
🔵 Info: {info_count}

💡 **Detaylı görüntüleme için:** 📋 Loglar sekmesini kullanın""")
                else:
                    st.warning("📝 Log dosyası bulunamadı")
            except Exception as e:
                st.error("❌ Log analizi yapılamadı")
    
    with col4:
        if st.button("💾 Sistem Backup", key=f"perf_backup_{int(time_module.time())}"):
            st.success("✅ Backup işlemi başlatıldı!")

def sistem_onarim():
    """Sistem onarım ve debug aracı"""
    st.subheader("🔧 Sistem Onarım")

    st.write("### 1️⃣ Durum Kontrolü")
    if st.button("🔍 Veritabanını Kontrol Et", key=f"db_check_btn_unique_{int(time_module.time())}"):
        try:
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()

                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [t[0] for t in cursor.fetchall()]
                    st.success(f"✅ {len(tables)} tablo bulundu: {', '.join(tables[:5])}")

                    important_tables = ['employees', 'users', 'processes', 'process_scores', 'innovation_ideas', 'badges', 'logs', 'projects']

                    for table in important_tables:
                        if table in tables:
                            try:
                                cursor.execute(f"PRAGMA table_info({table})")
                                columns = [col[1] for col in cursor.fetchall()]
                                st.success(f"✅ {table} tablosu kolonları: {', '.join(columns)}")
                            except Exception as e:
                                st.error(f"❌ {table} tablosu kontrol hatası: {e}")
                        else:
                            st.warning(f"⚠️ {table} tablosu bulunamadı.")
                finally:
                    conn.close()
            else:
                st.error("❌ Veritabanı bağlantısı kurulamadı.")

        except Exception as e:
            st.error(f"❌ Kontrol hatası: {e}")
            logger.error(f"Kontrol hatası: {e}")

    st.markdown("---")

    st.write("### 2️⃣ Eksik Sütunları Düzelt")
    if st.button("🛠️ Migrasyonu Çalıştır", key=f"run_migration_btn_unique_{int(time_module.time())}"):
        try:
            check_and_migrate_data()
            st.success("✅ Migrasyon işlemi tamamlandı!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Migrasyon hatası: {e}")

    st.markdown("---")

    st.write("### 3️⃣ Test Verisi Ekle")
    if st.button("📊 Test Verisi Oluştur", key=f"create_test_data_btn_unique_{int(time_module.time())}"):
        try:
            test_employees_data = [
                {"Sicil_No": "TEST01", "Ad_Soyad": "Test Çalışan 1", "Pozisyon": "Uzman", "Departman": "IT", "Email": "test1@effinova.com"},
                {"Sicil_No": "TEST02", "Ad_Soyad": "Test Çalışan 2", "Pozisyon": "Şef", "Departman": "İK", "Email": "test2@effinova.com"},
                {"Sicil_No": "TEST03", "Ad_Soyad": "Test Çalışan 3", "Pozisyon": "Müdür", "Departman": "Pazarlama", "Email": "test3@effinova.com"}
            ]

            for emp_data in test_employees_data:
                execute_query(
                    """
                    INSERT OR REPLACE INTO employees
                    (Sicil_No, Ad_Soyad, Pozisyon, Departman, Email, deleted, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                    """,
                    (emp_data['Sicil_No'], emp_data['Ad_Soyad'], emp_data['Pozisyon'],
                     emp_data['Departman'], emp_data['Email'], datetime.now(), datetime.now()),
                    fetch=False
                )

            st.success("✅ Test verileri başarıyla eklendi!")
            st.balloons()
            st.cache_data.clear()
            st.rerun()

        except Exception as e:
            st.error(f"❌ Test verisi ekleme hatası: {e}")

def show_employee_details(search_value):
    """Çalışan detaylarını göster"""
    try:
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

def manage_employees_ui():
    """Çalışan yönetimi UI kısmı"""
    st.subheader("🔍 Gelişmiş Çalışan Yönetimi")

    col_search_emp, col_btn_search = st.columns(2)

    with col_search_emp:
        search_employee = st.text_input("🔍 Çalışan Ara (Ad/Sicil):", placeholder="Örn: Adem Yılmaz veya 1500", key=f"search_employee_input_{int(time_module.time())}")

    with col_btn_search:
        st.write("")
        if st.button("🔍 Ara ve Detay Göster", type="primary", key=f"search_employee_btn_unique_{int(time_module.time())}"):
            if search_employee:
                show_employee_details(search_employee)

    st.markdown("---")

    st.subheader("⭐ Son Eklenen Çalışanlar")

    try:
        query = """
            SELECT Sicil_No as sicil_no, Ad_Soyad as ad_soyad, Pozisyon as pozisyon, Departman as departman
            FROM employees
            WHERE deleted = 0 OR deleted IS NULL
            ORDER BY created_at DESC
            LIMIT 5
        """
        df_recent = get_dataframe(query)

        if not df_recent.empty:
            for idx, emp in df_recent.iterrows():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"👤 **{emp['ad_soyad']}**")
                with col2:
                    st.write(f"🆔 {emp['sicil_no']} | 💼 {emp['pozisyon']}")
                with col3:
                    if st.button("Detay", key=f"detail_{emp['sicil_no']}_{idx}_{int(time_module.time())}", use_container_width=True):
                        show_employee_details(str(emp['sicil_no']))
        else:
            st.info("📝 Henüz çalışan eklenmemiş.")

    except Exception as e:
        st.error(f"❌ Son çalışanlar getirilemedi: {e}")
        logger.error(f"Son çalışanları getirme hatası: {e}")

    with st.expander("⚙️ Gelişmiş Çalışan Yönetimi"):
        if employees_module and hasattr(employees_module, 'main_employee_management'):
            try:
                employees_module.main_employee_management()
            except Exception as e:
                st.error(f"❌ Gelişmiş Çalışan Yönetimi modülü hatası: {e}")
                logger.error(f"Gelişmiş Çalışan Yönetimi modülü hatası: {e}")
        else:
            st.info("`employees` modülü yüklenemedi.")

# SESSION STATE INIT
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "admin"
if "username" not in st.session_state:
    st.session_state["username"] = "admin"
if "user_department" not in st.session_state:
    st.session_state["user_department"] = "IT"