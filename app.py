import os
import json
import random
import string
import hmac
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from database import get_db, init_db

# Load .env file if present in project directory
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_file):
    try:
        with open(_env_file, 'r', encoding='utf-8') as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    _k = _k.strip()
                    _v = _v.strip().strip("'\"")
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v
    except Exception:
        pass

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mama-pedhewale-secret-key-1948')

# Administrative Portal Authentication Credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'MamaSatara@1948')

SUPER_ADMIN_USERNAME = os.environ.get('SUPER_ADMIN_USERNAME', 'superadmin')
SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'MamaSuper@1948')

# Razorpay Payment Gateway Configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

def get_razorpay_client():
    """Initializes and returns Razorpay client if credentials are configured."""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception as e:
        app.logger.error(f"Error initializing Razorpay client: {e}")
        return None

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
        client = get_razorpay_client()
        if client:
            try:
                rzp_orders = client.order.all({'count': 10})
                matched = None
                for o in rzp_orders.get('items', []):
                    if o.get('receipt') == order_id:
                        matched = o
                        break
                if matched:
                    notes = matched.get('notes', {})
                    amt = (matched.get('amount', 0)) / 100.0
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO orders (
                            id, customer_name, customer_phone, customer_email,
                            address_line1, city, state, pincode, delivery_type,
                            delivery_date, delivery_slot, payment_method, payment_status,
                            subtotal, delivery_fee, discount, total_amount, status,
                            razorpay_order_id
                        )
                        VALUES (?, ?, ?, ?, ?, ?, 'Maharashtra', ?, 'standard',
                            ?, 'Standard', 'razorpay', 'Paid', ?, 0, 0, ?, 'Confirmed', ?)
                    """, (
                        order_id,
                        notes.get('customer_name', 'Valued Customer'),
                        notes.get('customer_phone', ''),
                        notes.get('customer_email', ''),
                        notes.get('customer_address', ''),
                        notes.get('customer_city', 'Satara'),
                        notes.get('customer_pincode', ''),
                        datetime.now().strftime('%Y-%m-%d'),
                        amt, amt, matched.get('id')
                    ))
                    conn.commit()
                    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            except Exception as e:
                app.logger.warning(f"Could not fetch order from Razorpay for success page: {e}")

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

def recalculate_order_items(items, conn):
    """
    Recalculates cart items server-side using authoritative database prices.
    Prevents client-side price tampering. Returns: (validated_items, subtotal)
    """
    validated_items = []
    subtotal = 0

    for item in items:
        qty = max(1, int(item.get('quantity', 1)))
        prod_id = item.get('id') or item.get('product_id')
        weight = item.get('weight', '500g')
        is_custom = bool(item.get('is_custom_box', False))

        if is_custom and item.get('box_contents'):
            box_price = 0
            box_contents = item.get('box_contents', {})
            for slot_key, sweet_info in box_contents.items():
                sweet_id = sweet_info.get('id') if isinstance(sweet_info, dict) else sweet_info
                row = conn.execute("SELECT price_500g, price_1kg FROM products WHERE id = ?", (sweet_id,)).fetchone()
                if row:
                    portion = (row['price_500g'] / 4.0) if weight == '500g' else (row['price_1kg'] / 4.0)
                    box_price += portion
                else:
                    box_price += (int(item.get('price', 400)) / 4.0)
            unit_price = int(round(box_price))
            prod_name = item.get('name', f"Custom Assorted Mithai Box ({weight})")
        else:
            row = conn.execute("SELECT name, price_250g, price_500g, price_1kg, in_stock FROM products WHERE id = ?", (prod_id,)).fetchone()
            if row:
                prod_name = row['name']
                if weight == '250g':
                    unit_price = int(row['price_250g'])
                elif weight == '1kg':
                    unit_price = int(row['price_1kg'])
                else:
                    unit_price = int(row['price_500g'])
            else:
                unit_price = int(item.get('price', 0))
                prod_name = item.get('name', 'Mithai Item')

        item_total = unit_price * qty
        subtotal += item_total
        validated_items.append({
            'product_id': prod_id,
            'name': prod_name,
            'weight': weight,
            'quantity': qty,
            'unit_price': unit_price,
            'item_total': item_total,
            'is_custom_box': is_custom,
            'box_contents': item.get('box_contents') if is_custom else None
        })

    return validated_items, subtotal

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """Handles standard/COD order placements with server-side price validation."""
    data = request.get_json() or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'Cart is empty or invalid data provided.'}), 400

    order_id = generate_order_id()
    customer = data.get('customer', {})
    delivery = data.get('delivery', {})
    payment = data.get('payment', {})

    conn = get_db()
    cursor = conn.cursor()

    # Recalculate totals server-side
    validated_items, subtotal = recalculate_order_items(items, conn)
    
    # Free delivery on orders above 799, otherwise delivery fee
    delivery_fee = 0 if subtotal >= 799 else int(delivery.get('fee', 60))
    discount = int(data.get('discount', 0))
    total_amount = max(0, subtotal + delivery_fee - discount)

    payment_method = payment.get('method', 'cod')
    payment_status = 'Pending' if payment_method == 'cod' else ('Paid' if payment_method in ['upi', 'card'] else 'Pending')

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
        for item in validated_items:
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
                item.get('name'),
                item.get('weight'),
                item.get('quantity'),
                item.get('unit_price'),
                item.get('item_total'),
                1 if is_custom else 0,
                box_contents
            ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f"Failed to record order: {str(e)}"}), 500

    conn.close()

    wa_msg = f"Namaskar Mama Pedhewale!%0AOrder ID: {order_id}%0AName: {customer.get('name')}%0AItems: {len(validated_items)} items%0ATotal: Rs. {total_amount}%0APayment: {payment_method.upper()}%0APincode: {customer.get('pincode')}"
    wa_url = f"https://wa.me/919699106264?text={wa_msg}"

    return jsonify({
        'success': True,
        'order_id': order_id,
        'total_amount': total_amount,
        'payment_status': payment_status,
        'whatsapp_url': wa_url,
        'redirect_url': url_for('order_success', order_id=order_id)
    })

# ==================== RAZORPAY PAYMENT GATEWAY ENDPOINTS ====================

@app.route('/api/payments/razorpay/create-order', methods=['POST'])
def api_razorpay_create_order():
    """
    Creates an internal pending order and requests a Razorpay Order ID.
    Recalculates price server-side using authoritative database prices.
    Converts amount to paise format for Razorpay.
    """
    data = request.get_json() or {}
    items = data.get('items', [])
    customer = data.get('customer', {})
    delivery = data.get('delivery', {})

    if not items:
        return jsonify({'error': 'Cart is empty. Please add items before checking out.'}), 400

    if not customer.get('name') or not customer.get('phone') or not customer.get('address1') or not customer.get('pincode'):
        return jsonify({'error': 'Please provide all required delivery details (name, phone, address, and pincode).'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Recalculate totals server-side
    validated_items, subtotal = recalculate_order_items(items, conn)
    
    if subtotal <= 0:
        conn.close()
        return jsonify({'error': 'Invalid order items or amounts.'}), 400

    # Free delivery on orders above 799, otherwise delivery fee
    delivery_fee = 0 if subtotal >= 799 else int(delivery.get('fee', 60))
    discount = int(data.get('discount', 0))
    total_amount = max(1, subtotal + delivery_fee - discount)
    amount_in_paise = int(total_amount * 100)

    order_id = generate_order_id()
    client = get_razorpay_client()

    razorpay_order_id = None
    if client:
        try:
            rzp_payload = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': order_id,
                'notes': {
                    'order_id': order_id,
                    'customer_name': customer.get('name', ''),
                    'customer_phone': customer.get('phone', ''),
                    'customer_email': customer.get('email', ''),
                    'customer_address': customer.get('address1', ''),
                    'customer_city': customer.get('city', ''),
                    'customer_pincode': customer.get('pincode', '')
                }
            }
            rzp_order = client.order.create(rzp_payload)
            razorpay_order_id = rzp_order['id']
        except Exception as e:
            conn.close()
            app.logger.error(f"Razorpay order creation failed: {e}")
            return jsonify({'error': f"Payment gateway error: {str(e)}"}), 502
    else:
        # If credentials are not configured, return clear instructions
        conn.close()
        return jsonify({
            'error': 'Razorpay payment gateway credentials not configured on the server. Please configure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment variables or .env file.'
        }), 500

    try:
        # Create order in database with status 'Pending' and payment_status 'Payment Initiated'
        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, address_line2, city, state, pincode,
                delivery_type, delivery_date, delivery_slot, gift_message,
                payment_method, payment_status, subtotal, delivery_fee, discount,
                total_amount, status, notes, razorpay_order_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'razorpay', 'Payment Initiated', ?, ?, ?, ?, 'Pending', ?, ?)
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
            delivery.get('slot', 'Standard Express'),
            delivery.get('gift_message', ''),
            subtotal,
            delivery_fee,
            discount,
            total_amount,
            data.get('notes', ''),
            razorpay_order_id
        ))

        # Insert items
        for item in validated_items:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, product_name, weight_selected,
                    quantity, unit_price, item_total, is_custom_box, box_contents
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item['product_id'],
                item['name'],
                item['weight'],
                item['quantity'],
                item['unit_price'],
                item['item_total'],
                1 if item['is_custom_box'] else 0,
                json.dumps(item['box_contents']) if item['is_custom_box'] and item['box_contents'] else None
            ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        app.logger.error(f"Database error while saving pending order: {e}")
        return jsonify({'error': f"Failed to record pending order: {str(e)}"}), 500

    conn.close()

    return jsonify({
        'success': True,
        'order_id': order_id,
        'razorpay_order_id': razorpay_order_id,
        'amount': amount_in_paise,
        'amount_in_rupees': total_amount,
        'currency': 'INR',
        'key_id': RAZORPAY_KEY_ID,
        'business_name': 'Mama Pedhewale (मामा कंदी पेढेवाले)',
        'description': f"Fresh Satara Mithai Order #{order_id}",
        'prefill': {
            'name': customer.get('name', ''),
            'contact': customer.get('phone', ''),
            'email': customer.get('email', '')
        }
    })

@app.route('/api/payments/razorpay/verify', methods=['POST'])
def api_razorpay_verify():
    """
    Cryptographically verifies Razorpay payment signature using RAZORPAY_KEY_SECRET.
    Only after successful verification is the order marked as 'Paid' and 'Confirmed'.
    """
    data = request.get_json() or {}
    order_id = data.get('order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([order_id, razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return jsonify({'success': False, 'error': 'Missing required payment verification parameters.'}), 400

    # 1. Cryptographic verification using Razorpay Key Secret
    verified = False
    client = get_razorpay_client()
    if client and RAZORPAY_KEY_SECRET:
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            verified = True
        except Exception as e:
            app.logger.warning(f"Razorpay SDK signature check failed: {e}")
            verified = False
    elif RAZORPAY_KEY_SECRET:
        msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
        expected_sig = hmac.new(RAZORPAY_KEY_SECRET.encode('utf-8'), msg, hashlib.sha256).hexdigest()
        verified = hmac.compare_digest(expected_sig, razorpay_signature)

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not verified:
        if order:
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET payment_status = 'Failed' WHERE id = ?", (order_id,))
            conn.commit()
        conn.close()
        app.logger.error(f"Razorpay signature mismatch for order {order_id}. Payment ID: {razorpay_payment_id}")
        return jsonify({'success': False, 'error': 'Payment signature verification failed. Untrusted payment attempt.'}), 400

    # 2. Idempotency check: if order is already marked Paid, return success immediately
    if order and order['payment_status'] == 'Paid':
        conn.close()
        return jsonify({
            'success': True,
            'message': 'Order already verified as Paid.',
            'order_id': order_id,
            'redirect_url': url_for('order_success', order_id=order_id)
        })

    # 3. Verify Razorpay order ID matches if order record was found
    if order and order['razorpay_order_id'] and order['razorpay_order_id'] != razorpay_order_id:
        conn.close()
        return jsonify({'success': False, 'error': 'Razorpay order ID does not match server order record.'}), 400

    # 4. Update or reconstruct order in local database
    cursor = conn.cursor()
    if order:
        cursor.execute("""
            UPDATE orders 
            SET status = 'Confirmed',
                payment_status = 'Paid',
                razorpay_payment_id = ?,
                razorpay_signature = ?
            WHERE id = ?
        """, (razorpay_payment_id, razorpay_signature, order_id))
        conn.commit()
    else:
        # In multi-container serverless environments (e.g. Vercel), reconstruct order from Razorpay
        cust_name = 'Customer'
        cust_phone = ''
        cust_email = ''
        cust_addr = ''
        cust_city = 'Satara'
        cust_pin = ''
        total_amt = 0
        if client:
            try:
                rzp_ord = client.order.fetch(razorpay_order_id)
                notes = rzp_ord.get('notes', {})
                cust_name = notes.get('customer_name', 'Customer')
                cust_phone = notes.get('customer_phone', '')
                cust_email = notes.get('customer_email', '')
                cust_addr = notes.get('customer_address', '')
                cust_city = notes.get('customer_city', 'Satara')
                cust_pin = notes.get('customer_pincode', '')
                total_amt = (rzp_ord.get('amount', 0)) / 100.0
            except Exception as e:
                app.logger.warning(f"Could not fetch order from Razorpay for reconstruction: {e}")

        cursor.execute("""
            INSERT INTO orders (
                id, customer_name, customer_phone, customer_email,
                address_line1, city, state, pincode, delivery_type,
                delivery_date, delivery_slot, payment_method, payment_status,
                subtotal, delivery_fee, discount, total_amount, status,
                razorpay_order_id, razorpay_payment_id, razorpay_signature
            )
            VALUES (?, ?, ?, ?, ?, ?, 'Maharashtra', ?, 'standard',
                ?, 'Standard', 'razorpay', 'Paid', ?, 0, 0, ?, 'Confirmed',
                ?, ?, ?)
        """, (
            order_id, cust_name, cust_phone, cust_email,
            cust_addr, cust_city, cust_pin,
            datetime.now().strftime('%Y-%m-%d'),
            total_amt, total_amt,
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        ))
        conn.commit()

    conn.close()

    return jsonify({
        'success': True,
        'order_id': order_id,
        'payment_id': razorpay_payment_id,
        'message': 'Payment successfully verified and confirmed! 🎉',
        'redirect_url': url_for('order_success', order_id=order_id)
    })

@app.route('/api/payments/razorpay/webhook', methods=['POST'])
def api_razorpay_webhook():
    """
    Receives and processes asynchronous payment notifications from Razorpay.
    Verifies webhook signature using RAZORPAY_WEBHOOK_SECRET (or RAZORPAY_KEY_SECRET).
    Idempotent processing prevents duplicate fulfillment actions.
    """
    webhook_body = request.get_data(as_text=True)
    webhook_signature = request.headers.get('X-Razorpay-Signature', '')
    secret = RAZORPAY_WEBHOOK_SECRET or RAZORPAY_KEY_SECRET

    if not secret:
        app.logger.warning("Webhook received but webhook secret is not configured on server.")
        return jsonify({'error': 'Webhook secret not configured on server.'}), 500

    # Verify signature
    verified = False
    client = get_razorpay_client()
    if client and hasattr(client.utility, 'verify_webhook_signature'):
        try:
            client.utility.verify_webhook_signature(webhook_body, webhook_signature, secret)
            verified = True
        except Exception:
            verified = False
    else:
        expected = hmac.new(secret.encode('utf-8'), webhook_body.encode('utf-8'), hashlib.sha256).hexdigest()
        verified = hmac.compare_digest(expected, webhook_signature)

    if not verified:
        app.logger.error("Invalid Razorpay webhook signature received.")
        return jsonify({'error': 'Invalid webhook signature'}), 400

    try:
        event_data = json.loads(webhook_body)
    except Exception:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    event_type = event_data.get('event')
    payload = event_data.get('payload', {})
    
    conn = get_db()
    cursor = conn.cursor()

    if event_type in ['order.paid', 'payment.captured']:
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_entity = payload.get('order', {}).get('entity', {})
        
        rzp_order_id = payment_entity.get('order_id') or order_entity.get('id')
        rzp_payment_id = payment_entity.get('id')
        internal_order_id = payment_entity.get('notes', {}).get('order_id') or order_entity.get('receipt')

        order = None
        if rzp_order_id:
            order = conn.execute("SELECT * FROM orders WHERE razorpay_order_id = ?", (rzp_order_id,)).fetchone()
        if not order and internal_order_id:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (internal_order_id,)).fetchone()

        if order and order['payment_status'] != 'Paid':
            cursor.execute("""
                UPDATE orders 
                SET status = 'Confirmed',
                    payment_status = 'Paid',
                    razorpay_payment_id = COALESCE(razorpay_payment_id, ?),
                    payment_details = ?
                WHERE id = ?
            """, (rzp_payment_id, json.dumps(payment_entity), order['id']))
            conn.commit()
            app.logger.info(f"Order {order['id']} marked Paid via webhook event {event_type}")

    elif event_type == 'payment.failed':
        payment_entity = payload.get('payment', {}).get('entity', {})
        rzp_order_id = payment_entity.get('order_id')
        if rzp_order_id:
            order = conn.execute("SELECT * FROM orders WHERE razorpay_order_id = ?", (rzp_order_id,)).fetchone()
            if order and order['payment_status'] != 'Paid':
                cursor.execute("UPDATE orders SET payment_status = 'Failed' WHERE id = ?", (order['id'],))
                conn.commit()

    conn.close()
    return jsonify({'status': 'ok', 'event': event_type}), 200

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
    if new_status in ['Dispatched', 'Out for Delivery']:
        cursor.execute("""
            UPDATE orders 
            SET status = ?, 
                tracking_number = COALESCE(tracking_number, 'MP-EXP-' || strftime('%m%d', 'now') || '-' || substr(id, -5)),
                dispatched_at = COALESCE(dispatched_at, datetime('now', 'localtime'))
            WHERE id = ?
        """, (new_status, order_id))
    elif payment_status:
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
