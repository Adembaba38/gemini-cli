# CONFIG.PY - VERİTABANI YAPILARI VE YARDIMCI FONKSİYONLAR
# Bu dosya effinova_panel.py'den taşınan tüm veritabanı kodlarını içerir

import os
import logging
import sqlite3
import hashlib
from datetime import datetime, date
from contextlib import contextmanager
import pandas as pd

# --- LOGGING SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "config.log")

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- MYSQL İMPORTLARI ---
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("⚠️ MySQL connector kurulu değil. Sadece SQLite kullanılabilir.")

# --- SQLALCHEMY İMPORTLARI ---
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

# --- VERİTABANI KONFİGÜRASYONU ---
DATABASE_TYPE = 'sqlite'  # 'mysql' veya 'sqlite'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "effinova.db")

# MySQL Konfigürasyonu
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'effinova_db',
    'user': 'root',
    'password': '',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True
}

# --- SQLALCHEMY ORM MODELLERİ ---
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

# --- VERİTABANI YÖNETİM SINIFLARI ---
class MySQLManager:
    def __init__(self):
        if not MYSQL_AVAILABLE:
            return
        self.connection = None
        self.cursor = None

    def connect(self):
        if not MYSQL_AVAILABLE:
            logger.error("MySQL connector kurulu değil!")
            return False
        try:
            self.connection = mysql.connector.connect(**MYSQL_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            logger.info("MySQL bağlantısı başarılı.")
            return True
        except Error as e:
            logger.error(f"MySQL bağlantı hatası: {e}")
            self.connection = None
            return False
        except Exception as e:
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
            logger.error(f"MySQL sorgu hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            if self.connection and not MYSQL_CONFIG.get('autocommit', False):
                self.connection.rollback()
            return None
        except Exception as e:
            logger.error(f"MySQL genel sorgu hatası (SQL: {query[:100]}..., Params: {params}): {e}")
            return None

    def get_dataframe(self, query, params=None):
        if not MYSQL_AVAILABLE:
            logger.error("MySQL mevcut değil, DataFrame alınamaz.")
            return pd.DataFrame()
        try:
            if not self.connection or not self.connection.is_connected():
                logger.info("MySQL bağlantısı kesilmiş, yeniden bağlanıyor.")
                if not self.connect():
                    return pd.DataFrame()
            return pd.read_sql(query, self.connection, params=params)
        except Exception as e:
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
            conn.row_factory = sqlite3.Row
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

# --- GLOBAL VERİTABANI YÖNETİCİSİ ---
db_manager = MySQLManager() if DATABASE_TYPE == 'mysql' and MYSQL_AVAILABLE else SQLiteManager()

# --- YARDIMCI VERİTABANI FONKSİYONLARI ---
def get_connection():
    if DATABASE_TYPE == 'mysql':
        if not db_manager.connection or not db_manager.connection.is_connected():
            db_manager.connect()
        return db_manager.connection
    else:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            logger.error(f"SQLite get_connection direct call error: {e}")
            return None

def execute_query(query, params=None, fetch=True):
    return db_manager.execute_query(query, params, fetch)

def get_dataframe(query, params=None):
    return db_manager.get_dataframe(query, params)

def log_action(username, action, details=None, table_name=None, record_id=None):
    """Kullanıcı eylemlerini logla"""
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
    """Veritabanı bağlantısını test et"""
    try:
        if DATABASE_TYPE == 'mysql':
            if db_manager.connect():
                return True
            else:
                logger.error("❌ MySQL bağlantısı başarısız!")
                return False
        else:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
    except Exception as e:
        logger.error(f"Bağlantı test hatası: {e}")
        return False

# --- TABLO OLUŞTURMA FONKSİYONLARI ---
def create_mysql_tables():
    """MySQL tabloları oluştur"""
    tables = {
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'mudur', 'calisan', 'gmy') DEFAULT 'calisan',
                email VARCHAR(100),
                score INT DEFAULT 0,
                last_login TIMESTAMP NULL,
                token VARCHAR(255),
                employee_sicil_no VARCHAR(20),
                department VARCHAR(100),
                deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_sicil_no (employee_sicil_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'employees': """
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Ad_Soyad VARCHAR(100) NOT NULL,
                Pozisyon VARCHAR(100) NOT NULL,
                Departman VARCHAR(100) NOT NULL,
                Yonetici_Adi VARCHAR(100),
                Email VARCHAR(100),
                Sicil_No VARCHAR(20) UNIQUE NOT NULL,
                İşe_Giriş_Tarihi DATE,
                Telefon VARCHAR(20),
                Adres TEXT,
                Dogum_Tarihi DATE,
                Egitim TEXT,
                Sertifikalar TEXT,
                Yetenekler TEXT,
                deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_sicil_no (Sicil_No),
                INDEX idx_departman (Departman)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'processes': """
            CREATE TABLE IF NOT EXISTS processes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                process_name VARCHAR(200) NOT NULL,
                description TEXT,
                department VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score INT DEFAULT 0,
                weight DECIMAL(3,2) DEFAULT 1.0,
                deleted BOOLEAN DEFAULT FALSE,
                INDEX idx_department (department)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'process_scores': """
            CREATE TABLE IF NOT EXISTS process_scores (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_name VARCHAR(100) NOT NULL,
                employee_sicil_no VARCHAR(20),
                process_id INT,
                tarih DATE NOT NULL,
                cikti INT DEFAULT 0,
                kalite INT DEFAULT 0,
                strateji INT DEFAULT 0,
                inovasyon INT DEFAULT 0,
                zaman DECIMAL(10,2) DEFAULT 0,
                ekstra INT DEFAULT 0,
                ekstra_aciklama TEXT,
                toplam_skor DECIMAL(10,2) DEFAULT 0,
                onay ENUM('Beklemede', 'Onaylandı', 'Reddedildi') DEFAULT 'Beklemede',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (process_id) REFERENCES processes(id) ON DELETE CASCADE,
                INDEX idx_employee (employee_sicil_no),
                INDEX idx_tarih (tarih)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'innovation_ideas': """
            CREATE TABLE IF NOT EXISTS innovation_ideas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_sicil_no VARCHAR(20),
                employee_name VARCHAR(100) NOT NULL,
                idea TEXT NOT NULL,
                description TEXT,
                category VARCHAR(100),
                created_at DATE DEFAULT (CURRENT_DATE),
                status ENUM('Beklemede', 'Değerlendiriliyor', 'Onaylandı', 'Reddedildi') DEFAULT 'Beklemede',
                score INT DEFAULT 0,
                reviewed_by VARCHAR(50),
                reviewed_at TIMESTAMP NULL,
                INDEX idx_employee (employee_sicil_no),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'badges': """
            CREATE TABLE IF NOT EXISTS badges (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_sicil_no VARCHAR(20),
                badge_title VARCHAR(100) NOT NULL,
                badge_emoji VARCHAR(10) DEFAULT '🏅',
                badge_points INT DEFAULT 0,
                badge_description TEXT,
                awarded_date DATE DEFAULT (CURRENT_DATE),
                awarded_by VARCHAR(50),
                INDEX idx_employee (employee_sicil_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'logs': """
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50),
                action VARCHAR(200) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                table_name VARCHAR(50),
                record_id VARCHAR(50),
                INDEX idx_username (username),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        'projects': """
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                start_date DATE,
                end_date DATE,
                status ENUM('Planning', 'In Progress', 'Completed', 'On Hold', 'Cancelled') DEFAULT 'Planning',
                budget DECIMAL(15,2) DEFAULT 0,
                manager_sicil_no VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_manager (manager_sicil_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    }

    success = False
    try:
        if db_manager.connect():
            for table_name, create_sql in tables.items():
                logger.info(f"MySQL tablosu oluşturuluyor/güncelleniyor: {table_name}")
                db_manager.execute_query(create_sql, fetch=False)
            logger.info("MySQL tabloları başarıyla oluşturuldu.")
            success = True
    except Exception as e:
        logger.error(f"MySQL tablo oluşturma hatası: {e}")
    finally:
        db_manager.disconnect()
    return success

def create_sqlite_tables():
    """SQLite tabloları oluştur"""
    db_manager.ensure_directories()
    success = False
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ana tablolar
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Ad_Soyad TEXT NOT NULL,
                    Pozisyon TEXT NOT NULL,
                    Departman TEXT NOT NULL,
                    Yonetici_Adi TEXT,
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
                CREATE TABLE IF NOT EXISTS process_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id INTEGER,
                    employee_name TEXT NOT NULL,
                    employee_sicil_no TEXT,
                    cikti INTEGER DEFAULT 0,
                    kalite INTEGER DEFAULT 0,
                    strateji INTEGER DEFAULT 0,
                    inovasyon INTEGER DEFAULT 0,
                    zaman REAL DEFAULT 0,
                    ekstra INTEGER DEFAULT 0,
                    ekstra_aciklama TEXT,
                    toplam_skor REAL DEFAULT 0,
                    tarih DATE DEFAULT CURRENT_DATE,
                    onay TEXT DEFAULT 'Beklemede',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_sicil_no) REFERENCES employees(Sicil_No),
                    FOREIGN KEY (process_id) REFERENCES processes(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS innovation_ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_sicil_no TEXT,
                    employee_name TEXT NOT NULL,
                    idea TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    created_at DATE DEFAULT CURRENT_DATE,
                    status TEXT DEFAULT 'Beklemede',
                    score INTEGER DEFAULT 0,
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP,
                    FOREIGN KEY (employee_sicil_no) REFERENCES employees(Sicil_No)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_sicil_no TEXT,
                    badge_title TEXT NOT NULL,
                    badge_emoji TEXT DEFAULT '🏅',
                    badge_points INTEGER DEFAULT 0,
                    badge_description TEXT,
                    awarded_date TEXT DEFAULT CURRENT_DATE,
                    awarded_by TEXT,
                    FOREIGN KEY (employee_sicil_no) REFERENCES employees(Sicil_No)
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
                    record_id TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_date DATE,
                    end_date DATE,
                    status TEXT DEFAULT 'Planning',
                    budget REAL DEFAULT 0,
                    manager_sicil_no TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (manager_sicil_no) REFERENCES employees(Sicil_No)
                )
            """)
            
            conn.commit()
            logger.info("SQLite tabloları başarıyla oluşturuldu.")
            success = True
    except Exception as e:
        logger.error(f"SQLite tablo oluşturma hatası: {e}")
    return success

def create_tables():
    """Veritabanı tipine göre tabloları oluştur"""
    if DATABASE_TYPE == 'mysql':
        return create_mysql_tables()
    else:
        return create_sqlite_tables()

# --- MİGRASYON VE BAŞLANGIÇ FONKSİYONLARI ---
def check_and_migrate_data():
    """Veritabanı migrasyonu"""
    try:
        if DATABASE_TYPE == 'sqlite':
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Eksik kolonları ekle
                employee_cols_to_add = [
                    "name TEXT", "department TEXT", "position TEXT",
                    "email TEXT", "sicil_no TEXT", "start_date TEXT", "phone TEXT"
                ]
                for col_def in employee_cols_to_add:
                    col_name = col_def.split(' ')[0]
                    try:
                        cursor.execute(f"ALTER TABLE employees ADD COLUMN {col_def}")
                        logger.info(f"employees tablosuna '{col_name}' kolonu eklendi.")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            logger.debug(f"employees tablosunda '{col_name}' kolonu zaten mevcut.")
                        else:
                            logger.error(f"employees tablosuna '{col_name}' kolonu eklenirken hata: {e}")

                user_cols_to_add = ["employee_sicil_no TEXT", "department TEXT"]
                for col_def in user_cols_to_add:
                    col_name = col_def.split(' ')[0]
                    try:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
                        logger.info(f"users tablosuna '{col_name}' kolonu eklendi.")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            logger.debug(f"users tablosunda '{col_name}' kolonu zaten mevcut.")

                # Veri migrasyonu
                cursor.execute("""
                    UPDATE employees
                    SET name = Ad_Soyad,
                        department = Departman,
                        position = Pozisyon
                    WHERE name IS NULL OR department IS NULL OR position IS NULL
                """)
                conn.commit()

        logger.info("Veri migrasyonu başarıyla tamamlandı.")
    except Exception as e:
        logger.error(f"Veri migrasyonu hatası: {e}")

def insert_default_data():
    """Varsayılan verileri ekle"""
    try:
        # Varsayılan çalışanlar
        default_employees = [
            ("İkmal ve Operasyon GMY", "İkmal ve Operasyon GMY", "İKMAL ve OPERASYON GMY", "GENEL MÜDÜR", "ikmal.gmy@effinova.com", "GMY001", str(date.today())),
            ("Denetim Müdürü", "Denetim Müdürü", "DENETİM MÜDÜRLÜĞÜ", "GENEL MÜDÜR", "denetim.mud@effinova.com", "MDR001", str(date.today())),
            ("İK Grup Müdürü", "İK Uzmanı", "İNSAN KAYNAKLARI GRUP MÜDÜRLÜĞÜ", "MALİ VE İDARİ İŞLER GN.MDR.", "ik.gm@effinova.com", "CLS001", str(date.today())),
            ("Satınalma Müdürü", "Satınalma Müdürü", "SATIN ALMA MÜDÜRLÜĞÜ", "MALİ VE İDARİ İŞLER GN.MDR.", "satin.mud@effinova.com", "ADM001", str(date.today()))
        ]

        # Çalışanları ekle
        if DATABASE_TYPE == 'mysql':
            emp_query = """
                INSERT IGNORE INTO employees
                (Ad_Soyad, Pozisyon, Departman, Yonetici_Adi, Email, Sicil_No, İşe_Giriş_Tarihi)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        else:
            emp_query = """
                INSERT OR IGNORE INTO employees
                (Ad_Soyad, Pozisyon, Departman, Yonetici_Adi, Email, Sicil_No, İşe_Giriş_Tarihi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
        for ad_soyad, pozisyon, departman, yonetici_adi, email, sicil_no, ise_giris_tarihi in default_employees:
            try:
                execute_query(emp_query, (ad_soyad, pozisyon, departman, yonetici_adi, email, sicil_no, ise_giris_tarihi), fetch=False)
                logger.info(f"Varsayılan çalışan eklendi: {ad_soyad} ({sicil_no})")
            except Exception as e:
                logger.warning(f"Çalışan eklenirken hata: {e}")

        # Varsayılan kullanıcılar
        default_users = [
            ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin", "admin@effinova.com", "ADM001", "IT"),
            ("mudur", hashlib.sha256("mudur123".encode()).hexdigest(), "mudur", "mudur@effinova.com", "MDR001", "DENETİM MÜDÜRLÜĞÜ"),
            ("calisan", hashlib.sha256("calisan123".encode()).hexdigest(), "calisan", "calisan@effinova.com", "CLS001", "İNSAN KAYNAKLARI GRUP MÜDÜRLÜĞÜ"),
            ("gmy", hashlib.sha256("gmy123".encode()).hexdigest(), "gmy", "gmy@effinova.com", "GMY001", "İKMAL ve OPERASYON GMY")
        ]

        # Kullanıcıları ekle
        if DATABASE_TYPE == 'mysql':
            user_query = """
                INSERT IGNORE INTO users
                (username, password, role, email, employee_sicil_no, department)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
        else:
            user_query = """
                INSERT OR IGNORE INTO users
                (username, password, role, email, employee_sicil_no, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
        for username, password, role, email, employee_sicil_no, department in default_users:
            try:
                execute_query(user_query, (username, password, role, email, employee_sicil_no, department), fetch=False)
                logger.info(f"Varsayılan kullanıcı eklendi: {username}")
            except Exception as e:
                logger.warning(f"Kullanıcı eklenirken hata: {e}")

        logger.info("Varsayılan veriler eklendi.")
    except Exception as e:
        logger.error(f"Varsayılan veri ekleme hatası: {e}")

def initialize_database():
    """Veritabanını başlat"""
    try:
        if test_connection():
            create_tables_success = create_tables()
            if not create_tables_success:
                logger.error("Tablolar oluşturulamadı.")
                return False

            if DATABASE_TYPE == 'sqlite':
                check_and_migrate_data()

            insert_default_data()

            logger.info("Veritabanı başlatma işlemi tamamlandı.")
            return True
        else:
            logger.error("Veritabanı bağlantı testi başarısız.")
            return False
    except Exception as e:
        logger.critical(f"Veritabanı başlatma hatası: {e}")
        return False

# --- SQLALCHEMY YÖNETİCİSİ ---
SQLITE_ENGINE = None
if SQLALCHEMY_AVAILABLE:
    SQLITE_ENGINE = create_engine(f"sqlite:///{SQLITE_DB_PATH}")

    def get_mysql_engine():
        if not MYSQL_AVAILABLE:
            return None
        mysql_url = f"mysql+mysqlconnector://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        return create_engine(mysql_url, echo=False)

class SQLAlchemyManager:
    def __init__(self):
        if not SQLALCHEMY_AVAILABLE:
            self.engine = None
            self.SessionLocal = None
            return

        if DATABASE_TYPE == 'mysql' and MYSQL_AVAILABLE:
            self.engine = get_mysql_engine()
        else:
            self.engine = SQLITE_ENGINE

        if self.engine:
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        else:
            self.SessionLocal = None

    def get_session(self):
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            logger.error("SQLAlchemy kurulu değil.")
            return None
        return self.SessionLocal()

    def init_tables(self):
        if not SQLALCHEMY_AVAILABLE or not self.engine:
            logger.warning("SQLAlchemy kullanılamıyor.")
            return False
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("SQLAlchemy tabloları oluşturuldu.")
            return True
        except Exception as e:
            logger.error(f"SQLAlchemy tablo oluşturma hatası: {e}")
            return False

sqlalchemy_manager = SQLAlchemyManager() if SQLALCHEMY_AVAILABLE else None