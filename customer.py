import streamlit as st
from database import (
    add_order,
    generate_booking_number,
    update_payment_status,
    reduce_inventory,
    get_order_history,
    save_feedback,
    validate_coupon  # Newly added for coupon validation
)

def display_menu():
    # Coffee menu with prices
    return {
        "Americano": 5.0,
        "Cappuccino": 6.0,
        "Latte": 6.5,
        "Caramel Macchiato": 7.0,
        "Espresso": 4.0
    }

def process_mock_payment(booking_number):
    # Generate a mock payment confirmation URL
    return f"http://localhost:8501/?payment_success=true&booking_number={booking_number}"

def process_payment_query_params():
    """Process query parameters to handle payment success."""
    query_params = st.experimental_get_query_params()
    if "payment_success" in query_params and query_params["payment_success"][0] == "true":
        booking_number = query_params.get("booking_number", [None])[0]
        if booking_number:
            update_payment_status(booking_number, "Paid")
            st.success(f"Payment successful for Booking Number: {booking_number}")
        else:
            st.error("Invalid Booking Number for payment confirmation.")

def customer_dashboard():
    # Check if the user is logged in
    if not st.session_state.get("logged_in"):
        st.error("You are not logged in!")
        return

    # Process any payment success notifications
    process_payment_query_params()

    username = st.session_state.get("username")
    st.subheader(f"Welcome, {username}! Place your order below.")

    # Display the menu
    menu = display_menu()
    st.header("Coffee Menu")
    st.table([[item, f"${price}"] for item, price in menu.items()])

    # Order form
    st.header("Order Your Coffee")
    coffee_type = st.selectbox("Select Coffee Type", list(menu.keys()))
    size = st.selectbox("Select Size", ["Small", "Medium", "Large"])
    addons = st.multiselect("Select Add-ons", ["Extra Sugar", "Extra Milk", "Whipped Cream"])
    quantity = st.number_input("Quantity", min_value=1, step=1)

    # Calculate price
    price_per_item = menu[coffee_type]
    if size == "Medium":
        price_per_item += 1.0
    elif size == "Large":
        price_per_item += 2.0
    price_per_item += 0.5 * len(addons)
    total_price = price_per_item * quantity

    # Apply Coupon Code
    st.subheader("Apply Coupon Code (Optional)")
    coupon_code = st.text_input("Enter Coupon Code")
    discount = None  # Initialize discount
    discount_percent = 0

    if st.button("Apply Coupon"):
        if coupon_code:
            discount = validate_coupon(coupon_code)
            if discount:
                discount_percent = discount[0]
                st.success(f"Coupon Applied! {discount_percent}% discount will be applied.")
            else:
                st.error("Invalid or expired coupon code.")
        else:
            st.warning("Please enter a coupon code.")

    # Place order button
    if st.button("Place Order"):
        # Apply discount if available
        discount_amount = 0
        if discount:
            discount_amount = total_price * (discount_percent / 100)
            total_price -= discount_amount

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
        reduce_inventory({coffee_type: quantity})  # Reduce inventory

        st.success(f"Order placed successfully! Booking Number: {booking_number}")
        if discount_amount > 0:
            st.info(f"Discount Applied: ${discount_amount:.2f}")

        # Redirect to mock payment page
        mock_payment_url = process_mock_payment(booking_number)
        st.markdown(f"[Proceed to Payment]({mock_payment_url})", unsafe_allow_html=True)

    # Display Order History
    st.header("Order History")
    order_history = get_order_history(username)
    if order_history:
        st.table(order_history)
    else:
        st.info("No orders found.")

    # Feedback Section
    st.header("Leave Feedback")
    feedback_booking_number = st.text_input("Enter Booking Number")
    feedback_text = st.text_area("Leave your feedback here")
    feedback_rating = st.slider("Rate your experience (1 - Poor, 5 - Excellent)", 1, 5, step=1)

    if st.button("Submit Feedback"):
        if feedback_booking_number and feedback_text:
            success = save_feedback(feedback_booking_number, feedback_text, feedback_rating)
            if success:
                st.success("Thank you for your feedback!")
            else:
                st.error("Failed to save feedback. Please try again.")
        else:
            st.warning("Please fill in all required fields.")
