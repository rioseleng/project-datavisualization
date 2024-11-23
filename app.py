import streamlit as st
import matplotlib.pyplot as plt
from database import (
    add_order,
    generate_booking_number,
    update_payment_status,
    reduce_inventory,
    create_tables,
    initialize_inventory,
    create_default_admin,
    get_inventory,
    restock_inventory,
    save_feedback,
    get_order_history,
    get_sales_data,
    get_feedback,
    add_coupon,
    validate_coupon,
    get_low_stock_items,
    get_current_orders,
    get_inventory_health,
)
import stripe
import pandas as pd
import matplotlib.pyplot as plt

# Set your Stripe Secret Key
stripe.api_key = "sk_test_51QIp8UDHM9kjOuDQoaRrAgdwyIVWSM5LQUPYcjzrFj0d7mn2bxW0O0JZou4EBNkZA6m0cEFsQ3jksba8LwHizZKf00zkYD1FVb"

# Initialize database and default admin
create_tables()
initialize_inventory()
create_default_admin()


def display_menu():
    """Display the coffee menu."""
    return {
        "Americano": 5.0,
        "Cappuccino": 6.0,
        "Latte": 6.5,
        "Caramel Macchiato": 7.0,
        "Espresso": 4.0
    }


def process_payment(amount, booking_number):
    """Create a Stripe Checkout Session and return the payment URL."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"Order {booking_number}"},
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=f"http://localhost:8501?payment_success=true&booking_number={booking_number}",
            cancel_url=f"http://localhost:8501?payment_canceled=true&booking_number={booking_number}",
        )
        return session.url
    except Exception as e:
        st.error(f"Error creating payment session: {e}")
        return None


def process_payment_query_params():
    """Process query parameters for payment success or cancellation."""
    query_params = st.experimental_get_query_params()
    if "payment_success" in query_params and query_params["payment_success"][0] == "true":
        booking_number = query_params.get("booking_number", [None])[0]
        if booking_number:
            update_payment_status(booking_number, "Paid")
            st.success(f"Payment successful for Booking Number: {booking_number}")
    elif "payment_canceled" in query_params and query_params["payment_canceled"][0] == "true":
        booking_number = query_params.get("booking_number", [None])[0]
        if booking_number:
            update_payment_status(booking_number, "Canceled")
            st.warning(f"Payment canceled for Booking Number: {booking_number}")


def customer_dashboard():
    """Customer dashboard for placing orders and leaving feedback."""
    if not st.session_state.get("logged_in"):
        st.error("You are not logged in!")
        return

    # Process payment query parameters for Stripe
    process_payment_query_params()
    username = st.session_state.get("username")
    st.subheader(f"Welcome, {username}!")

    menu = ["Place Order", "Order History", "Leave Feedback"]
    choice = st.selectbox("Choose an Option", menu)

    if choice == "Place Order":
        # Display menu and order form
        menu = display_menu()
        st.header("Coffee Menu")
        st.table([{"Item": item, "Price": f"${price:.2f}"} for item, price in menu.items()])

        coffee_type = st.selectbox("Select Coffee Type", list(menu.keys()))
        size = st.selectbox("Select Size", ["Small", "Medium", "Large"])
        addons = st.multiselect("Select Add-ons", ["Extra Sugar", "Extra Milk", "Whipped Cream"])
        quantity = st.number_input("Quantity", min_value=1, step=1)

        # Coupon code section
        coupon_code = st.text_input("Enter Coupon Code (Optional)")
        discount = 0
        if st.button("Apply Coupon"):
            if coupon_code:
                coupon_details = validate_coupon(coupon_code)
                if coupon_details:
                    discount_percent, valid_until = coupon_details
                    st.success(f"Coupon Applied! {discount_percent}% discount will be applied.")
                    discount = discount_percent
                else:
                    st.error("Invalid or expired coupon code.")
            else:
                st.warning("Please enter a coupon code.")

        # Calculate price
        price_per_item = menu[coffee_type]
        if size == "Medium":
            price_per_item += 1.0
        elif size == "Large":
            price_per_item += 2.0
        price_per_item += 0.5 * len(addons)
        total_price = price_per_item * quantity

        # Apply discount if applicable
        if discount > 0:
            discount_amount = total_price * (discount / 100)
            total_price -= discount_amount
            st.info(f"Discount Applied: ${discount_amount:.2f}")

        # Display final price
        st.write(f"**Total Price: ${total_price:.2f}**")

        # Place order button
        if st.button("Place Order"):
            booking_number = generate_booking_number()
            order_details = {
                'username': username,
                'coffee_type': coffee_type,
                'size': size,
                'addons': ", ".join(addons),
                'price': total_price,
                'booking_number': booking_number
            }
            add_order(order_details)
            reduce_inventory({"Coffee Beans": quantity})  # Example: Update inventory
            st.success(f"Order placed! Booking Number: {booking_number}")

            # Pass the discounted total price to the payment process
            payment_url = process_payment(total_price, booking_number)
            if payment_url:
                st.markdown(f"[Proceed to Payment]({payment_url})", unsafe_allow_html=True)

    elif choice == "Order History":
        order_history = get_order_history(username)
        if order_history:
            st.table(order_history)
        else:
            st.info("No orders found.")

    elif choice == "Leave Feedback":
        booking_number = st.text_input("Enter Booking Number")
        feedback = st.text_area("Leave Feedback")
        rating = st.slider("Rate Your Experience (1-5)", 1, 5, step=1)
        if st.button("Submit Feedback"):
            success = save_feedback(booking_number, feedback, rating)
            if success:
                st.success("Feedback submitted!")
            else:
                st.error("Failed to save feedback.")

    if st.button("Sign Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False


# Analytics Dashboard
def analytics_dashboard():
    st.title("Analytics Dashboard")
    
    # Real-time orders
    st.subheader("Current Orders")
    orders = get_current_orders()
    if orders:
        st.table(orders)
    else:
        st.info("No current orders available.")

    # Inventory health check
    st.subheader("Inventory Health Check")
    inventory_health = get_inventory_health()
    
    if inventory_health:
        items = [item[0] for item in inventory_health]
        stocks = [item[1] for item in inventory_health]
        thresholds = [item[2] for item in inventory_health]

        # Create a bar chart for inventory health
        fig, ax = plt.subplots()
        bars = ax.bar(items, stocks, color=["red" if stock <= threshold else "blue" for stock, threshold in zip(stocks, thresholds)])
        ax.axhline(y=20, color='orange', linestyle='--', label="Low Stock Threshold")  # Example threshold line
        ax.set_ylabel("Stock Level")
        ax.set_title("Inventory Health Check")
        ax.legend()
        st.pyplot(fig)

        # Display inventory details below the chart
        for item, stock, threshold in inventory_health:
            status = "Low Stock" if stock <= threshold else "Healthy"
            st.write(f"{item}: {stock} units in stock ({status})")
    else:
        st.info("All inventory levels are healthy.")


def admin_dashboard():
    """Admin dashboard for managing inventory, sales, and feedback."""
    st.title("Admin Dashboard")
    task = st.selectbox("Choose Task", ["Manage Inventory", "Manage Coupons", "Analytics Dashboard", "View Sales", "View Feedback"])

    if task == "Manage Inventory":
        st.header("Current Inventory")
        inventory = get_inventory()
        st.table([{"Item": item[0], "Stock": item[1], "Threshold": item[2]} for item in inventory])

        st.subheader("Restock Inventory")
        item = st.selectbox("Select Item to Restock", [item[0] for item in inventory])
        quantity = st.number_input("Quantity to Add", min_value=1, step=1)
        if st.button("Restock"):
            restock_inventory(item, quantity)
            st.success(f"Restocked {quantity} units of {item}.")
    elif task == "Manage Coupons":
        manage_coupons()
    elif task == "Analytics Dashboard":
        analytics_dashboard()
    elif task == "View Sales":
        st.header("Sales Reports")
        period = st.selectbox("Select Report Period", ["Daily", "Weekly", "Monthly"])
        sales_data = get_sales_data()
        if sales_data:
            st.table(pd.DataFrame(sales_data, columns=["Coffee Type", "Revenue"]))
            st.bar_chart(pd.DataFrame(sales_data, columns=["Coffee Type", "Revenue"]))
        else:
            st.info("No sales data available.")
    elif task == "View Feedback":
        st.header("Customer Feedback")
        feedback_data = get_feedback()
        if feedback_data:
            st.table(pd.DataFrame(feedback_data, columns=["Feedback ID", "Booking Number", "Feedback", "Rating"]))
        else:
            st.info("No feedback available.")

    if st.button("Sign Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False


def login():
    """Login page for customers and admins."""
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "adminpassword":
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.session_state.username = username
            admin_dashboard()
        else:
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.session_state.username = username
            customer_dashboard()


def login():
    """Login page for customers and admins."""
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "adminpassword":
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.session_state.username = username
            admin_dashboard()
        else:
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.session_state.username = username
            customer_dashboard()


def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False

    if st.session_state.logged_in:
        if st.session_state.is_admin:
            admin_dashboard()
        else:
            customer_dashboard()
    else:
        login()


if __name__ == "__main__":
    main()
