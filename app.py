# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2.extras import RealDictCursor

# fallback sqlite
import sqlite3

app = Flask(__name__)

# Secret key fixa para sessões (em produção, use variável de ambiente)
app.secret_key = "segredo123"

# Lê DATABASE_URL (definida no Render). Se não existir, o app usa sqlite local.
DATABASE_URL = os.environ.get("DATABASE_URL")


# ------------------------
# FUNÇÕES DE CONEXÃO
# ------------------------
def get_conn():
    """
    Retorna uma conexão: Postgres (psycopg2) se DATABASE_URL existir,
    caso contrário retorna sqlite3.Connection.
    """
    if DATABASE_URL:
        # Forçar sslmode=require para segurança em conexões externas
        return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """
    Cria tabela 'usuarios' se não existir (Postgres ou SQLite).
    """
    if DATABASE_URL:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                senha VARCHAR(200) NOT NULL
            );
            """
        )
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            );
            """
        )
        conn.commit()
        conn.close()


# Inicializa DB ao iniciar o app (útil pro ambiente sem DB externo)
init_db()


# ------------------------
# ROTAS
# ------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    """
    Rota de login.
    GET -> mostra form
    POST -> tenta logar
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Validação simples
        if not username or not password:
            flash("Preencha usuário e senha.", "warning")
            return redirect(url_for("login"))

        conn = get_conn()
        try:
            if DATABASE_URL:
                cur = conn.cursor()
                cur.execute("SELECT username FROM usuarios WHERE username=%s AND senha=%s", (username, password))
                user = cur.fetchone()
                cur.close()
                conn.close()
                found = bool(user)
            else:
                user = conn.execute(
                    "SELECT username FROM usuarios WHERE username=? AND senha=?", (username, password)
                ).fetchone()
                conn.close()
                found = bool(user)
        except Exception as e:
            # Log nos logs do servidor; mostra mensagem genérica ao usuário
            print("Erro ao consultar DB (login):", e)
            found = False

        if found:
            # simples: guarda apenas o username na sessão
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Usuário ou senha incorretos.", "danger")
            return redirect(url_for("login"))

    # GET
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    """
    Rota de cadastro.
    GET -> mostra form
    POST -> cria usuário (se não duplicado)
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Preencha usuário e senha.", "warning")
            return redirect(url_for("register_page"))

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
            return redirect(url_for("login"))
        except Exception as e:
            # Possível duplicidade ou outro erro
            print("Erro ao inserir usuário:", e)
            flash("Esse nome de usuário já existe (ou houve erro).", "warning")
            try:
                conn.close()
            except:
                pass
            return redirect(url_for("register_page"))

    # GET
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    """
    Rota protegida: só acessível quando 'user' está na sessão.
    Exibe lista de usuários cadastrados (apenas usernames).
    """
    if "user" not in session:
        return redirect(url_for("login"))

    # Buscando lista de usuários
    conn = get_conn()
    try:
        if DATABASE_URL:
            cur = conn.cursor()
            cur.execute("SELECT username FROM usuarios ORDER BY id ASC")
            rows = cur.fetchall()  # lista de dicts (RealDictCursor)
            # extrai lista de strings
            users = [r["username"] for r in rows]
            cur.close()
            conn.close()
        else:
            rows = conn.execute("SELECT username FROM usuarios ORDER BY id ASC").fetchall()
            users = [r["username"] for r in rows]
            conn.close()
    except Exception as e:
        print("Erro ao listar usuários:", e)
        users = []

    return render_template("dashboard.html", users=users, current_user=session.get("user"))


@app.route("/logout")
def logout():
    """
    Logout simples: limpa sessão e redireciona ao login.
    """
    session.pop("user", None)
    return redirect(url_for("login"))


# ------------------------
# RUN (apenas se executar diretamente)
# ------------------------
if __name__ == "__main__":
    # Para desenvolvimento local
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
