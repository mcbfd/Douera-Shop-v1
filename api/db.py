import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'douera.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
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

    # Reviews Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            orderId TEXT NOT NULL,
            productId TEXT,
            userId TEXT NOT NULL,
            userName TEXT,
            rating_product INTEGER NOT NULL,
            rating_service INTEGER NOT NULL,
            comment TEXT,
            admin_reply TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (orderId) REFERENCES orders(id),
            FOREIGN KEY (userId) REFERENCES users(id)
        )
    ''')

    # Insert default Super Admin if not exists
    c.execute('SELECT count(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO users (id, email, password, name, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('u1', 'admin@douerashop.sn', 'admin123', 'Super Admin', 'super_admin', 'active'))
        
        c.execute('''
            INSERT INTO users (id, email, password, name, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('u2', 'demo@douerashop.sn', 'password123', 'Admin Démo', 'admin', 'active'))

    # Insert default Products if not exists
    c.execute('SELECT count(*) FROM products')
    if c.fetchone()[0] == 0:
        default_products = [
            ('p1', 'iPhone 11 Pro 64Go', 280000, 'Téléphone', 'assets/electronics_1.png', 5, 'Un produit d\'exception.'),
            ('p2', 'iPhone XR 128Go', 175000, 'Téléphone', 'assets/electronics_1.png', 8, 'Un produit d\'exception.'),
            ('p3', 'iPhone XR 64Go', 150000, 'Téléphone', 'assets/electronics_1.png', 12, 'Un produit d\'exception.'),
            ('p4', 'iPhone 11 Simple', 220000, 'Téléphone', 'assets/electronics_2.png', 6, 'Un produit d\'exception.'),
            ('p5', 'Bracelets Luxe', 5000, 'Mode', 'assets/fashion_1.png', 25, 'Un produit d\'exception.'),
            ('p6', 'Colliers Élégance', 12000, 'Luxe', 'assets/fashion_1.png', 15, 'Un produit d\'exception.'),
            ('p7', 'Gants pour sport Pro', 7500, 'Sport', 'assets/electronics_2.png', 20, 'Un produit d\'exception.'),
            ('p8', 'Chaussure de Sport Nike', 35000, 'Sport', 'assets/fashion_1.png', 10, 'Un produit d\'exception.')
        ]
        c.executemany('''
            INSERT INTO products (id, name, price, category, image, stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_products)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
