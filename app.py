from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import requests
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rbxmarket_secret_2024_change_me")

# ── Dossiers persistants (/data sur Render avec Disk, sinon local)
BASE_DIR   = os.environ.get("PERSISTENT_DIR", os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "models")
LOGO_DIR   = os.path.join(BASE_DIR, "uploads", "logos")
DB_PATH    = os.path.join(BASE_DIR, "database.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOGO_DIR,   exist_ok=True)

ALLOWED_MODELS = {"rbxm", "rbxmx"}
ALLOWED_IMAGES = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

# ── SQLite ───────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                description TEXT,
                price_type  TEXT    DEFAULT 'free',
                price       INTEGER DEFAULT 0,
                category    TEXT    DEFAULT 'Other',
                file        TEXT    NOT NULL,
                thumbnail   TEXT    DEFAULT '',
                author      TEXT    NOT NULL,
                author_id   INTEGER NOT NULL,
                downloads   INTEGER DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        db.commit()

init_db()

# ── Helpers ──────────────────────────────────────────────────────────────────
def allowed_model(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_MODELS

def allowed_image(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_IMAGES

def get_user_info(cookie):
    try:
        r = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            cookies={".ROBLOSECURITY": cookie}, timeout=8
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_robux_balance(user_id, cookie):
    try:
        r = requests.get(
            f"https://economy.roblox.com/v1/users/{user_id}/currency",
            cookies={".ROBLOSECURITY": cookie}, timeout=8
        )
        return r.json().get("robux", 0) if r.status_code == 200 else None
    except:
        return None

def get_avatar_url(user_id):
    try:
        r = requests.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot"
            f"?userIds={user_id}&size=150x150&format=Png&isCircular=false",
            timeout=8
        )
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                return data[0].get("imageUrl", "")
    except:
        pass
    return ""

def get_setting(key, default=""):
    with get_db() as db:
        row = db.execute("SELECT value FROM site_settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key, value):
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO site_settings (key,value) VALUES (?,?)", (key, value))
        db.commit()

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    with get_db() as db:
        models = [dict(m) for m in db.execute(
            "SELECT * FROM models ORDER BY created_at DESC"
        ).fetchall()]
    return render_template("index.html",
        logged_in = "user_id" in session,
        username  = session.get("username", ""),
        robux     = session.get("robux", 0),
        avatar    = session.get("avatar", ""),
        models    = models,
        site_logo = get_setting("site_logo")
    )

@app.route("/login", methods=["POST"])
def login():
    cookie = request.form.get("roblosecurity", "").strip()
    if not cookie:
        return jsonify({"success": False, "error": "Cookie .ROBLOSECURITY requis"})
    info = get_user_info(cookie)
    if not info:
        return jsonify({"success": False, "error": "Cookie invalide ou expiré."})
    uid   = info["id"]
    uname = info["name"]
    robux = get_robux_balance(uid, cookie)
    avatar = get_avatar_url(uid)
    session.update({
        "user_id": uid, "username": uname,
        "roblosecurity": cookie,
        "robux": robux if robux is not None else 0,
        "avatar": avatar
    })
    return jsonify({"success": True, "username": uname,
                    "robux": session["robux"], "avatar": avatar})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/upload_model", methods=["POST"])
def upload_model():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Non connecté"})
    name       = request.form.get("model_name", "").strip()
    desc       = request.form.get("description", "").strip()
    price_type = request.form.get("price_type", "free")
    price      = request.form.get("price", "0")
    category   = request.form.get("category", "Other").strip()
    if not name:
        return jsonify({"success": False, "error": "Nom du modèle requis"})
    mf = request.files.get("model_file")
    if not mf or not allowed_model(mf.filename):
        return jsonify({"success": False, "error": "Fichier .rbxm ou .rbxmx requis"})

    model_filename = secure_filename(f"{session['user_id']}_{mf.filename}")
    mf.save(os.path.join(UPLOAD_DIR, model_filename))

    thumb_path = ""
    tf = request.files.get("thumbnail")
    if tf and allowed_image(tf.filename):
        tfn = secure_filename(f"thumb_{session['user_id']}_{tf.filename}")
        tf.save(os.path.join(UPLOAD_DIR, tfn))
        thumb_path = tfn

    robux_price = 0
    if price_type == "paid":
        try: robux_price = int(price)
        except: pass

    with get_db() as db:
        cur = db.execute("""
            INSERT INTO models (name,description,price_type,price,category,
                                file,thumbnail,author,author_id)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (name, desc, price_type, robux_price, category,
              model_filename, thumb_path, session["username"], session["user_id"]))
        db.commit()
        model = dict(db.execute("SELECT * FROM models WHERE id=?", (cur.lastrowid,)).fetchone())
    return jsonify({"success": True, "model": model})

@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Non connecté"})
    logo = request.files.get("logo")
    if not logo or not allowed_image(logo.filename):
        return jsonify({"success": False, "error": "Image PNG/JPG/SVG requise"})
    filename = secure_filename(f"logo_{session['user_id']}_{logo.filename}")
    logo.save(os.path.join(LOGO_DIR, filename))
    set_setting("site_logo", filename)
    return jsonify({"success": True, "logo_path": filename})

@app.route("/uploads/models/<path:filename>")
def serve_model(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/uploads/logos/<path:filename>")
def serve_logo(filename):
    return send_from_directory(LOGO_DIR, filename)

@app.route("/download/<int:model_id>")
def download_model(model_id):
    with get_db() as db:
        m = db.execute("SELECT * FROM models WHERE id=?", (model_id,)).fetchone()
        if not m:
            return "Modèle introuvable", 404
        db.execute("UPDATE models SET downloads=downloads+1 WHERE id=?", (model_id,))
        db.commit()
    return send_from_directory(UPLOAD_DIR, m["file"], as_attachment=True)

@app.route("/api/models")
def api_models():
    with get_db() as db:
        models = [dict(m) for m in db.execute(
            "SELECT * FROM models ORDER BY created_at DESC").fetchall()]
    return jsonify(models)

if __name__ == "__main__":
    print("🎮 RBX Market → http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
