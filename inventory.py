import streamlit as st
from database import create_connection

# Initialize the inventory
def initialize_inventory():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item TEXT PRIMARY KEY,
            stock INTEGER,
            threshold INTEGER
        )
    ''')
    conn.commit()

    # Default inventory items
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

# Get current inventory
def get_inventory():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory = cursor.fetchall()
    conn.close()
    return inventory

# Reduce inventory based on sales
def reduce_inventory(sale_items):
    conn = create_connection()
    cursor = conn.cursor()

    for item, quantity in sale_items.items():
        cursor.execute('''
            UPDATE inventory
            SET stock = stock - ?
            WHERE item = ?
        ''', (quantity, item))
    conn.commit()
    conn.close()

# Generate low inventory alerts
def low_inventory_alert():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT item, stock FROM inventory WHERE stock <= threshold')
    low_stock_items = cursor.fetchall()
    conn.close()
    return low_stock_items

# Generate restock list
def generate_restock_list():
    low_stock_items = low_inventory_alert()
    restock_list = [item[0] for item in low_stock_items]
    return restock_list

# Manually restock inventory
def restock_inventory(item, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE inventory
        SET stock = stock + ?
        WHERE item = ?
    ''', (quantity, item))
    conn.commit()
    conn.close()

# Admin interface for managing inventory
def manage_inventory():
    st.title("Inventory Management")

    # Display current inventory
    st.subheader("Current Inventory")
    inventory = get_inventory()
    for item in inventory:
        st.write(f"{item[0]}: {item[1]} units (Threshold: {item[2]} units)")

    # Low inventory alerts
    low_stock_items = low_inventory_alert()
    if low_stock_items:
        st.warning("Low Inventory Alert!")
        for item, stock in low_stock_items:
            st.write(f"{item}: Only {stock} units left!")

    # Restock items
    st.subheader("Restock Inventory")
    item_to_restock = st.selectbox("Select Item to Restock", [item[0] for item in inventory])
    restock_quantity = st.number_input("Quantity to Add", min_value=1, step=1)
    if st.button("Restock"):
        restock_inventory(item_to_restock, restock_quantity)
        st.success(f"Restocked {restock_quantity} units of {item_to_restock}.")

    # Display restock list
    st.subheader("Restock List")
    restock_list = generate_restock_list()
    if restock_list:
        st.write("Items to Restock:")
        for item in restock_list:
            st.write(f"- {item}")
    else:
        st.write("No items need restocking at the moment.")
