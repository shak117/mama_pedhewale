import os
import json
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from database import get_db, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mama-pedhewale-secret-key-1948'

# Administrative Portal Authentication Credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'MamaSatara@1948')

SUPER_ADMIN_USERNAME = os.environ.get('SUPER_ADMIN_USERNAME', 'superadmin')
SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'MamaSuper@1948')

def generate_order_id():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"MP-{datetime.now().strftime('%Y%m%d')}-{suffix}"

# Context processor for global data (categories, cart helpers)
@app.context_processor
def inject_global_data():
    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY display_order").fetchall()
    conn.close()
    return {
        'nav_categories': categories,
        'current_year': datetime.now().year,
        'store_phone': '+91 9699106264',
        'store_phone_alt': '+91 7620794973',
        'store_whatsapp': '919699106264',
        'store_email': 'contact@mamakandipedhewale.com',
        'store_address': 'Near Yashoda College, NH 4 Highway, Wadhe Phata, Pune - Satara Rd, Satara - 415003, Maharashtra'
    }

# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY display_order").fetchall()
    bestsellers = conn.execute("SELECT * FROM products WHERE is_bestseller = 1 LIMIT 8").fetchall()
    festive_specials = conn.execute("SELECT * FROM products WHERE is_festive = 1 LIMIT 4").fetchall()
    featured_reviews = conn.execute("""
        SELECT r.*, p.name as product_name 
        FROM reviews r 
        LEFT JOIN products p ON r.product_id = p.id 
        WHERE r.is_featured = 1
    """).fetchall()
    conn.close()
    return render_template(
        'index.html',
        categories=categories,
        bestsellers=bestsellers,
        festive_specials=festive_specials,
        reviews=featured_reviews
    )

@app.route('/products')
def products():
    conn = get_db()
    category_filter = request.args.get('category', '')
    dietary_filter = request.args.get('dietary', '')
    sort_by = request.args.get('sort', 'popular')
    search_query = request.args.get('search', '').strip()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if category_filter:
        query += " AND category_id = ?"
        params.append(category_filter)

    if dietary_filter == 'pure_ghee':
        query += " AND is_pure_ghee = 1"
    elif dietary_filter == 'sugar_free':
        query += " AND is_sugar_free = 1"

    if search_query:
        query += " AND (name LIKE ? OR name_mr LIKE ? OR description LIKE ? OR ingredients LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if sort_by == 'price_low':
        query += " ORDER BY price_250g ASC"
    elif sort_by == 'price_high':
        query += " ORDER BY price_250g DESC"
    elif sort_by == 'rating':
        query += " ORDER BY rating DESC"
    else:
        query += " ORDER BY is_bestseller DESC, rating DESC"

    products_list = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY display_order").fetchall()
    conn.close()

    return render_template(
        'products.html',
        products=products_list,
        categories=categories,
        current_category=category_filter,
        current_dietary=dietary_filter,
        current_sort=sort_by,
        search_query=search_query
    )

@app.route('/product/<product_id>')
def product_detail(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return redirect(url_for('products'))
    
    category = conn.execute("SELECT * FROM categories WHERE id = ?", (product['category_id'],)).fetchone()
    related = conn.execute(
        "SELECT * FROM products WHERE category_id = ? AND id != ? LIMIT 4",
        (product['category_id'], product_id)
    ).fetchall()
    reviews = conn.execute(
        "SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC",
        (product_id,)
    ).fetchall()
    conn.close()

    return render_template(
        'product_detail.html',
        product=product,
        category=category,
        related_products=related,
        reviews=reviews
    )

@app.route('/custom-box')
def custom_box():
    conn = get_db()
    # Fetch sweets eligible for custom box
    sweets = conn.execute("SELECT * FROM products WHERE category_id IN ('pedha', 'barfi', 'traditional-mithai') AND in_stock = 1").fetchall()
    conn.close()
    return render_template('custom_box.html', available_sweets=sweets)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/order-success/<order_id>')
def order_success(order_id):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return redirect(url_for('index'))
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()
    return render_template('order_success.html', order=order, items=items)

@app.route('/track-order')
def track_order():
    order_id = request.args.get('order_id', '').strip()
    phone = request.args.get('phone', '').strip()
    order = None
    items = []
    error = None

    if order_id or phone:
        conn = get_db()
        if order_id:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        elif phone:
            order = conn.execute("SELECT * FROM orders WHERE customer_phone = ? ORDER BY created_at DESC LIMIT 1", (phone,)).fetchone()
        
        if order:
            items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],)).fetchall()
        else:
            error = "No order found matching the provided details. Please verify your Order ID or registered mobile number."
        conn.close()

    return render_template('track_order.html', order=order, items=items, error=error, searched_id=order_id, searched_phone=phone)

@app.route('/corporate')
def corporate():
    return render_template('corporate.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['is_super_admin'] = True
            session['admin_role'] = 'Super Admin'
            return redirect(url_for('admin'))
        elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['is_super_admin'] = False
            session['admin_role'] = 'Staff Admin'
            return redirect(url_for('admin'))
        else:
            error = "Invalid admin username or password. Please try again."
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('is_super_admin', None)
    session.pop('admin_role', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db()
    stats = {
        'total_orders': conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        'total_revenue': conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_status = 'Paid' OR payment_method = 'cod'").fetchone()[0],
        'pending_fulfillment': conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Confirmed', 'Packed')").fetchone()[0],
        'total_products': conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    }
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        orders = conn.execute("SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC", (status_filter,)).fetchall()
    else:
        orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    
    products_list = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        ORDER BY c.display_order, p.name
    """).fetchall()

    inquiries = conn.execute("SELECT * FROM corporate_inquiries ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template(
        'admin.html',
        stats=stats,
        orders=orders,
        products=products_list,
        inquiries=inquiries,
        current_filter=status_filter,
        is_super_admin=session.get('is_super_admin', False),
        admin_role=session.get('admin_role', 'Staff Admin')
    )

# ==================== REST API ENDPOINTS ====================

@app.route('/api/products')
def api_products():
    conn = get_db()
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = "SELECT * FROM products WHERE in_stock = 1"
    params = []
    if category:
        query += " AND category_id = ?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR name_mr LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])
        
    products = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/check-pincode', methods=['POST'])
def api_check_pincode():
    data = request.get_json() or {}
    pincode = str(data.get('pincode', '')).strip()

    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return jsonify({
            'serviceable': False,
            'message': 'Please enter a valid 6-digit Indian PIN code.'
        }), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM serviceable_pincodes WHERE pincode = ?", (pincode,)).fetchone()
    conn.close()

    if row:
        days = row['delivery_days']
        timing = 'Same-Day Delivery available!' if row['same_day_available'] else f"Delivers in {days} business days"
        return jsonify({
            'serviceable': True,
            'pincode': row['pincode'],
            'city': row['city'],
            'state': row['state'],
            'same_day_available': bool(row['same_day_available']),
            'delivery_days': days,
            'express_fee': row['express_fee'],
            'message': f"Delivery available to {row['city']}, {row['state']}! ({timing})"
        })
    else:
        # Default all-India courier shipping for unlisted pincodes
        return jsonify({
            'serviceable': True,
            'pincode': pincode,
            'city': 'Your Location',
            'state': 'India',
            'same_day_available': False,
            'delivery_days': 3,
            'express_fee': 80,
            'message': f"Delivered via All-India Express Courier (approx 3-4 days)."
        })

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    data = request.get_json()
    if not data or not data.get('items'):
        return jsonify({'error': 'Cart is empty or invalid data provided.'}), 400

    order_id = generate_order_id()
    customer = data.get('customer', {})
    items = data.get('items', [])
    delivery = data.get('delivery', {})
    payment = data.get('payment', {})

    # Calculate totals
    subtotal = sum(int(item.get('price', 0)) * int(item.get('quantity', 1)) for item in items)
    
    # Free delivery on orders above 799, otherwise delivery fee
    delivery_fee = 0 if subtotal >= 799 else int(delivery.get('fee', 60))
    discount = int(data.get('discount', 0))
    total_amount = max(0, subtotal + delivery_fee - discount)

    payment_method = payment.get('method', 'cod')
    payment_status = 'Paid' if payment_method in ['upi', 'card'] else 'Pending'

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, address_line2, city, state, pincode,
                delivery_type, delivery_date, delivery_slot, gift_message,
                payment_method, payment_status, subtotal, delivery_fee, discount,
                total_amount, status, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            customer.get('name', 'Customer'),
            customer.get('phone', ''),
            customer.get('email', ''),
            customer.get('address1', ''),
            customer.get('address2', ''),
            customer.get('city', ''),
            customer.get('state', ''),
            customer.get('pincode', ''),
            delivery.get('type', 'standard'),
            delivery.get('date', datetime.now().strftime('%Y-%m-%d')),
            delivery.get('slot', 'Standard (10 AM - 7 PM)'),
            delivery.get('gift_message', ''),
            payment_method,
            payment_status,
            subtotal,
            delivery_fee,
            discount,
            total_amount,
            'Confirmed',
            data.get('notes', '')
        ))

        # Insert order items
        for item in items:
            is_custom = bool(item.get('is_custom_box', False))
            box_contents = json.dumps(item.get('box_contents')) if is_custom else None
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, product_name, weight_selected,
                    quantity, unit_price, item_total, is_custom_box, box_contents
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item.get('product_id'),
                item.get('name', 'Mithai Item'),
                item.get('weight', '500g'),
                int(item.get('quantity', 1)),
                int(item.get('price', 0)),
                int(item.get('price', 0)) * int(item.get('quantity', 1)),
                1 if is_custom else 0,
                box_contents
            ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f"Failed to record order: {str(e)}"}), 500

    conn.close()

    # Generate WhatsApp order text link
    wa_msg = f"Namaskar Mama Pedhewale!%0AOrder ID: {order_id}%0AName: {customer.get('name')}%0AItems: {len(items)} items%0ATotal: Rs. {total_amount}%0APayment: {payment_method.upper()}%0APincode: {customer.get('pincode')}"
    wa_url = f"https://wa.me/919822012345?text={wa_msg}"

    return jsonify({
        'success': True,
        'order_id': order_id,
        'total_amount': total_amount,
        'payment_status': payment_status,
        'whatsapp_url': wa_url,
        'redirect_url': url_for('order_success', order_id=order_id)
    })

@app.route('/api/corporate-inquiry', methods=['POST'])
def api_corporate_inquiry():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid submission.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO corporate_inquiries (
            company_name, contact_person, email, phone,
            estimated_boxes, box_type, occasion, event_date, message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('company_name', ''),
        data.get('contact_person', ''),
        data.get('email', ''),
        data.get('phone', ''),
        int(data.get('estimated_boxes', 50)),
        data.get('box_type', 'Premium Assorted Box'),
        data.get('occasion', 'Diwali / Corporate Event'),
        data.get('event_date', ''),
        data.get('message', '')
    ))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Thank you! Our Gifting Specialist will connect with you within 4 business hours with customized samples and pricing.'
    })

# ==================== ADMIN API ====================

@app.route('/api/admin/order/<order_id>/status', methods=['POST'])
def api_admin_update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized access. Please login as admin.'}), 401

    data = request.get_json() or {}
    new_status = data.get('status')
    payment_status = data.get('payment_status')

    if not new_status:
        return jsonify({'error': 'Missing status'}), 400

    conn = get_db()
    cursor = conn.cursor()
    if payment_status:
        cursor.execute("UPDATE orders SET status = ?, payment_status = ? WHERE id = ?", (new_status, payment_status, order_id))
    else:
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'order_id': order_id, 'new_status': new_status})

@app.route('/api/admin/order/<order_id>/delete', methods=['POST'])
def api_admin_delete_order(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized access. Please login as admin.'}), 401

    conn = get_db()
    cursor = conn.cursor()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found.'}), 404

    # Enforce rule: only orders before dispatching can be deleted
    if order['status'] in ['Dispatched', 'Out for Delivery', 'Delivered']:
        conn.close()
        return jsonify({'error': f"Cannot delete order because it has already been marked as '{order['status']}'. Only pre-dispatch orders can be deleted."}), 400

    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'order_id': order_id, 'message': f"Order {order_id} deleted successfully."})

@app.route('/api/admin/product/<product_id>/toggle-stock', methods=['POST'])
def api_admin_toggle_stock(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized access. Please login as admin.'}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET in_stock = CASE WHEN in_stock = 1 THEN 0 ELSE 1 END WHERE id = ?", (product_id,))
    conn.commit()
    new_val = conn.execute("SELECT in_stock FROM products WHERE id = ?", (product_id,)).fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'product_id': product_id, 'in_stock': bool(new_val)})

@app.route('/api/admin/product/<product_id>/update-prices', methods=['POST'])
def api_admin_update_product_prices(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized access. Please login.'}), 401
    
    if not session.get('is_super_admin'):
        return jsonify({'error': 'Super Admin privileges required to update product prices.'}), 403

    data = request.get_json() or {}
    try:
        p250 = int(data.get('price_250g', 0))
        p500 = int(data.get('price_500g', 0))
        p1kg = int(data.get('price_1kg', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Prices must be valid positive numbers.'}), 400

    if p250 <= 0 or p500 <= 0 or p1kg <= 0:
        return jsonify({'error': 'All pack prices (250g, 500g, 1kg) must be greater than zero.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    prod = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not prod:
        conn.close()
        return jsonify({'error': 'Product not found.'}), 404

    cursor.execute("""
        UPDATE products 
        SET price_250g = ?, price_500g = ?, price_1kg = ?
        WHERE id = ?
    """, (p250, p500, p1kg, product_id))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'product_id': product_id,
        'product_name': prod['name'],
        'price_250g': p250,
        'price_500g': p500,
        'price_1kg': p1kg,
        'message': f"Prices updated for {prod['name']}."
    })

if __name__ == '__main__':
    init_db()
    print("Starting Mama Pedhewale Web Application on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
