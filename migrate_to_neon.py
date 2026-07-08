"""
Import des données SQLite vers Neon PostgreSQL
"""
import psycopg2
import sqlite3
import json
import os

NEON_URL = 'postgresql://neondb_owner:npg_WwdyYSs7Nl0q@ep-muddy-haze-as7g9uu9.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require'
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'api', 'douera.db')

def migrate():
    # Connexion SQLite source
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sc = sqlite_conn.cursor()
    
    # Connexion Neon destination
    pg_conn = psycopg2.connect(NEON_URL, connect_timeout=15)
    pg_conn.autocommit = False
    pc = pg_conn.cursor()
    
    print("🔧 Création des tables...")
    
    pc.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            name TEXT,
            role TEXT,
            status TEXT,
            address TEXT,
            phone TEXT
        )
    """)
    
    pc.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT,
            price INTEGER,
            category TEXT,
            image TEXT,
            stock INTEGER,
            description TEXT,
            specs TEXT,
            media TEXT
        )
    """)
    
    pc.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            "userId" TEXT,
            date TEXT,
            method TEXT,
            status TEXT,
            total INTEGER,
            items TEXT,
            customer_firstname TEXT,
            customer_lastname TEXT,
            customer_address TEXT,
            customer_phone TEXT,
            review_id TEXT
        )
    """)
    
    pc.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            "orderId" TEXT,
            "productId" TEXT,
            "userId" TEXT,
            "userName" TEXT,
            rating_product INTEGER,
            rating_service INTEGER,
            comment TEXT,
            admin_reply TEXT,
            date TEXT
        )
    """)
    
    pg_conn.commit()
    print("✅ Tables créées")
    
    # Migration users
    sc.execute('SELECT * FROM users')
    users = [dict(r) for r in sc.fetchall()]
    for u in users:
        pc.execute("""
            INSERT INTO users (id, email, password, name, role, status, address, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                email=EXCLUDED.email, name=EXCLUDED.name,
                role=EXCLUDED.role, status=EXCLUDED.status,
                address=EXCLUDED.address, phone=EXCLUDED.phone
        """, (u['id'], u['email'], u['password'], u['name'], u['role'], u['status'], u.get('address'), u.get('phone')))
    pg_conn.commit()
    print(f"✅ {len(users)} utilisateurs migrés")
    
    # Migration products
    sc.execute('SELECT * FROM products')
    products = [dict(r) for r in sc.fetchall()]
    for p in products:
        pc.execute("""
            INSERT INTO products (id, name, price, category, image, stock, description, specs, media)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name=EXCLUDED.name, price=EXCLUDED.price,
                category=EXCLUDED.category, image=EXCLUDED.image,
                stock=EXCLUDED.stock, description=EXCLUDED.description,
                specs=EXCLUDED.specs, media=EXCLUDED.media
        """, (p['id'], p['name'], p['price'], p['category'], p['image'], p['stock'], p.get('description'), p.get('specs'), p.get('media')))
    pg_conn.commit()
    print(f"✅ {len(products)} produits migrés")
    
    # Migration orders
    sc.execute('SELECT * FROM orders')
    orders = [dict(r) for r in sc.fetchall()]
    for o in orders:
        pc.execute("""
            INSERT INTO orders (id, "userId", date, method, status, total, items,
                customer_firstname, customer_lastname, customer_address, customer_phone, review_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (o['id'], o.get('userId'), o['date'], o['method'], o['status'],
              o['total'], o['items'], o.get('customer_firstname'), o.get('customer_lastname'),
              o.get('customer_address'), o.get('customer_phone'), o.get('review_id')))
    pg_conn.commit()
    print(f"✅ {len(orders)} commandes migrées")
    
    # Migration reviews
    sc.execute('SELECT * FROM reviews')
    reviews = [dict(r) for r in sc.fetchall()]
    for r in reviews:
        pc.execute("""
            INSERT INTO reviews (id, "orderId", "productId", "userId", "userName",
                rating_product, rating_service, comment, admin_reply, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (r['id'], r.get('orderId'), r.get('productId'), r['userId'],
              r.get('userName'), r['rating_product'], r['rating_service'],
              r.get('comment'), r.get('admin_reply'), r['date']))
    pg_conn.commit()
    print(f"✅ {len(reviews)} avis migrés")
    
    sqlite_conn.close()
    pc.close()
    pg_conn.close()
    print("\n🎉 Migration complète ! Votre base Neon est prête.")

if __name__ == '__main__':
    migrate()
