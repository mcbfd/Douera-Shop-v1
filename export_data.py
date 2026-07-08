"""
Script pour exporter les données SQLite vers un fichier SQL
à importer dans une nouvelle base PostgreSQL (Neon, Supabase, etc.)
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'api', 'douera.db')

def export_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    tables = ['users', 'products', 'orders', 'reviews']
    
    sql_lines = []
    sql_lines.append("-- Export données Douéra Shop")
    sql_lines.append("-- À importer dans votre nouvelle base PostgreSQL\n")
    
    # Créer les tables
    sql_lines.append("""
-- TABLES
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT, role TEXT, status TEXT, address TEXT, phone TEXT);
CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, price INTEGER, category TEXT, image TEXT, stock INTEGER, description TEXT, specs TEXT, media TEXT);
CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, userId TEXT, date TEXT, method TEXT, status TEXT, total INTEGER, items TEXT, customer_firstname TEXT, customer_lastname TEXT, customer_address TEXT, customer_phone TEXT, review_id TEXT);
CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, orderId TEXT, productId TEXT, userId TEXT, userName TEXT, rating_product INTEGER, rating_service INTEGER, comment TEXT, admin_reply TEXT, date TEXT);
""")
    
    for table in tables:
        try:
            c.execute(f'SELECT * FROM {table}')
            rows = c.fetchall()
            if rows:
                sql_lines.append(f"\n-- {table.upper()} ({len(rows)} entrées)")
                for row in rows:
                    d = dict(row)
                    cols = ', '.join(d.keys())
                    vals = ', '.join([
                        'NULL' if v is None else f"'{str(v).replace(chr(39), chr(39)+chr(39))}'"
                        for v in d.values()
                    ])
                    sql_lines.append(f"INSERT INTO {table} ({cols}) VALUES ({vals}) ON CONFLICT (id) DO NOTHING;")
            else:
                sql_lines.append(f"\n-- {table.upper()}: aucune donnée")
        except Exception as e:
            sql_lines.append(f"\n-- Erreur table {table}: {e}")
    
    conn.close()
    
    sql_content = '\n'.join(sql_lines)
    output_path = 'export_data.sql'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"✅ Export terminé : {output_path}")
    print("Ce fichier contient toutes vos données à importer dans la nouvelle base.")
    return sql_content

if __name__ == '__main__':
    export_data()
