import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from .db import get_db_connection, init_db, DB
import sys

# Redirection forcée pour éviter la pollution de la réponse HTTP par des prints
sys.stdout = sys.stderr

app = Flask(__name__)
CORS(app)

# --- Ensure DB Initialized ---
try:
    init_db()
except Exception as e:
    sys.stderr.write(f"Init DB Error: {e}\n")
    traceback.print_exc()

@app.route('/api/health')
def health():
    try:
        db = DB(get_db_connection())
        # Utilisation de la méthode fetchone de la classe DB pour la conversion automatique
        db.execute('SELECT count(*) FROM users')
        u_row = db.fetchone()
        u_count = list(u_row.values())[0] if u_row else 0
        
        db.execute('SELECT count(*) FROM products')
        p_row = db.fetchone()
        p_count = list(p_row.values())[0] if p_row else 0
        
        db.close()
        return jsonify({
            "status": "ok", 
            "db": "postgres", 
            "users": u_count, 
            "products": p_count
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "trace": traceback.format_exc()})

# --- 1. Products API ---
@app.route('/api/products', methods=['GET'])
@app.route('/products', methods=['GET'])
def get_products():
    try:
        db = DB(get_db_connection())
        products = db.execute('SELECT * FROM products').fetchall()
        
        # Auto-init if empty
        if len(products) == 0:
            db.close()
            init_db()
            db = DB(get_db_connection())
            products = db.execute('SELECT * FROM products').fetchall()
            
        db.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def save_product():
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
        db.execute('''
            UPDATE products 
            SET name = ?, price = ?, category = ?, image = ?, stock = ?, description = ?
            WHERE id = ?
        ''', (name, price, category, image, stock, description, p_id))
    else:
        p_id = 'p' + str(int(time.time() * 1000))
        db.execute('''
            INSERT INTO products (id, name, price, category, image, stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (p_id, name, price, category, image, stock, description))
        
    db.commit()
    db.close()
    return jsonify({"success": True, "id": p_id})

@app.route('/api/products/<p_id>', methods=['DELETE'])
def delete_product(p_id):
    db = DB(get_db_connection())
    db.execute('DELETE FROM products WHERE id = ?', (p_id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

# --- 2. Users & Auth API ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    db = DB(get_db_connection())
    db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = db.fetchone()
    db.close()
    
    if not user:
        return jsonify({"error": "Identifiants incorrects"}), 401
    
    if user['status'] == 'blocked':
        return jsonify({"error": "Compte bloqué. Contactez le Super Admin."}), 403
    
    token = f"{user['id']}-{int(time.time()*1000)}"
    session_data = {
        "userId": user['id'],
        "name": user['name'],
        "role": user['role'],
        "address": user.get('address'),
        "phone": user.get('phone'),
        "token": token,
        "expires": int(time.time() * 1000) + (3600 * 1000 * 8)
    }
    return jsonify(session_data)

@app.route('/api/users', methods=['GET'])
def get_users():
    db = DB(get_db_connection())
    db.execute('SELECT * FROM users')
    users = db.fetchall()
    db.close()
    for u in users:
        u.pop('password', None)
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def save_user():
    data = request.json
    u_id = data.get('id')
    email = data.get('email')
    password = data.get('password', 'default123')
    name = data.get('name')
    role = data.get('role', 'client')
    status = data.get('status', 'active')
    address = data.get('address')
    phone = data.get('phone')
    
    db = DB(get_db_connection())
    if u_id:
        db.execute('''
            UPDATE users SET email=?, password=?, name=?, role=?, status=?, address=?, phone=? WHERE id=?
        ''', (email, password, name, role, status, address, phone, u_id))
    else:
        u_id = 'u' + str(int(time.time() * 1000))
        db.execute('''
            INSERT INTO users (id, email, password, name, role, status, address, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (u_id, email, password, name, role, status, address, phone))
        
    db.commit()
    db.close()
    return jsonify({"success": True, "id": u_id})

@app.route('/api/users/<u_id>', methods=['DELETE'])
def delete_user(u_id):
    db = DB(get_db_connection())
    db.execute('DELETE FROM users WHERE id = ?', (u_id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route('/api/users/<u_id>/profile', methods=['PATCH'])
def update_user_profile(u_id):
    data = request.json
    address = data.get('address')
    phone = data.get('phone')
    
    db = DB(get_db_connection())
    db.execute('UPDATE users SET address = ?, phone = ? WHERE id = ?', (address, phone, u_id))
    db.commit()
    db.close()
    return jsonify({"success": True})

# --- 3. Orders API ---
@app.route('/api/orders', methods=['GET'])
def get_orders():
    db = DB(get_db_connection())
    query = '''
        SELECT o.*, r.rating_product, r.rating_service, r.comment as review_comment, r.admin_reply, r.id as review_id
        FROM orders o
        LEFT JOIN reviews r ON o.id = r.orderId
        ORDER BY o.date DESC
    '''
    db.execute(query)
    orders = db.fetchall()
    db.close()
    for o in orders:
        if isinstance(o['items'], str):
            o['items'] = json.loads(o['items'])
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    items_json = json.dumps(data.get('items', []))
    total = data.get('total', 0)
    method = data.get('method', 'Espèces')
    user_id = data.get('userId', 'guest')
    o_id = 'ORD-' + str(int(time.time()))
    date_str = data.get('date') or str(int(time.time() * 1000))
    status = 'En attente'
    
    customer_firstname = data.get('customer_firstname')
    customer_lastname = data.get('customer_lastname')
    customer_address = data.get('customer_address')
    customer_phone = data.get('customer_phone')
    
    db = DB(get_db_connection())
    db.execute('''
        INSERT INTO orders (id, userId, date, method, status, total, items, customer_firstname, customer_lastname, customer_address, customer_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (o_id, user_id, date_str, method, status, total, items_json, customer_firstname, customer_lastname, customer_address, customer_phone))
    
    for item in data.get('items', []):
        db.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (item.get('quantity', 1), item.get('id')))
        
    db.commit()
    db.close()
    return jsonify({"success": True, "id": o_id})

@app.route('/api/orders/<o_id>', methods=['PUT'])
def update_order_status(o_id):
    new_status = request.json.get('status')
    db = DB(get_db_connection())
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, o_id))
    db.commit()
    db.close()
    return jsonify({"success": True})

# --- REVIEWS ---
@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.json
    review_id = 'rev-' + str(int(time.time()))
    db = DB(get_db_connection())
    db.execute('''
        INSERT INTO reviews (id, orderId, productId, userId, userName, rating_product, rating_service, comment, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        review_id, 
        data['orderId'], 
        data.get('productId'), 
        data['userId'], 
        data['userName'], 
        data['rating_product'], 
        data['rating_service'], 
        data['comment'], 
        datetime.now().isoformat()
    ))
    db.commit()
    db.close()
    return jsonify({"success": True, "id": review_id})

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    db = DB(get_db_connection())
    db.execute('SELECT * FROM reviews ORDER BY date DESC')
    reviews = db.fetchall()
    db.close()
    return jsonify(reviews)

@app.route('/api/reviews/<review_id>/reply', methods=['PATCH'])
def reply_to_review(review_id):
    data = request.json
    db = DB(get_db_connection())
    db.execute('UPDATE reviews SET admin_reply = ? WHERE id = ?', (data['reply'], review_id))
    db.commit()
    db.close()
    return jsonify({"success": True})

# Need to expose DATABASE_URL for health check
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:B%40c%40lori%402015@db.wfdoqlomlpsowxzwfxfu.supabase.co:5432/postgres"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
