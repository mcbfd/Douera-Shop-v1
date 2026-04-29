import sqlite3
import os

DB_PATH = 'backend/douera.db'

def update():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Add specs to products if not exists
    try:
        c.execute('ALTER TABLE products ADD COLUMN specs TEXT')
        print("Column 'specs' added to 'products'")
    except sqlite3.OperationalError:
        print("Column 'specs' already exists")

    # Add admin_reply to reviews if not exists
    try:
        c.execute('ALTER TABLE reviews ADD COLUMN admin_reply TEXT')
        print("Column 'admin_reply' added to 'reviews'")
    except sqlite3.OperationalError:
        print("Column 'admin_reply' already exists")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update()
