import os
import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")

with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                senha VARCHAR(100) NOT NULL
            );
        """)
        conn.commit()

print("Tabela criada com sucesso!")
