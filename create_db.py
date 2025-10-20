import os
import sqlite3

# tenta importar psycopg (nova API)
try:
    import psycopg
except ImportError:
    psycopg = None

DATABASE_URL = os.environ.get("DATABASE_URL")  # Render ou Postgres remoto
SQLITE_FILE = "users.db"

def create_tables_postgres():
    with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    senha VARCHAR(200) NOT NULL
                );
            """)
        print("Tabela 'usuarios' criada no Postgres com sucesso.")

def create_tables_sqlite():
    conn = sqlite3.connect(SQLITE_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    print(f"Tabela 'usuarios' criada no SQLite ({SQLITE_FILE}).")

if DATABASE_URL and psycopg:
    create_tables_postgres()
else:
    create_tables_sqlite()
