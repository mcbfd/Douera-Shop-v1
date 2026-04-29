import sqlite3
import json
from datetime import datetime

DB_PATH = 'backend/douera.db'

def setup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get user 'mcb'
    user = c.execute("SELECT id FROM users WHERE email='mcb@douerashop.sn'").fetchone()
    if not user:
        print("User mcb@douerashop.sn not found. Please register first.")
        return
    
    user_id = user[0]
    order_id = 'TEST-ORDER-123'
    
    # Delete if exists
    c.execute("DELETE FROM orders WHERE id=?", (order_id,))
    
    # Create Delivered Order
    items = [
        {"id": "p1", "name": "iPhone 11 Pro 64Go", "price": 280000, "quantity": 1, "image": "assets/electronics_1.png"}
    ]
    
    c.execute('''
        INSERT INTO orders (id, userId, date, method, status, total, items, customer_firstname, customer_lastname, customer_address, customer_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_id,
        user_id,
        datetime.now().isoformat(),
        'wave',
        'Livrée',
        280000,
        json.dumps(items),
        'Moussa',
        'Test',
        'Quartier Escale, Douéra',
        '781234567'
    ))
    
    conn.commit()
    conn.close()
    print(f"Test order {order_id} created for user {user_id} with status 'Livrée'.")

if __name__ == '__main__':
    setup()
