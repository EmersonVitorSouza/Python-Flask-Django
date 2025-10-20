import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

try:
    import psycopg
except ImportError:
    psycopg = None

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "segredo123")

DATABASE_URL = os.environ.get("DATABASE_URL")  # Postgres remoto

def get_conn():
    if DATABASE_URL and psycopg:
        return psycopg.connect(DATABASE_URL, sslmode="require")
    else:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        return conn

# ---------------------------
# ROTAS
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Preencha usuário e senha.", "warning")
            return redirect(url_for("login"))

        # LOGIN
        user = None
        if DATABASE_URL and psycopg:
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT username FROM usuarios WHERE username=%s AND senha=%s",
                            (username, password)
                        )
                        user = cur.fetchone()
            except Exception as e:
                print("Erro login Postgres:", e)
        else:
            try:
                conn = get_conn()
                user = conn.execute(
                    "SELECT username FROM usuarios WHERE username=? AND senha=?",
                    (username, password)
                ).fetchone()
                conn.close()
            except Exception as e:
                print("Erro login SQLite:", e)

        if user:
            session["user"] = user[0] if DATABASE_URL else user["username"]
            return redirect(url_for("dashboard"))
        else:
            flash("Usuário ou senha incorretos.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Preencha usuário e senha.", "warning")
            return redirect(url_for("register_page"))

        # CADASTRO
        success = False
        if DATABASE_URL and psycopg:
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO usuarios (username, senha) VALUES (%s, %s)",
                            (username, password)
                        )
                        conn.commit()
                        success = True
            except Exception as e:
                print("Erro registro Postgres:", e)
        else:
            try:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                    (username, password)
                )
                conn.commit()
                conn.close()
                success = True
            except Exception as e:
                print("Erro registro SQLite:", e)

        if success:
            flash("Usuário criado com sucesso! Faça login.", "success")
            return redirect(url_for("login"))
        else:
            flash("Usuário já existe ou houve erro.", "warning")
            return redirect(url_for("register_page"))

    return render_template("register.html")


@app.route("/usuarios")
def usuarios():
    if "user" not in session:
        return redirect(url_for("login"))

    # LISTA USUÁRIOS
    users = []
    if DATABASE_URL and psycopg:
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT username FROM usuarios ORDER BY id ASC")
                    rows = cur.fetchall()
                    users = [r[0] for r in rows]
        except Exception as e:
            print("Erro listar usuários Postgres:", e)
    else:
        try:
            conn = get_conn()
            rows = conn.execute("SELECT username FROM usuarios ORDER BY id ASC").fetchall()
            users = [r["username"] for r in rows]
            conn.close()
        except Exception as e:
            print("Erro listar usuários SQLite:", e)

    return render_template("usuarios.html", users=users, current_user=session.get("user"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
