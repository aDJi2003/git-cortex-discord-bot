# core/database.py
import os
import hashlib
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("DB_SERVER"),
    'database': os.getenv("DB_DATABASE"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'port': os.getenv("DB_PORT", 3306)
}

def get_db_connection():
    """Membuat dan mengembalikan koneksi ke database MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error saat menghubungkan ke MySQL: {e}")
        return None

def setup_database():
    """Membuat tabel cache di MySQL jika belum ada."""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS QueryCache (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                QueryHash VARCHAR(64) UNIQUE NOT NULL,
                FullQuery TEXT NOT NULL,
                Response TEXT NOT NULL,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Database setup berhasil. Tabel 'QueryCache' siap digunakan di MySQL.")
    except Error as e:
        print(f"Error saat setup database: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def _hash_query(query: str) -> str:
    """Membuat SHA-256 hash dari sebuah string query."""
    return hashlib.sha256(query.encode('utf-8')).hexdigest()

def get_cached_response(query: str) -> str | None:
    """Mencari respons di database MySQL berdasarkan hash dari query."""
    query_hash = _hash_query(query)
    conn = get_db_connection()
    if not conn:
        return None
        
    response = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Response FROM QueryCache WHERE QueryHash = %s", (query_hash,))
        row = cursor.fetchone()
        if row:
            response = row[0]
            print(f"Cache HIT untuk query: {query[:50]}...")
    except Error as e:
        print(f"Error saat mengambil cache: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return response

def cache_response(query: str, response: str):
    """Menyimpan query dan respons baru ke dalam database MySQL."""
    query_hash = _hash_query(query)
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        sql = "INSERT INTO QueryCache (QueryHash, FullQuery, Response) VALUES (%s, %s, %s)"
        val = (query_hash, query, response)
        cursor.execute(sql, val)
        conn.commit()
        print(f"Cache SAVED untuk query: {query[:50]}...")
    except Error as e:
        print(f"Error saat menyimpan cache: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

setup_database()