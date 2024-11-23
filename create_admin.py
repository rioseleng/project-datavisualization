from database import add_user, create_user_table

# Ensure the users table is created before adding an admin user
create_user_table()

# Manually create an admin account
if __name__ == "__main__":
    username = "admin"
    password = "adminpassword"
    is_admin = 1  # Set is_admin to 1 for admin accounts
    success = add_user(username, password, is_admin)

    if success:
        print(f"Admin account '{username}' created successfully!")
    else:
        print(f"Failed to create admin account. Username '{username}' may already exist.")
