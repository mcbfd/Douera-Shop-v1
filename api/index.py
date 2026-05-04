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
        # Check for psycopg2
        try:
            import psycopg2
            psycopg2_installed = True
        except ImportError:
            psycopg2_installed = False

        conn = get_db_connection()
        is_postgres = hasattr(conn, 'tpc_begin')
        db = DB(conn)
        db.execute('SELECT count(*) FROM users')
        u_count = list(db.fetchone().values())[0]
        db.close()
        return jsonify({
            "status": "ok", 
            "db_type": "postgres" if is_postgres else "sqlite", 
            "psycopg2": psycopg2_installed,
            "vercel": bool(os.environ.get('VERCEL')),
            "users": u_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "trace": traceback.format_exc()}), 500

# --- 1. Products API ---
@app.route('/api/products', methods=['GET'])
@app.route('/products', methods=['GET'])
def get_products():
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM products')
        rows = db.fetchall()
        
        # MANUALLY CONVERT TO DICT (ROBUST METHOD)
        products = [dict(row) for row in rows]
        
        if len(products) == 0:
            db.close()
            init_db()
            db = DB(get_db_connection())
            db.execute('SELECT * FROM products')
            products = [dict(row) for row in db.fetchall()]
            
        db.close()
        return jsonify(products)
    except Exception as e:
        sys.stderr.write(f"API Products Error: {e}\n")
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<p_id>', methods=['DELETE'])
def delete_product(p_id):
    try:
        db = DB(get_db_connection())
        db.execute('DELETE FROM products WHERE id = ?', (p_id,))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 2. Users & Auth API ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        db = DB(get_db_connection())
        db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        row = db.fetchone()
        db.close()
        
        if not row:
            return jsonify({"error": "Identifiants incorrects"}), 401
        
        user = dict(row)
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM users')
        users = [dict(row) for row in db.fetchall()]
        db.close()
        for u in users:
            u.pop('password', None)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
def save_user():
    try:
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
        
        # Vérifier si l'email existe déjà pour un nouvel utilisateur
        if not u_id:
            db.execute('SELECT id FROM users WHERE email = ?', (email,))
            if db.fetchone():
                db.close()
                return jsonify({"error": "Cet email est déjà utilisé par un autre compte."}), 400

        if u_id:
            # Update user logic
            if password and password != '********': # '********' is a placeholder we might use
                db.execute('''
                    UPDATE users SET email=?, password=?, name=?, role=?, status=?, address=?, phone=? WHERE id=?
                ''', (email, password, name, role, status, address, phone, u_id))
            else:
                db.execute('''
                    UPDATE users SET email=?, name=?, role=?, status=?, address=?, phone=? WHERE id=?
                ''', (email, name, role, status, address, phone, u_id))
        else:
            # Create user logic
            u_id = 'u' + str(int(time.time() * 1000))
            # Use provided password or default
            final_pass = password if password else 'douera123'
            db.execute('''
                INSERT INTO users (id, email, password, name, role, status, address, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (u_id, email, final_pass, name, role, status, address, phone))
            
        db.commit()
        db.close()
        return jsonify({"success": True, "id": u_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<u_id>', methods=['DELETE'])
def delete_user(u_id):
    try:
        db = DB(get_db_connection())
        db.execute('DELETE FROM users WHERE id = ?', (u_id,))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 3. Orders API ---
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        db = DB(get_db_connection())
        query = '''
            SELECT o.*, r.rating_product, r.rating_service, r.comment as review_comment, r.admin_reply, r.id as review_id
            FROM orders o
            LEFT JOIN reviews r ON o.id = r.orderId
            ORDER BY o.date DESC
        '''
        db.execute(query)
        orders = [dict(row) for row in db.fetchall()]
        db.close()
        for o in orders:
            if isinstance(o.get('items'), str):
                try:
                    o['items'] = json.loads(o['items'])
                except:
                    o['items'] = []
        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/orders/<o_id>', methods=['PUT'])
def update_order_status(o_id):
    try:
        data = request.json
        new_status = data.get('status')
        db = DB(get_db_connection())
        
        # Get current status to see if we need to adjust stock
        db.execute('SELECT status, items FROM orders WHERE id = ?', (o_id,))
        order = db.fetchone()
        
        if order:
            old_status = order['status']
            # If cancelling an active order, return items to stock
            if new_status == 'Annulée' and old_status != 'Annulée':
                items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                for item in items:
                    db.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (item.get('quantity', 1), item.get('id')))
            
            # If restoring a cancelled order, reduce stock
            elif old_status == 'Annulée' and new_status != 'Annulée':
                items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                for item in items:
                    db.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (item.get('quantity', 1), item.get('id')))

        db.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, o_id))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<o_id>', methods=['DELETE'])
def delete_order(o_id):
    try:
        db = DB(get_db_connection())
        db.execute('DELETE FROM orders WHERE id = ?', (o_id,))
        db.commit()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 4. Reviews API ---
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        db = DB(get_db_connection())
        db.execute('SELECT * FROM reviews ORDER BY date DESC')
        reviews = [dict(row) for row in db.fetchall()]
        db.close()
        return jsonify(reviews)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
