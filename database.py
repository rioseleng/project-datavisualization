import sqlite3
import bcrypt


def create_connection():
    """Establish a connection to the SQLite database."""
    try:
        conn = sqlite3.connect('coffee_shop.db')
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def create_tables():
    """Create tables for storing user, order, inventory, feedback, and coupon information."""
    conn = create_connection()
    if conn is None:
        return
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            coffee_type TEXT,
            size TEXT,
            addons TEXT,
            price REAL,
            discount REAL DEFAULT 0.0,
            booking_number TEXT UNIQUE,
            status TEXT DEFAULT 'Pending',
            payment_status TEXT DEFAULT 'Pending',
            ready_notification_sent INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item TEXT PRIMARY KEY,
            stock INTEGER,
            threshold INTEGER
        )
    ''')

    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_number TEXT UNIQUE,
            feedback TEXT,
            rating INTEGER,
            FOREIGN KEY (booking_number) REFERENCES orders(booking_number)
        )
    ''')

    # Table for coupons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            coupon_code TEXT PRIMARY KEY,
            discount_percent REAL,
            valid_until DATETIME
        )
    ''')

    conn.commit()
    conn.close()


def create_default_admin():
    """Create a default admin user."""
    conn = create_connection()
    if conn is None:
        return
    cursor = conn.cursor()

    username = "admin"
    password = "adminpassword"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, is_admin)
        VALUES (?, ?, 1)
    ''', (username, hashed_password))
    conn.commit()
    conn.close()


def initialize_inventory():
    """Initialize default inventory levels."""
    conn = create_connection()
    cursor = conn.cursor()
    default_items = [
        ("Coffee Beans", 100, 20),
        ("Milk", 100, 20),
        ("Sugar", 100, 20),
        ("Cups", 100, 20)
    ]
    for item, stock, threshold in default_items:
        cursor.execute('''
            INSERT OR IGNORE INTO inventory (item, stock, threshold)
            VALUES (?, ?, ?)
        ''', (item, stock, threshold))
    conn.commit()
    conn.close()


def get_inventory():
    """Retrieve the current inventory."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory = cursor.fetchall()
    conn.close()
    return inventory


def restock_inventory(item, quantity):
    """Restock an item in the inventory."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE inventory
        SET stock = stock + ?
        WHERE item = ?
    ''', (quantity, item))
    conn.commit()
    conn.close()


def reduce_inventory(items):
    """Reduce inventory levels based on a sale."""
    conn = create_connection()
    cursor = conn.cursor()
    for item, quantity in items.items():
        cursor.execute('''
            UPDATE inventory
            SET stock = stock - ?
            WHERE item = ?
        ''', (quantity, item))
    conn.commit()
    conn.close()


def add_order(order_details):
    """Add a new order to the database."""
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO orders (username, coffee_type, size, addons, price, booking_number, status, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', 'Pending')
        ''', (
            order_details['username'],
            order_details['coffee_type'],
            order_details['size'],
            order_details['addons'],
            order_details['price'],
            order_details['booking_number']
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding order: {e}")
        return False
    finally:
        conn.close()


def generate_booking_number():
    """Generate a unique booking number."""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d%H%M%S")


def update_payment_status(booking_number, status):
    """Update the payment status of an order."""
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE orders
            SET payment_status = ?
            WHERE booking_number = ?
        ''', (status, booking_number))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating payment status: {e}")
        return False
    finally:
        conn.close()


def save_feedback(booking_number, feedback, rating):
    """Save customer feedback."""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO feedback (booking_number, feedback, rating)
            VALUES (?, ?, ?)
        ''', (booking_number, feedback, rating))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving feedback: {e}")
        return False
    finally:
        conn.close()


def get_feedback():
    """Retrieve all feedback from the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM feedback')
    feedback = cursor.fetchall()
    conn.close()
    return feedback


def get_order_history(username):
    """Retrieve the order history for a specific customer."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT coffee_type, size, addons, price, booking_number, payment_status, timestamp
        FROM orders WHERE username = ?
    ''', (username,))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_sales_data():
    """Retrieve sales data for reporting."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT coffee_type, SUM(price) as revenue
        FROM orders
        GROUP BY coffee_type
    ''')
    sales_data = cursor.fetchall()
    conn.close()
    return sales_data


# START ADDITIONS FOR COUPONS AND ANALYTICS
def add_coupon(coupon_code, discount_percent, valid_until):
    """Add a new coupon."""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO coupons (coupon_code, discount_percent, valid_until)
            VALUES (?, ?, ?)
        ''', (coupon_code, discount_percent, valid_until))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding coupon: {e}")
        return False
    finally:
        conn.close()


def validate_coupon(coupon_code):
    """Validate if a coupon code is valid."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT discount_percent, valid_until FROM coupons WHERE coupon_code = ?
    ''', (coupon_code,))
    result = cursor.fetchone()
    conn.close()
    return result if result else None


def get_low_stock_items():
    """Fetch low stock inventory items."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT item, stock FROM inventory WHERE stock <= threshold
    ''')
    low_stock_items = cursor.fetchall()
    conn.close()
    return low_stock_items


def mark_order_ready(booking_number):
    """Mark an order as ready."""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE orders SET status = 'Ready', ready_notification_sent = 1
            WHERE booking_number = ?
        ''', (booking_number,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating order status: {e}")
        return False
    finally:
        conn.close()


def get_current_orders():
    """Fetch all current orders with status 'Pending'."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT booking_number, coffee_type, size, addons, status, timestamp
        FROM orders WHERE status = 'Pending'
    ''')
    current_orders = cursor.fetchall()
    conn.close()
    return current_orders


def get_inventory_health():
    """Fetch the health of inventory."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT item, stock, threshold FROM inventory
    ''')
    inventory_health = cursor.fetchall()
    conn.close()
    return inventory_health
# END ADDITIONS
