import os
import json
import time
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import sqlite3
import requests

# Try to import psycopg2 (Postgres)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    has_psycopg2 = True
except ImportError:
    has_psycopg2 = False

# Redirection forcée
sys.stdout = sys.stderr

app = Flask(__name__)
CORS(app)

CORS(app)

# --- DATABASE CONFIGURATION ---
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:B%40c%40lori%402015@db.wfdoqlomlpsowxzwfxfu.supabase.co:5432/postgres?sslmode=require"

# Nettoyage de l'URL pour éviter les erreurs de paramètres (ex: pgbouncer)
if DATABASE_URL and "?" in DATABASE_URL:
    base_url = DATABASE_URL.split("?")[0]
    # On garde seulement sslmode si présent car c'est souvent requis
    if "sslmode=require" in DATABASE_URL:
        DATABASE_URL = base_url + "?sslmode=require"
    else:
        DATABASE_URL = base_url

# --- WAVE CONFIGURATION ---
WAVE_API_KEY = "wave_priv_test_..." # À remplacer par votre clé réelle

# --- ORANGE MONEY CONFIGURATION ---
OM_CLIENT_ID = "6motYSPYXgCEZHNZjmTOUQcm2Koo2Hix"
OM_CLIENT_SECRET = "gnenZ2WixE1mHHrCTky0pGw7fDjGIHbxmFHtacR3zNLr"
OM_MERCHANT_KEY = "487087"
OM_AUTH_URL = "https://api.orange.com/oauth/v3/token"
OM_PAY_URL = "https://api.orange.com/orange-money-webpay/dev/v1/webpayment" # Gardez 'dev' pour les tests

# --- NOTIFICATION CONFIGURATION ---
# Renseignez ces variables pour recevoir des notifications en temps réel
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "7624283697:AAHwXqRFTcgB8F_Hlp5poNJ6rxpr8ohZAg8"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or "848554777"

SMTP_SERVER = os.environ.get("SMTP_SERVER") or "smtp.gmail.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or 587)
SMTP_USER = os.environ.get("SMTP_USER") or ""                  # Votre email expéditeur (ex: contact@douerashop.sn)
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") or ""          # Mot de passe d'application SMTP
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or ""              # Votre adresse email de réception admin

# WhatsApp Notification (CallMeBot - Gratuit et Personnel pour l'admin)
WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE") or ""        # Numéro au format international (ex: "+221781607468")
WHATSAPP_API_KEY = os.environ.get("WHATSAPP_API_KEY") or ""    # Clé API obtenue via CallMeBot

# WhatsApp Pro (UltraMsg - Optionnel)
ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID") or ""
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN") or ""

def send_admin_notification(order_id, customer_name, total, items_list, phone, address, payment_method, status="En attente"):
    # Log console fallback
    sys.stderr.write(f"🔔 NOTIFICATION ADMIN : Commande {order_id} ({status}) - {customer_name} - {total} XOF\n")
    
    # Formatage des articles
    items_desc = ""
    try:
        if isinstance(items_list, str):
            items_list = json.loads(items_list)
        
        if isinstance(items_list, list):
            for item in items_list:
                items_desc += f"- {item.get('name', 'Produit')} x{item.get('quantity', 1)} ({int(item.get('price', 0)):,} XOF)\n"
        else:
            items_desc = "Format des articles non supporté"
    except Exception as e:
        items_desc = f"Erreur de lecture des articles : {str(e)}"

    status_icon = "🟢" if status == "Payé" else "🔔"
    title_text = "Commande PAYÉE !" if status == "Payé" else "Nouvelle Commande !"

    # 1. Envoi par Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            telegram_msg = (
                f"{status_icon} <b>{title_text} - Douéra Shop</b>\n\n"
                f"📦 <b>Numéro :</b> <code>{order_id}</code>\n"
                f"👤 <b>Client :</b> {customer_name}\n"
                f"📞 <b>Téléphone :</b> {phone}\n"
                f"📍 <b>Adresse :</b> {address}\n"
                f"💳 <b>Paiement :</b> {payment_method}\n"
                f"💰 <b>Total :</b> <b>{int(total):,} XOF</b>\n\n"
                f"🛍️ <b>Détails des articles :</b>\n{items_desc}"
            )
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": telegram_msg,
                "parse_mode": "HTML"
            }
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code != 200:
                sys.stderr.write(f"Telegram API response: {res.status_code} - {res.text}\n")
        except Exception as e:
            sys.stderr.write(f"Telegram Notification Error: {e}\n")

    # 2. Envoi par E-mail
    if SMTP_USER and SMTP_PASSWORD and ADMIN_EMAIL:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = ADMIN_EMAIL
            msg['Subject'] = f"{status_icon} Douéra Shop - {title_text} ({order_id})"

            body = f"""Bonjour Administrateur,

{title_text} sur Douéra Shop.

Détails de la commande :
------------------------------------------
ID Commande : {order_id}
Client : {customer_name}
Téléphone : {phone}
Adresse : {address}
Mode de Paiement : {payment_method}
Statut : {status}
Total : {int(total):,} XOF
------------------------------------------

Articles commandés :
{items_desc}

Rendez-vous sur votre tableau de bord pour traiter cette commande.
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, ADMIN_EMAIL, msg.as_string())
            server.quit()
        except Exception as e:
            sys.stderr.write(f"Email Notification Error: {e}\n")

    # 3. Envoi par WhatsApp (CallMeBot - Gratuit/Personnel)
    if WHATSAPP_PHONE and WHATSAPP_API_KEY:
        try:
            wa_text = (
                f"🔔 *{title_text} - Douéra Shop*\n\n"
                f"📦 *Numéro :* {order_id}\n"
                f"👤 *Client :* {customer_name}\n"
                f"📞 *Tél :* {phone}\n"
                f"📍 *Adresse :* {address}\n"
                f"💳 *Paiement :* {payment_method}\n"
                f"💰 *Total :* {int(total):,} XOF\n\n"
                f"🛍️ *Détails :*\n{items_desc.replace('- ', '• ')}"
            )
            url = "https://api.callmebot.com/whatsapp.php"
            params = {
                "phone": WHATSAPP_PHONE,
                "text": wa_text,
                "apikey": WHATSAPP_API_KEY
            }
            res = requests.get(url, params=params, timeout=10)
            if res.status_code != 200:
                sys.stderr.write(f"CallMeBot WhatsApp response: {res.status_code} - {res.text}\n")
        except Exception as e:
            sys.stderr.write(f"CallMeBot WhatsApp Error: {e}\n")

    # 4. Envoi par WhatsApp (UltraMsg - Professionnel)
    if ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN and WHATSAPP_PHONE:
        try:
            wa_text = (
                f"🔔 *{title_text} - Douéra Shop*\n\n"
                f"📦 *Numéro :* {order_id}\n"
                f"👤 *Client :* {customer_name}\n"
                f"📞 *Tél :* {phone}\n"
                f"📍 *Adresse :* {address}\n"
                f"💳 *Paiement :* {payment_method}\n"
                f"💰 *Total :* {int(total):,} XOF\n\n"
                f"🛍️ *Détails :*\n{items_desc.replace('- ', '• ')}"
            )
            url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
            payload = {
                "token": ULTRAMSG_TOKEN,
                "to": WHATSAPP_PHONE,
                "body": wa_text,
                "priority": 10
            }
            res = requests.post(url, data=payload, timeout=10)
            if res.status_code != 200:
                sys.stderr.write(f"UltraMsg WhatsApp response: {res.status_code} - {res.text}\n")
        except Exception as e:
            sys.stderr.write(f"UltraMsg WhatsApp Error: {e}\n")

def get_db_connection():
    try:
        if DATABASE_URL and has_psycopg2:
            return psycopg2.connect(DATABASE_URL, connect_timeout=10)
    except Exception as e:
        sys.stderr.write(f"Postgres failed: {e}\n")
    
    db_path = '/tmp/douera.db' if (os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')) else os.path.join(os.path.dirname(__file__), 'douera.db')
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

class DB:
    def __init__(self, conn):
        self.conn = conn
        self.is_postgres = hasattr(conn, 'tpc_begin')
        if self.is_postgres:
            from psycopg2.extras import RealDictCursor
            self.cur = conn.cursor(cursor_factory=RealDictCursor)
        else:
            self.cur = conn.cursor()

    def execute(self, query, params=None):
        if self.is_postgres:
            query = query.replace('?', '%s')
        if params:
            self.cur.execute(query, params)
        else:
            self.cur.execute(query)
        return self.cur

    def fetchall(self):
        rows = self.cur.fetchall()
        return [dict(r) for r in rows]

    def fetchone(self):
        row = self.cur.fetchone()
        if not row: return None
        return dict(row)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        is_postgres = hasattr(conn, 'tpc_begin')
        id_type = "TEXT PRIMARY KEY"
        
        cur.execute(f"CREATE TABLE IF NOT EXISTS users (id {id_type}, email TEXT UNIQUE, password TEXT, name TEXT, role TEXT, status TEXT, address TEXT, phone TEXT)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS products (id {id_type}, name TEXT, price INTEGER, category TEXT, image TEXT, stock INTEGER, description TEXT, specs TEXT, media TEXT)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS orders (id {id_type}, userId TEXT, date TEXT, method TEXT, status TEXT, total INTEGER, items TEXT, customer_firstname TEXT, customer_lastname TEXT, customer_address TEXT, customer_phone TEXT)")
        
        try:
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS media TEXT" if is_postgres else "ALTER TABLE products ADD COLUMN media TEXT")
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_id TEXT" if is_postgres else "ALTER TABLE orders ADD COLUMN review_id TEXT")
        except:
            conn.rollback()
            pass
            
        cur.execute(f"CREATE TABLE IF NOT EXISTS reviews (id {id_type}, orderId TEXT, productId TEXT, userId TEXT, userName TEXT, rating_product INTEGER, rating_service INTEGER, comment TEXT, admin_reply TEXT, date TEXT)")

        cur.execute('SELECT count(*) FROM users')
        if cur.fetchone()[0] == 0:
            p = "(%s, %s, %s, %s, %s, %s)" if is_postgres else "(?, ?, ?, ?, ?, ?)"
            cur.execute(f"INSERT INTO users (id, email, password, name, role, status) VALUES {p}", ('u1', 'admin@douerashop.sn', 'admin123', 'Super Admin', 'super_admin', 'active'))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        sys.stderr.write(f"Init DB Error: {e}\n")

# --- API ROUTES ---

@app.route('/api/health')
def health():
    db_type = "Inconnu"
    error_msg = None
    try:
        # Tentative de connexion pour test
        if DATABASE_URL and has_psycopg2:
            try:
                conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
                db_type = "Postgres (SÉCURISÉ & PERMANENT) ✅"
                conn.close()
            except Exception as e:
                error_msg = str(e)
                db_type = f"SQLite (TEMPORAIRE - ATTENTION) ⚠️ | Erreur Postgres: {error_msg}"
        else:
            db_type = "SQLite (TEMPORAIRE) - Pas de DATABASE_URL ou psycopg2"
    except Exception as e:
        db_type = f"Erreur critique: {str(e)}"
        
    return jsonify({
        "status": "online-v2", 
        "database": db_type,
        "psycopg2": has_psycopg2,
        "postgres_error": error_msg
    })

@app.route('/api/products', methods=['GET'])
@app.route('/products', methods=['GET'])
def get_products():
    db = None
    try:
        db = DB(get_db_connection())
        try:
            db.execute('SELECT * FROM products')
            products = db.fetchall()
        except:
            init_db()
            db = DB(get_db_connection())
            db.execute('SELECT * FROM products')
            products = db.fetchall()
            
        if len(products) == 0:
            init_db()
            db.execute("INSERT INTO products (id, name, price, category, image, stock) VALUES (?, ?, ?, ?, ?, ?)", ('p1', 'iPhone 11', 220000, 'Téléphone', 'assets/electronics_1.png', 10))
            db.commit()
            db.execute('SELECT * FROM products')
            products = db.fetchall()
            
        db.close()
        return jsonify(products)
    except Exception as e:
        if db: db.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def save_product():
    try:
        data = request.json
        p_id = data.get('id')
        name = data.get('name')
        price = data.get('price')
        category = data.get('category')
        image = data.get('image', 'assets/electronics_1.png')
        stock = data.get('stock', 0)
        description = data.get('description', "Un produit d'exception.")
        media = json.dumps(data.get('media', []))
        
        db = DB(get_db_connection())
        if p_id:
            db.execute('UPDATE products SET name=?, price=?, category=?, image=?, stock=?, description=?, media=? WHERE id=?', (name, price, category, image, stock, description, media, p_id))
        else:
            p_id = 'p' + str(int(time.time() * 1000))
            db.execute('INSERT INTO products (id, name, price, category, image, stock, description, media) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (p_id, name, price, category, image, stock, description, media))
        db.commit()
        db.close()
        return jsonify({"success": True, "id": p_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM users')
        users = db.fetchall()
        db.close()
        for u in users: u.pop('password', None)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
def save_user():
    try:
        data = request.json
        u_id = data.get('id')
        db = DB(get_db_connection())
        if u_id:
            db.execute('UPDATE users SET name=?, email=?, role=?, status=?, address=?, phone=? WHERE id=?', (data.get('name'), data.get('email'), data.get('role'), data.get('status'), data.get('address'), data.get('phone'), u_id))
        else:
            u_id = 'u' + str(int(time.time() * 1000))
            db.execute('INSERT INTO users (id, name, email, password, role, status, address, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (u_id, data.get('name'), data.get('email'), data.get('password', 'default123'), data.get('role', 'client'), data.get('status', 'active'), data.get('address'), data.get('phone')))
        db.commit()
        db.close()
        return jsonify({"success": True, "id": u_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        db = DB(get_db_connection())
        db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (data.get('email'), data.get('password')))
        user = db.fetchone()
        db.close()
        if user:
            return jsonify({"userId": user['id'], "name": user['name'], "role": user['role'], "expires": int(time.time() * 1000) + 3600*1000*8})
        return jsonify({"error": "Identifiants incorrects"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        email = data.get('email', '').strip()
        new_password = data.get('new_password', '').strip()

        if not email or not new_password:
            return jsonify({"error": "Email et nouveau mot de passe requis."}), 400

        if len(new_password) < 6:
            return jsonify({"error": "Le mot de passe doit comporter au moins 6 caractères."}), 400

        db = DB(get_db_connection())
        db.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = db.fetchone()

        if not user:
            return jsonify({"error": "Aucun compte trouvé avec cet email."}), 404

        db.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
        db.commit()
        db.close()
        return jsonify({"success": True, "message": "Mot de passe mis à jour avec succès."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/check-email', methods=['POST'])
def check_email():
    try:
        data = request.json
        email = data.get('email', '').strip()
        if not email:
            return jsonify({"error": "Email requis."}), 400
        db = DB(get_db_connection())
        db.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = db.fetchone()
        db.close()
        if user:
            return jsonify({"exists": True})
        return jsonify({"exists": False, "error": "Aucun compte trouvé avec cet email."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders', methods=['POST'])
def save_order():
    try:
        data = request.json
        o_id = data.get('id') or ('TRX-' + str(int(time.time() * 1000)))
        db = DB(get_db_connection())
        
        # Serialization of items for DB
        items_json = json.dumps(data.get('items', []))
        
        # Récupération flexible des données client (Frontend vs Backend naming)
        c_fn = data.get('customer_firstname') or data.get('firstname') or 'Invité'
        c_ln = data.get('customer_lastname') or data.get('lastname') or ''
        c_addr = data.get('customer_address') or data.get('address') or 'Non précisée'
        c_phone = data.get('customer_phone') or data.get('phone') or 'Non précisé'
        
        db.execute('''
            INSERT INTO orders (id, userId, date, method, status, total, items, customer_firstname, customer_lastname, customer_address, customer_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            o_id, data.get('userId'), datetime.now().isoformat(),
            data.get('method', 'Livraison'), 'En attente',
            data.get('total', 0), items_json,
            c_fn, c_ln, c_addr, c_phone
        ))
        db.commit()
        db.close()
        
        # NOTIFICATION ADMIN : Nouvelle commande (Uniquement si paiement à la livraison)
        payment_method = data.get('method', 'Livraison')
        is_online_payment = payment_method.lower().strip() in ['wave', 'orange money', 'orangemoney', 'orange']
        
        if not is_online_payment:
            sys.stderr.write(f"🔔 NOTIFICATION ADMIN : Nouvelle commande {o_id} de {c_fn} {c_ln} (Paiement hors-ligne)\n")
            try:
                send_admin_notification(
                    order_id=o_id,
                    customer_name=f"{c_fn} {c_ln}".strip(),
                    total=data.get('total', 0),
                    items_list=data.get('items', []),
                    phone=c_phone,
                    address=c_addr,
                    payment_method=payment_method,
                    status="En attente"
                )
            except Exception as e_notif:
                sys.stderr.write(f"⚠️ Notification creation failed: {e_notif}\n")
        else:
            sys.stderr.write(f"⏳ NOTIFICATION ADMIN : Commande {o_id} en attente de paiement en ligne ({payment_method}).\n")
        
        return jsonify({"success": True, "id": o_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
@app.route('/api/user/orders', methods=['GET'])
def get_orders():
    try:
        db = DB(get_db_connection())
        # Filter by userId if provided
        u_id = request.args.get('userId')
        if u_id:
            db.execute('SELECT * FROM orders WHERE userId = ? ORDER BY date DESC', (u_id,))
        else:
            db.execute('SELECT * FROM orders ORDER BY date DESC')
        orders = db.fetchall()
        db.close()
        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<o_id>', methods=['GET'])
def get_single_order(o_id):
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM orders WHERE id = ?', (o_id,))
        order = db.fetchone()
        db.close()
        if order:
            if isinstance(order.get('items'), str):
                try: order['items'] = json.loads(order['items'])
                except: pass
            return jsonify(order)
        return jsonify({"error": "Commande introuvable"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<o_id>', methods=['PUT'])
def update_order(o_id):
    try:
        data = request.json
        status = data.get('status')
        db = DB(get_db_connection())
        db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, o_id))
        db.commit()
        db.close()
        
        # LOGIQUE DE NOTIFICATION DE STATUT (Flexible)
        status_clean = status.lower().strip()
        if 'expédi' in status_clean:
            sys.stderr.write(f"📲 NOTIFICATION CLIENT : Votre commande {o_id} a été expédiée ! 🚚\n")
        elif 'livré' in status_clean:
            sys.stderr.write(f"✨ NOTIFICATION CLIENT : Commande {o_id} livrée ! Merci de confirmer la réception. ✅\n")
        elif 'confirm' in status_clean or 'reçu' in status_clean:
            sys.stderr.write(f"🏆 NOTIFICATION ADMIN : Le client a confirmé la réception de la commande {o_id} ! 💰\n")
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM reviews ORDER BY date DESC')
        reviews = db.fetchall()
        db.close()
        return jsonify(reviews)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<r_id>', methods=['DELETE'])
def delete_review(r_id):
    try:
        db = DB(get_db_connection())
        # On nettoie d'abord la référence dans la table orders
        db.execute('UPDATE orders SET review_id = NULL WHERE review_id = ?', (r_id,))
        # On supprime l'avis
        db.execute('DELETE FROM reviews WHERE id = ?', (r_id,))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<r_id>/reply', methods=['PATCH'])
def reply_review(r_id):
    try:
        data = request.json
        reply = data.get('reply')
        db = DB(get_db_connection())
        db.execute('UPDATE reviews SET admin_reply = ? WHERE id = ?', (reply, r_id))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
        data = request.json
        r_id = 'REV' + str(int(time.time()))
        db = DB(get_db_connection())
        db.execute('''
            INSERT INTO reviews (id, orderId, userId, userName, rating_product, rating_service, comment, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r_id, 
            data.get('orderId', 'N/A'), 
            data.get('userId', 'guest'), 
            data.get('userName') or data.get('username') or 'Client Douéra', 
            data.get('rating_product', 5), 
            data.get('rating_service', 5), 
            data.get('comment', ''), 
            datetime.now().isoformat()
        ))
        db.execute('UPDATE orders SET review_id = ? WHERE id = ?', (r_id, data.get('orderId')))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- WAVE PAYMENT INTEGRATION ---

@app.route('/api/payments/wave/session', methods=['POST'])
def create_wave_session():
    try:
        data = request.json
        amount = data.get('amount')
        order_id = data.get('order_id')
        
        # URL de base pour les redirections (à adapter selon le domaine)
        base_url = request.host_url.rstrip('/')
        
        headers = {
            "Authorization": f"Bearer {WAVE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount,
            "currency": "XOF",
            "error_url": f"{base_url}/checkout.html?status=error&orderId={order_id}",
            "success_url": f"{base_url}/success.html?ref={order_id}",
            "client_reference": order_id
        }
        
        response = requests.post("https://api.wave.com/v1/checkout/sessions", headers=headers, json=payload)
        
        if response.status_code != 200:
            return jsonify({"error": f"Wave API Error: {response.text}"}), response.status_code
            
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/payments/wave/webhook', methods=['POST'])
def wave_webhook():
    try:
        data = request.json
        # Wave envoie un événement 'checkout.session.completed'
        if data.get('type') == 'checkout.session.completed':
            session = data.get('data')
            order_id = session.get('client_reference')
            payment_status = session.get('payment_status')
            
            if payment_status == 'succeeded':
                db = DB(get_db_connection())
                # On met à jour la commande en 'Payé'
                db.execute("UPDATE orders SET status = 'Payé' WHERE id = ?", (order_id,))
                db.commit()
                db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
                order = db.fetchone()
                db.close()
                sys.stderr.write(f"✅ WAVE WEBHOOK: Commande {order_id} marquée comme PAYÉE.\n")
                if order:
                    try:
                        send_admin_notification(
                            order_id=order_id,
                            customer_name=f"{order.get('customer_firstname', '')} {order.get('customer_lastname', '')}".strip(),
                            total=order.get('total', 0),
                            items_list=order.get('items', []),
                            phone=order.get('customer_phone', ''),
                            address=order.get('customer_address', ''),
                            payment_method=order.get('method', 'Wave'),
                            status="Payé"
                        )
                    except Exception as e_notif:
                        sys.stderr.write(f"⚠️ Wave Paid Notification Failed: {e_notif}\n")
                
        return "", 200
    except Exception as e:
        sys.stderr.write(f"❌ WAVE WEBHOOK ERROR: {str(e)}\n")
        return jsonify({"error": str(e)}), 500

# --- ORANGE MONEY PAYMENT INTEGRATION ---

@app.route('/api/payments/orange/session', methods=['POST'])
def create_orange_session():
    try:
        data = request.json
        amount = data.get('amount')
        order_id = data.get('order_id')
        
        # 1. Obtenir le token d'accès Orange
        import base64
        auth_header = base64.b64encode(f"{OM_CLIENT_ID}:{OM_CLIENT_SECRET}".encode()).decode()
        
        token_res = requests.post(OM_AUTH_URL, 
            headers={"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"}
        )
        
        if token_res.status_code != 200:
            return jsonify({"error": f"Orange Auth Error: {token_res.text}"}), token_res.status_code
            
        access_token = token_res.json().get('access_token')
        
        # 2. Créer la session de paiement
        base_url = request.host_url.rstrip('/')
        payload = {
            "merchant_key": OM_MERCHANT_KEY,
            "currency": "OUV", # OUV est requis pour le mode test (Sandbox)
            "order_id": order_id,
            "amount": amount,
            "return_url": f"{base_url}/success.html?ref={order_id}",
            "cancel_url": f"{base_url}/checkout.html?status=cancel&orderId={order_id}",
            "notif_url": f"{base_url}/api/payments/orange/webhook",
            "lang": "fr"
        }
        
        pay_res = requests.post(OM_PAY_URL,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload
        )
        
        if pay_res.status_code != 201:
            sys.stderr.write(f"❌ ORANGE PAY ERROR: Status {pay_res.status_code} - Response: {pay_res.text}\n")
            return jsonify({"error": f"Orange Pay Error: {pay_res.text}"}), pay_res.status_code
            
        return jsonify(pay_res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/payments/orange/webhook', methods=['POST'])
def orange_webhook():
    try:
        data = request.json
        # Orange envoie une notification avec l'status
        status = data.get('status')
        order_id = data.get('notif_token') # Souvent le token ou order_id selon config
        
        if status == 'SUCCESS':
            db = DB(get_db_connection())
            db.execute("UPDATE orders SET status = 'Payé' WHERE id = ?", (order_id,))
            db.commit()
            db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = db.fetchone()
            db.close()
            sys.stderr.write(f"✅ ORANGE WEBHOOK: Commande {order_id} marquée comme PAYÉE.\n")
            if order:
                try:
                    send_admin_notification(
                        order_id=order_id,
                        customer_name=f"{order.get('customer_firstname', '')} {order.get('customer_lastname', '')}".strip(),
                        total=order.get('total', 0),
                        items_list=order.get('items', []),
                        phone=order.get('customer_phone', ''),
                        address=order.get('customer_address', ''),
                        payment_method=order.get('method', 'Orange Money'),
                        status="Payé"
                    )
                except Exception as e_notif:
                    sys.stderr.write(f"⚠️ Orange Paid Notification Failed: {e_notif}\n")
            
        return "", 200
    except Exception as e:
        sys.stderr.write(f"❌ ORANGE WEBHOOK ERROR: {str(e)}\n")
        return jsonify({"error": str(e)}), 500
