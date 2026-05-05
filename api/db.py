import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
import sys

# Supabase Connection String
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:B%40c%40lori%402015@db.wfdoqlomlpsowxzwfxfu.supabase.co:6543/postgres?sslmode=require&pgbouncer=true"

# Sécurité : Si on est sur Vercel et que l'URL utilise encore le port 5432, on force le passage au port 6543
if (os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')) and ":5432/" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace(":5432/", ":6543/")

# Nettoyage pour psycopg2 : On enlève "pgbouncer=true" qui cause une erreur DSN
if "pgbouncer=true" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("pgbouncer=true", "")
    DATABASE_URL = DATABASE_URL.replace("&&", "&").replace("?&", "?").rstrip("?").rstrip("&")

def get_db_connection():
    # Détection de psycopg2
    try:
        import psycopg2
        has_psycopg2 = True
    except ImportError:
        has_psycopg2 = False

    is_vercel = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')

    if DATABASE_URL and has_psycopg2:
        try:
            # Connexion directe simplifiée
            return psycopg2.connect(DATABASE_URL, connect_timeout=5)
        except Exception as e:
            sys.stderr.write(f"DB Error: {e}\n")
            return get_sqlite_connection()
    else:
        return get_sqlite_connection()

def get_sqlite_connection():
    db_path = '/tmp/douera.db' if (os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')) else os.path.join(os.path.dirname(__file__), 'douera.db')
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Determine if we are on Postgres or SQLite
    is_postgres = hasattr(conn, 'tpc_begin') # Simple check for psycopg2 connection
    
    id_type = "TEXT PRIMARY KEY"
    
    # Users Table
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id {id_type},
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            address TEXT,
            phone TEXT
        )
    ''')

    # Products Table
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS products (
            id {id_type},
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            category TEXT NOT NULL,
            image TEXT NOT NULL,
            stock INTEGER NOT NULL,
            description TEXT,
            specs TEXT
        )
    ''')

    # Orders Table
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS orders (
            id {id_type},
            userId TEXT,
            date TEXT NOT NULL,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            total INTEGER NOT NULL,
            items TEXT NOT NULL,
            customer_firstname TEXT,
            customer_lastname TEXT,
            customer_address TEXT,
            customer_phone TEXT
        )
    ''')
    
    # Add review_id column if not exists (Migration)
    try:
        # Check if column exists first to avoid unnecessary errors
        if is_postgres:
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_id TEXT")
        else:
            cur.execute("ALTER TABLE orders ADD COLUMN review_id TEXT")
        conn.commit()
    except Exception as e:
        conn.rollback()
        sys.stderr.write(f"Migration Info: {e}\n")

    # Reviews Table
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS reviews (
            id {id_type},
            orderId TEXT NOT NULL,
            productId TEXT,
            userId TEXT NOT NULL,
            userName TEXT,
            rating_product INTEGER NOT NULL,
            rating_service INTEGER NOT NULL,
            comment TEXT,
            admin_reply TEXT,
            date TEXT NOT NULL
        )
    ''')

    # Insert default Super Admin if not exists
    cur.execute('SELECT count(*) FROM users')
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute('''
            INSERT INTO users (id, email, password, name, role, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''' if is_postgres else '''
            INSERT INTO users (id, email, password, name, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('u1', 'admin@douerashop.sn', 'admin123', 'Super Admin', 'super_admin', 'active'))
        
        cur.execute('''
            INSERT INTO users (id, email, password, name, role, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''' if is_postgres else '''
            INSERT INTO users (id, email, password, name, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('u2', 'demo@douerashop.sn', 'password123', 'Admin Démo', 'admin', 'active'))

    # Insert default Products if not exists
    cur.execute('SELECT count(*) FROM products')
    count = cur.fetchone()[0]
    if count == 0:
        default_products = [
            ('p1', 'iPhone 11 Pro 64Go', 280000, 'Téléphone', 'assets/electronics_1.png', 5, 'Un produit d\'exception.'),
            ('p2', 'iPhone XR 128Go', 175000, 'Téléphone', 'assets/Iphone XR.jpg', 8, 'Un produit d\'exception.'),
            ('p3', 'iPhone XR 64Go', 150000, 'Téléphone', 'assets/Iphone XR.jpeg', 12, 'Un produit d\'exception.'),
            ('p4', 'iPhone 11 Simple', 220000, 'Téléphone', 'assets/iPhone11_Visuel1-DM.webp', 6, 'Un produit d\'exception.'),
            ('p5', 'Bracelets Luxe', 5000, 'Mode', 'assets/Bracelet.webp', 25, 'Un produit d\'exception.'),
            ('p6', 'Colliers Élégance', 12000, 'Luxe', 'assets/Colier.webp', 15, 'Un produit d\'exception.'),
            ('p7', 'Gants pour sport Pro', 7500, 'Sport', 'assets/Gantdesporthomme_1.webp', 20, 'Un produit d\'exception.'),
            ('p8', 'Chaussure de Sport Nike', 35000, 'Sport', 'assets/Chaussure nike.jpg', 10, 'Un produit d\'exception.')
        ]
        placeholder = "(%s, %s, %s, %s, %s, %s, %s)" if is_postgres else "(?, ?, ?, ?, ?, ?, ?)"
        for p in default_products:
            cur.execute(f'''
                INSERT INTO products (id, name, price, category, image, stock, description)
                VALUES {placeholder}
            ''', p)

    conn.commit()
    cur.close()
    conn.close()
class DB:
    def __init__(self, conn):
        self.conn = conn
        self.is_postgres = hasattr(conn, 'tpc_begin')
        self.cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()

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
