import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mama_pedhewale.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        name_mr TEXT NOT NULL,
        description TEXT,
        image_url TEXT,
        display_order INTEGER DEFAULT 0
    )
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        category_id TEXT NOT NULL,
        name TEXT NOT NULL,
        name_mr TEXT NOT NULL,
        tagline TEXT,
        description TEXT,
        image_url TEXT,
        badge TEXT,
        price_250g INTEGER NOT NULL,
        price_500g INTEGER NOT NULL,
        price_1kg INTEGER NOT NULL,
        shelf_life_days INTEGER DEFAULT 15,
        ingredients TEXT,
        is_pure_ghee BOOLEAN DEFAULT 1,
        is_sugar_free BOOLEAN DEFAULT 0,
        is_bestseller BOOLEAN DEFAULT 0,
        is_festive BOOLEAN DEFAULT 0,
        in_stock BOOLEAN DEFAULT 1,
        rating REAL DEFAULT 4.8,
        reviews_count INTEGER DEFAULT 45,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """)

    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        address_line1 TEXT NOT NULL,
        address_line2 TEXT,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        pincode TEXT NOT NULL,
        delivery_type TEXT DEFAULT 'standard',
        delivery_date TEXT,
        delivery_slot TEXT,
        gift_message TEXT,
        payment_method TEXT NOT NULL,
        payment_status TEXT DEFAULT 'Pending',
        subtotal INTEGER NOT NULL,
        delivery_fee INTEGER NOT NULL,
        discount INTEGER DEFAULT 0,
        total_amount INTEGER NOT NULL,
        status TEXT DEFAULT 'Confirmed',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Order Items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        product_id TEXT,
        product_name TEXT NOT NULL,
        weight_selected TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER NOT NULL,
        item_total INTEGER NOT NULL,
        is_custom_box BOOLEAN DEFAULT 0,
        box_contents TEXT,
        FOREIGN KEY (order_id) REFERENCES orders (id)
    )
    """)

    # Corporate Inquiries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS corporate_inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        estimated_boxes INTEGER NOT NULL,
        box_type TEXT,
        occasion TEXT,
        event_date TEXT,
        message TEXT,
        status TEXT DEFAULT 'New',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Customer Reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT,
        customer_name TEXT NOT NULL,
        city TEXT,
        rating INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        date TEXT,
        is_featured BOOLEAN DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)

    # Pincodes table for delivery validation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS serviceable_pincodes (
        pincode TEXT PRIMARY KEY,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        same_day_available BOOLEAN DEFAULT 0,
        delivery_days INTEGER DEFAULT 2,
        express_fee INTEGER DEFAULT 50
    )
    """)

    # Ensure tracking columns exist in orders table
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN tracking_number TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN courier_name TEXT DEFAULT 'Mama Fresh Express'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN dispatched_at TIMESTAMP")
    except Exception:
        pass

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema initialized successfully.")
