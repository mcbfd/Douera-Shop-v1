import os
import json
import time
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import sqlite3

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

# --- DATABASE CONFIGURATION ---
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:B%40c%40lori%402015@db.wfdoqlomlpsowxzwfxfu.supabase.co:6543/postgres?sslmode=require"
if DATABASE_URL and ":5432/" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace(":5432/", ":6543/")

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
        cur.execute(f"CREATE TABLE IF NOT EXISTS products (id {id_type}, name TEXT, price INTEGER, category TEXT, image TEXT, stock INTEGER, description TEXT, specs TEXT)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS orders (id {id_type}, userId TEXT, date TEXT, method TEXT, status TEXT, total INTEGER, items TEXT, customer_firstname TEXT, customer_lastname TEXT, customer_address TEXT, customer_phone TEXT)")
        
        try:
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
        
        db = DB(get_db_connection())
        if p_id:
            db.execute('UPDATE products SET name=?, price=?, category=?, image=?, stock=?, description=? WHERE id=?', (name, price, category, image, stock, description, p_id))
        else:
            p_id = 'p' + str(int(time.time() * 1000))
            db.execute('INSERT INTO products (id, name, price, category, image, stock, description) VALUES (?, ?, ?, ?, ?, ?, ?)', (p_id, name, price, category, image, stock, description))
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

@app.route('/api/orders', methods=['POST'])
def save_order():
    try:
        data = request.json
        o_id = data.get('id') or ('TRX-' + str(int(time.time() * 1000)))
        db = DB(get_db_connection())
        
        # Serialization of items for DB
        items_json = json.dumps(data.get('items', []))
        
        db.execute('''
            INSERT INTO orders (id, userId, date, method, status, total, items, customer_firstname, customer_lastname, customer_address, customer_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            o_id, data.get('userId'), datetime.now().isoformat(),
            data.get('method', 'Livraison'), 'En attente',
            data.get('total', 0), items_json,
            data.get('firstname'), data.get('lastname'),
            data.get('address'), data.get('phone')
        ))
        db.commit()
        db.close()
        
        # NOTIFICATION ADMIN : Nouvelle commande
        sys.stderr.write(f"🔔 NOTIFICATION ADMIN : Nouvelle commande {o_id} de {data.get('firstname')} {data.get('lastname')}\n")
        
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

@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
        data = request.json
        r_id = 'REV' + str(int(time.time()))
        db = DB(get_db_connection())
        db.execute('INSERT INTO reviews (id, orderId, userId, rating_product, rating_service, comment, date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (r_id, data.get('orderId'), data.get('userId'), data.get('rating_product'), data.get('rating_service'), data.get('comment'), datetime.now().isoformat()))
        db.execute('UPDATE orders SET review_id = ? WHERE id = ?', (r_id, data.get('orderId')))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
