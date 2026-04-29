import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import get_db_connection, init_db

# Serve parent folder as static (the whole scratch dir)
app = Flask(__name__, static_folder='../', static_url_path='')
CORS(app)

# --- Ensure DB Initialized ---
init_db()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# --- 1. Products API ---
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

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
    
    conn = get_db_connection()
    
    if p_id:
        # Update
        conn.execute('''
            UPDATE products 
            SET name = ?, price = ?, category = ?, image = ?, stock = ?, description = ?
            WHERE id = ?
        ''', (name, price, category, image, stock, description, p_id))
    else:
        # Insert
        p_id = 'p' + str(int(time.time() * 1000))
        conn.execute('''
            INSERT INTO products (id, name, price, category, image, stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (p_id, name, price, category, image, stock, description))
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": p_id})

@app.route('/api/products/<p_id>', methods=['DELETE'])
def delete_product(p_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (p_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- 2. Users & Auth API ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({"error": "Identifiants incorrects"}), 401
    
    u_dict = dict(user)
    if u_dict['status'] == 'blocked':
        return jsonify({"error": "Compte bloqué. Contactez le Super Admin."}), 403
    
    # Fake JWT token for simplicity
    token = f"{u_dict['id']}-{int(time.time()*1000)}"
    session_data = {
        "userId": u_dict['id'],
        "name": u_dict['name'],
        "role": u_dict['role'],
        "address": u_dict['address'],
        "phone": u_dict['phone'],
        "token": token,
        "expires": int(time.time() * 1000) + (3600 * 1000 * 8)
    }
    return jsonify(session_data)

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    # Mask passwords
    res = []
    for u in users:
        d = dict(u)
        d.pop('password', None)
        res.append(d)
    return jsonify(res)

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
    
    conn = get_db_connection()
    if u_id:
        conn.execute('''
            UPDATE users SET email=?, password=?, name=?, role=?, status=?, address=?, phone=? WHERE id=?
        ''', (email, password, name, role, status, address, phone, u_id))
    else:
        u_id = 'u' + str(int(time.time() * 1000))
        conn.execute('''
            INSERT INTO users (id, email, password, name, role, status, address, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (u_id, email, password, name, role, status, address, phone))
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": u_id})

@app.route('/api/users/<u_id>', methods=['DELETE'])
def delete_user(u_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (u_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/users/<u_id>/profile', methods=['PATCH'])
def update_user_profile(u_id):
    data = request.json
    address = data.get('address')
    phone = data.get('phone')
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET address = ?, phone = ? WHERE id = ?', (address, phone, u_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- 3. Orders API ---
@app.route('/api/orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    # Join with reviews to get review info if it exists
    query = '''
        SELECT o.*, r.rating_product, r.rating_service, r.comment as review_comment, r.admin_reply, r.id as review_id
        FROM orders o
        LEFT JOIN reviews r ON o.id = r.orderId
        ORDER BY o.date DESC
    '''
    orders = conn.execute(query).fetchall()
    conn.close()
    res = []
    for o in orders:
        d = dict(o)
        d['items'] = json.loads(d['items'])
        res.append(d)
    return jsonify(res)

@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        items_json = json.dumps(data.get('items', []))
        total = data.get('total', 0)
        method = data.get('method', 'Espèces')
        user_id = data.get('userId', 'guest')
        
        # Use provided ID if available (Wave/OM/TRX ref)
        o_id = data.get('id')
        if not o_id:
            o_id = 'ORD-' + str(int(time.time()))
            
        date_str = data.get('date') or datetime.now().isoformat()
        status = 'En attente'
        
        customer_firstname = data.get('customer_firstname')
        customer_lastname = data.get('customer_lastname')
        customer_address = data.get('customer_address')
        customer_phone = data.get('customer_phone')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO orders (id, userId, date, method, status, total, items, customer_firstname, customer_lastname, customer_address, customer_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (o_id, user_id, date_str, method, status, total, items_json, customer_firstname, customer_lastname, customer_address, customer_phone))
        
        for item in data.get('items', []):
            conn.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (item.get('quantity', 1), item.get('id')))
            
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": o_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<o_id>', methods=['PUT'])
def update_order_status(o_id):
    new_status = request.json.get('status')
    conn = get_db_connection()
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, o_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/orders/<o_id>', methods=['DELETE'])
def delete_order(o_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM orders WHERE id = ?', (o_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- REVIEWS ---
@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.json
    review_id = 'rev-' + str(int(time.time()))
    conn = get_db_connection()
    conn.execute('''
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
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": review_id})

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    conn = get_db_connection()
    reviews = conn.execute('SELECT * FROM reviews ORDER BY date DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in reviews])

@app.route('/api/reviews/<review_id>/reply', methods=['PATCH'])
def reply_to_review(review_id):
    data = request.json
    conn = get_db_connection()
    conn.execute('UPDATE reviews SET admin_reply = ? WHERE id = ?', (data['reply'], review_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
