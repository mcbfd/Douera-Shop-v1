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

# Redirection forcée pour éviter la pollution de la réponse HTTP par des prints
sys.stdout = sys.stderr

app = Flask(__name__)
CORS(app)

# --- DATABASE CONFIGURATION ---
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:B%40c%40lori%402015@db.wfdoqlomlpsowxzwfxfu.supabase.co:6543/postgres?sslmode=require"

# Sécurité : Si on est sur Vercel et que l'URL utilise encore le port 5432, on force le passage au port 6543
if DATABASE_URL and ":5432/" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace(":5432/", ":6543/")

def get_db_connection():
    try:
        if DATABASE_URL and has_psycopg2:
            return psycopg2.connect(DATABASE_URL, connect_timeout=10)
    except Exception as e:
        sys.stderr.write(f"Postgres failed: {e}\n")
    
    # SQLite Fallback
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
        
        # Migration review_id
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_id TEXT" if is_postgres else "ALTER TABLE orders ADD COLUMN review_id TEXT")
        except:
            conn.rollback()
            pass
            
        cur.execute(f"CREATE TABLE IF NOT EXISTS reviews (id {id_type}, orderId TEXT, productId TEXT, userId TEXT, userName TEXT, rating_product INTEGER, rating_service INTEGER, comment TEXT, admin_reply TEXT, date TEXT)")

        # Admin default
        cur.execute('SELECT count(*) FROM users')
        if cur.fetchone()[0] == 0:
            p = (%s, %s, %s, %s, %s, %s) if is_postgres else (?, ?, ?, ?, ?, ?)
            cur.execute(f"INSERT INTO users (id, email, password, name, role, status) VALUES {p}", ('u1', 'admin@douerashop.sn', 'admin123', 'Super Admin', 'super_admin', 'active'))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        sys.stderr.write(f"Init DB Error: {e}\n")

# --- API ROUTES ---

@app.route('/api/health')
def health():
    return jsonify({"status": "online", "psycopg2": has_psycopg2})

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
            # Insert mini default for display
            db.execute("INSERT INTO products (id, name, price, category, image, stock) VALUES (?, ?, ?, ?, ?, ?)", ('p1', 'iPhone 11', 220000, 'Téléphone', 'assets/electronics_1.png', 10))
            db.commit()
            db.execute('SELECT * FROM products')
            products = db.fetchall()
            
        db.close()
        return jsonify(products)
    except Exception as e:
        if db: db.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        db = DB(get_db_connection())
        db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = db.fetchone()
        db.close()
        if user:
            return jsonify({"userId": user['id'], "name": user['name'], "role": user['role']})
        return jsonify({"error": "Identifiants incorrects"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM orders')
        orders = db.fetchall()
        db.close()
        return jsonify(orders)
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
