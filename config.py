# config.py

import mysql.connector
from mysql.connector import Error
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
import logging
import os
from contextlib import contextmanager

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- MySQL connector import with error handling ---
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("⚠️ MySQL connector kurulu değil. Sadece SQLite kullanılabilir.")

# --- SQLAlchemy imports ---
try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, Float
    try:
        from sqlalchemy.orm import declarative_base
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None
    logger.warning("⚠️ SQLAlchemy kurulu değil. ORM özellikleri kullanılamayacak.")

# =============================================================================
# KONFIGÜRASYON AYARLARI
# =============================================================================

# Veritabanı tipi seçimi: 'mysql' veya 'sqlite'
if MYSQL_AVAILABLE:
    DATABASE_TYPE = 'sqlite'  # İsterseniz 'mysql' yapabilirsiniz
else:
    DATABASE_TYPE = 'sqlite'  # MySQL yoksa zorla SQLite

# MySQL Konfigürasyonu
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'effinova_db',
    'user': 'root',
    'password': '',  # MYSQL ŞİFRENİZİ BURAYA YAZIN
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True
}

# SQLite Konfigürasyonu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "effinova.db")

# SQLAlchemy Konfigürasyonu
SQLITE_ENGINE = None
SQLiteSessionLocal = None

if SQLALCHEMY_AVAILABLE:
    SQLITE_ENGINE = create_engine(f"sqlite:///{SQLITE_DB_PATH}")

    def get_mysql_engine():
        if not MYSQL_AVAILABLE:
            return None
        mysql_url = f"mysql+mysqlconnector://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        return create_engine(mysql_url, echo=False)

    SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=SQLITE_ENGINE)

# =============================================================================
# SQLALCHEMY ORM MODELLER
# =============================================================================

if SQLALCHEMY_AVAILABLE:
    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(String(50), unique=True, nullable=False)
        password = Column(String(255), nullable=False)
        role = Column(String(20), default='calisan')
        email = Column(String(100))
        score = Column(Integer, default=0)
        last_login = Column(DateTime)
        token = Column(String(255))
        employee_sicil_no = Column(String(20))
        department = Column(String(100))
        deleted = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.now)

    class Employee(Base):
        __tablename__ = 'employees'
        id = Column(Integer, primary_key=True, autoincrement=True)
        Ad_Soyad = Column(String(100), nullable=False)
        Pozisyon = Column(String(100), nullable=False)
        Departman = Column(String(100), nullable=False)
        Yonetici_Adi = Column(String(100))
        IK_Yonetici_Adi = Column(String(100))
        Email = Column(String(100))
        Sicil_No = Column(String(20), unique=True, nullable=False)
        İşe_Giriş_Tarihi = Column(Date)
        Telefon = Column(String(20))
        Adres = Column(Text)
        Dogum_Tarihi = Column(Date)
        Egitim = Column(Text)
        Sertifikalar = Column(Text)
        Yetenekler = Column(Text)
        deleted = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class Process(Base):
        __tablename__ = 'processes'
        id = Column(Integer, primary_key=True, autoincrement=True)
        process_name = Column(String(200), nullable=False)
        description = Column(Text)
        department = Column(String(100))
        created_at = Column(DateTime, default=datetime.now)
        score = Column(Integer, default=0)
        weight = Column(Float, default=1.0)
        deleted = Column(Boolean, default=False)

    class ProcessScore(Base):
        __tablename__ = 'process_scores'
        id = Column(Integer, primary_key=True, autoincrement=True)
        process_id = Column(Integer, ForeignKey('processes.id'))
        employee_name = Column(String(100), nullable=False)
        employee_sicil_no = Column(String(20))
        cikti = Column(Integer, default=0)
        kalite = Column(Integer, default=0)
        strateji = Column(Integer, default=0)
        inovasyon = Column(Integer, default=0)
        zaman = Column(Float, default=0)
        ekstra = Column(Integer, default=0)
        ekstra_aciklama = Column(Text)
        toplam_skor = Column(Float, default=0)
        tarih = Column(Date, default=date.today())
        onay = Column(String(50), default='Beklemede')
        created_at = Column(DateTime, default=datetime.now)
        process = relationship("Process", backref="scores")

    class InnovationIdea(Base):
        __tablename__ = 'innovation_ideas'
        id = Column(Integer, primary_key=True, autoincrement=True)
        employee_sicil_no = Column(String(20))
        employee_name = Column(String(100), nullable=False)
        idea = Column(Text, nullable=False)
        description = Column(Text)
        category = Column(String(100))
        created_at = Column(Date, default=date.today())
        status = Column(String(50), default='Beklemede')
        score = Column(Integer, default=0)
        reviewed_by = Column(String(50))
        reviewed_at = Column(DateTime)

    class Project(Base):
        __tablename__ = 'projects'
        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(200), nullable=False)
        description = Column(Text)
        start_date = Column(Date, default=date.today())
        end_date = Column(Date, default=date.today())
        status = Column(String(50), default='Planning')
        budget = Column(Float, default=0)
        manager_sicil_no = Column(String(20))
        created_at = Column(DateTime, default=datetime.now)

# =============================================================================
# VERİTABANI YÖNETİM SINIFLARI
# =============================================================================

class MySQLManager:
    def __init__(self):
        if not MYSQL_AVAILABLE:
            return
        self.connection = None
        self.cursor = None

    def connect(self):
        if not MYSQL_AVAILABLE:
            st.error("MySQL connector kurulu değil!")
            logger.error("MySQL connector kurulu değil!")
            return False
        try:
            self.connection = mysql.connector.connect(**MYSQL_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            logger.info("MySQL bağlantısı başarılı.")
            return True
        except Error as e:
            st.error(f"MySQL bağlantı hatası: {e}")
            logger.error(f"MySQL bağlantı hatası: {e}")
            self.connection = None
            return False
        except Exception as e:
            st.error(f"MySQL bağlantısı bilinmeyen bir hata nedeniyle başarısız: {e}")
            logger.error(f"MySQL bağlantısı bilinmeyen bir hata nedeniyle başarısız: {e}")
            self.connection = None
            return False

    def disconnect(self):
        if not MYSQL_AVAILABLE:
            return
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None
                logger.info("MySQL bağlantısı kapatıldı.")
        except Exception as e:
            logger.error(f"MySQL disconnect error: {e}")

    def execute_query(self, query, params=None, fetch=True):
        if not MYSQL_AVAILABLE:
            logger.error("MySQL mevcut değil, sorgu çalıştırılamaz.")
            return None
        try:
            if not self.connection or not self.connection.is_connected():
                logger.info("MySQL bağlantısı kesilmiş, yeniden bağlanılıyor.")
                if not self.connect():
                    return None

            self.cursor.execute(query, params or ())

            if fetch:
                result = self.cursor.fetchall()
                return result
            else:
                if not MYSQL_CONFIG.get('autocommit', False):
                    self.connection.commit()
                return self.cursor.rowcount

        except Error as e:
            st.error(f"MySQL sorgu hatası: {e}")
            logger.error(f"MySQL sorgu hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            if self.connection and not MYSQL_CONFIG.get('autocommit', False):
                self.connection.rollback()
            return None
        except Exception as e:
            st.error(f"MySQL genel sorgu hatası: {e}")
            logger.error(f"MySQL genel sorgu hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            return None

    def get_dataframe(self, query, params=None):
        if not MYSQL_AVAILABLE:
            logger.error("MySQL mevcut değil, DataFrame alınamaz.")
            return pd.DataFrame()
        try:
            if not self.connection or not self.connection.is_connected():
                logger.info("MySQL bağlantısı kesilmiş, yeniden bağlanılıyor.")
                if not self.connect():
                    return pd.DataFrame()

            return pd.read_sql(query, self.connection, params=params)
        except Exception as e:
            st.error(f"MySQL DataFrame hatası: {e}")
            logger.error(f"MySQL DataFrame hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            return pd.DataFrame()

class SQLiteManager:
    def __init__(self):
        self.db_path = SQLITE_DB_PATH
        self.ensure_directories()

    def ensure_directories(self):
        dirs_to_create = ["uploads", "logs", "exports"]
        for dir_name in dirs_to_create:
            dir_path = os.path.join(BASE_DIR, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Klasör oluşturuldu: {dir_path}")

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.Error as e:
            logger.error(f"SQLite bağlantı hatası: {e}")
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"SQLite bilinmeyen bağlantı hatası: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query, params=None, fetch=True):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"SQLite sorgu hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            raise

    def get_dataframe(self, query, params=None):
        try:
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"SQLite DataFrame hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            return pd.DataFrame()

# =============================================================================
# GLOBAL VERİTABANI YÖNETİCİSİ
# =============================================================================

if DATABASE_TYPE == 'mysql' and MYSQL_AVAILABLE:
    db_manager = MySQLManager()
else:
    DATABASE_TYPE = 'sqlite'
    db_manager = SQLiteManager()

# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def get_connection():
    if DATABASE_TYPE == 'mysql':
        if not db_manager.connection or not db_manager.connection.is_connected():
            db_manager.connect()
        return db_manager.connection
    else:
        return db_manager.get_connection()

def execute_query(query, params=None, fetch=True):
    return db_manager.execute_query(query, params, fetch)

def get_dataframe(query, params=None):
    return db_manager.get_dataframe(query, params)

def log_action(username, action, details=None, table_name=None, record_id=None):
    try:
        if DATABASE_TYPE == 'mysql':
            query = """
                INSERT INTO logs (username, action, details, table_name, record_id)
                VALUES (%s, %s, %s, %s, %s)
            """
        else:
            query = """
                INSERT INTO logs (username, action, details, table_name, record_id)
                VALUES (?, ?, ?, ?, ?)
            """
        execute_query(query, (username, action, details, table_name, record_id), fetch=False)
        logger.info(f"Log: User='{username}', Action='{action}', Table='{table_name}', Record='{record_id}'")
    except Exception as e:
        logger.error(f"Log kaydetme hatası: {e}")

def test_connection():
    try:
        if DATABASE_TYPE == 'mysql':
            if db_manager.connect():
                db_manager.disconnect()
                return True
            else:
                return False
        else:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
    except Exception as e:
        logger.error(f"Bağlantı test hatası: {e}")
        return False

def create_sqlite_tables():
    """SQLite tabloları oluştur"""
    db_manager.ensure_directories()
    success = False
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'calisan',
                    email TEXT,
                    score INTEGER DEFAULT 0,
                    last_login TEXT,
                    token TEXT,
                    employee_sicil_no TEXT,
                    department TEXT,
                    deleted INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Employees tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Ad_Soyad TEXT NOT NULL,
                    Pozisyon TEXT NOT NULL,
                    Departman TEXT NOT NULL,
                    Yonetici_Adi TEXT,
                    IK_Yonetici_Adi TEXT,
                    Email TEXT,
                    Sicil_No TEXT UNIQUE NOT NULL,
                    İşe_Giriş_Tarihi DATE,
                    Telefon TEXT,
                    Adres TEXT,
                    Dogum_Tarihi DATE,
                    Egitim TEXT,
                    Sertifikalar TEXT,
                    Yetenekler TEXT,
                    deleted INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Diğer tabloları da ekle...
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    description TEXT,
                    department TEXT,
                    created_at DATE DEFAULT CURRENT_DATE,
                    score INTEGER DEFAULT 0,
                    weight REAL DEFAULT 1.0,
                    deleted INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    table_name TEXT,
                    record_id TEXT
                )
            """)

            conn.commit()
            st.success("✅ SQLite tabloları başarıyla oluşturuldu!")
            logger.info("SQLite tabloları başarıyla oluşturuldu.")
            success = True

    except Exception as e:
        st.error(f"❌ SQLite tablo oluşturma hatası: {e}")
        logger.error(f"SQLite tablo oluşturma hatası: {e}")
    return success

def create_tables():
    if DATABASE_TYPE == 'mysql':
        # MySQL tablo oluşturma kodu...
        pass
    else:
        return create_sqlite_tables()

def insert_default_data():
    try:
        default_users = [
            ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin", "admin@effinova.com", "ADM001", "IT"),
            ("mudur", hashlib.sha256("mudur123".encode()).hexdigest(), "mudur", "mudur@effinova.com", "MDR001", "DENETİM MÜDÜRLÜĞÜ"),
            ("calisan", hashlib.sha256("calisan123".encode()).hexdigest(), "calisan", "calisan@effinova.com", "CLS001", "İNSAN KAYNAKLARI GRUP MÜDÜRLÜĞÜ"),
            ("gmy", hashlib.sha256("gmy123".encode()).hexdigest(), "gmy", "gmy@effinova.com", "GMY001", "İKMAL ve OPERASYON GMY")
        ]

        for username, password, role, email, employee_sicil_no, department in default_users:
            try:
                if DATABASE_TYPE == 'mysql':
                    query = "INSERT IGNORE INTO users (username, password, role, email, employee_sicil_no, department) VALUES (%s, %s, %s, %s, %s, %s)"
                else:
                    query = "INSERT OR IGNORE INTO users (username, password, role, email, employee_sicil_no, department) VALUES (?, ?, ?, ?, ?, ?)"
                execute_query(query, (username, password, role, email, employee_sicil_no, department), fetch=False)
                logger.info(f"Varsayılan kullanıcı eklendi/güncellendi: {username}")
            except Exception as e:
                logger.warning(f"Kullanıcı eklenirken hata: {e}")

        st.success("✅ Varsayılan veriler eklendi!")
        logger.info("Varsayılan veriler eklendi.")

    except Exception as e:
        st.error(f"❌ Varsayılan veri ekleme hatası: {e}")
        logger.error(f"Varsayılan veri ekleme hatası: {e}")

def initialize_database():
    if test_connection():
        create_tables_success = create_tables()
        if create_tables_success:
            insert_default_data()
            return True
        else:
            logger.error("Tablolar oluşturulamadığı için veritabanı başlatılamadı.")
            return False
    logger.error("Veritabanı bağlantı testi başarısız olduğu için başlatılamadı.")
    return False