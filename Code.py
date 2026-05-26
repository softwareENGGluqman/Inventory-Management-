import streamlit as st
import pandas as pd
import os

# 1. Page Config
st.set_page_config(page_title="Pharmacy Pro", page_icon="🏥", layout="wide")

FILE_PATH = 'inventory.csv'
USERS_FILE = 'users.csv'

# 2. Data Helper Functions
def load_data(): return pd.read_csv(FILE_PATH)
def save_data(df): df.to_csv(FILE_PATH, index=False)
def load_users(): return pd.read_csv(USERS_FILE)
def save_users(df): df.to_csv(USERS_FILE, index=False)

# 3. Session State Initialization (Login System ke liye)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# ================= LOGIN SECTION =================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://images.unsplash.com/photo-1586015555751-63bb77f4322a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="Secure Pharmacy Portal")
        st.title("🔐 Login Portal")
        
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                users_df = load_users()
                # Check credentials
                user_record = users_df[(users_df['username'] == user_input) & (users_df['password'] == pass_input)]
                
                if not user_record.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_input
                    st.session_state['role'] = user_record.iloc[0]['role']
                    st.rerun() # Page refresh karne ke liye
                else:
                    st.error("❌ Invalid Username or Password!")

# ================= MAIN APP SECTION =================
else:
    df = load_data()
    
    # Sidebar Profile & Navigation
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.sidebar.write(f"**User:** {st.session_state['username']}")
    st.sidebar.write(f"**Role:** {st.session_state['role']}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['role'] = ""
        st.rerun()
        
    st.sidebar.divider()
    
    # Role-Based Menu
    if st.session_state['role'] == "Admin":
        menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "➕ Add Medicine", "🛒 Sell Medicine", "👥 Register Employee"])
    else:
        menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🛒 Sell Medicine"])

    # --- TAB 1: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📊 Inventory Dashboard")
        st.image("https://images.unsplash.com/photo-1555252333-9f8e92e65df9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Current Stock")
            st.dataframe(df, use_container_width=True)
        with col2:
            st.subheader("⚠️ Low Stock Alerts (Below 20 units)")
            low_stock = df[df['stock'] < 20]
            if not low_stock.empty:
                st.error("Please re-stock these items!")
                st.dataframe(low_stock, use_container_width=True)
            else:
                st.success("All stock levels are optimal.")

    # --- TAB 2: ADD MEDICINE (Admin Only) ---
    elif menu == "➕ Add Medicine":
        st.title("➕ Add New Inventory")
        st.image("https://images.unsplash.com/photo-1471864190281-a93a3070b6de?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
        
        with st.form("add_med_form"):
            med_name = st.text_input("Medicine Name & Power")
            category = st.selectbox("Category", ["Tablet", "Syrup", "Injection", "Ointment"])
            stock_qty = st.number_input("Initial Stock", min_value=1, value=50)
            price_unit = st.number_input("Price (₹)", min_value=1.0, value=10.0)
            expiry = st.date_input("Expiry Date")
            
            if st.form_submit_button("Add to Database"):
                if med_name:
                    new_row = pd.DataFrame({"medicine_name": [med_name], "category": [category], "stock": [stock_qty], "price": [price_unit], "expiry_date": [expiry]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ {med_name} added successfully!")
                else:
                    st.warning("Name cannot be empty.")

    # --- TAB 3: SELL MEDICINE (Admin & Employee) ---
    elif menu == "🛒 Sell Medicine":
        st.title("🛒 POS Counter")
        st.image("https://images.unsplash.com/photo-1576602976047-174e57a47881?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
        
        med_list = df['medicine_name'].tolist()
        selected_med = st.selectbox("Select Medicine", med_list)
        sell_qty = st.number_input("Quantity", min_value=1, value=1)
        
        if st.button("Generate Bill & Sell"):
            current_stock = df.loc[df['medicine_name'] == selected_med, 'stock'].values[0]
            price = df.loc[df['medicine_name'] == selected_med, 'price'].values[0]
            
            if sell_qty > current_stock:
                st.error(f"❌ Only {current_stock} units left in stock!")
            else:
                df.loc[df['medicine_name'] == selected_med, 'stock'] -= sell_qty
                save_data(df)
                total_amount = sell_qty * price
                st.success(f"✅ Sale confirmed! Total Bill: ₹{total_amount}")
                st.balloons() # Thoda animation UI ke liye

    # --- TAB 4: REGISTER EMPLOYEE (Admin Only) ---
    elif menu == "👥 Register Employee":
        st.title("👥 Employee Management")
        st.info("Only Admins can register new staff members.")
        
        with st.form("register_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            role = st.selectbox("Assign Role", ["Employee", "Admin"])
            
            if st.form_submit_button("Create Account"):
                users_df = load_users()
                if new_user in users_df['username'].values:
                    st.error("Username already exists!")
                elif new_user and new_pass:
                    new_user_df = pd.DataFrame({"username": [new_user], "password": [new_pass], "role": [role]})
                    users_df = pd.concat([users_df, new_user_df], ignore_index=True)
                    save_users(users_df)
                    st.success(f"✅ Account created for {new_user} as {role}.")


