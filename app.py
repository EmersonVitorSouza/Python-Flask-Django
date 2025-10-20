import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "segredo123")

# Lê DATABASE_URL (definida no Render). Se não existir, tenta usar sqlite local (útil para dev).
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if DATABASE_URL:
        # Em Render, geralmente a URL já está pronta; forçamos sslmode=require por segurança.
        return psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=RealDictCursor)
    else:
        import sqlite3
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    if DATABASE_URL:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            senha VARCHAR(200) NOT NULL
        );
        """)
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = get_conn()
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
        """)
        conn.commit()
        conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_conn()
        if DATABASE_URL:
            cur = conn.cursor()
            cur.execute("SELECT * FROM usuarios WHERE username=%s AND senha=%s", (username, password))
            user = cur.fetchone()
            cur.close()
            conn.close()
        else:
            user = conn.execute("SELECT * FROM usuarios WHERE username=? AND senha=?", (username, password)).fetchone()
            conn.close()

        if user:
            flash("Login bem-sucedido!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Usuário ou senha incorretos.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"].strip()
    password = request.form["password"].strip()

    conn = get_conn()
    try:
        if DATABASE_URL:
            cur = conn.cursor()
            cur.execute("INSERT INTO usuarios (username, senha) VALUES (%s, %s)", (username, password))
            conn.commit()
            cur.close()
            conn.close()
        else:
            conn.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
        flash("Usuário criado com sucesso! Faça login.", "success")
    except Exception as e:
        # IntegrityError para duplicidade; mensagens genéricas para não vazar detalhes
        flash("Esse nome de usuário já existe (ou houve erro).", "warning")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    return "<h1>Bem-vindo ao painel!</h1>"

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
