import streamlit as st
import pandas as pd
import os

# 1. Page Configuration
st.set_page_config(page_title="Pharmacy Pro Portal", page_icon="🏥", layout="wide")

FILE_PATH = 'inventory.csv'
USERS_FILE = 'users.csv'

# 2. Database Safety Functions (Automatically creates files if missing to prevent FileNotFoundError)
def load_data():
    if not os.path.exists(FILE_PATH):
        pd.DataFrame(columns=["medicine_name", "category", "stock", "price", "expiry_date"]).to_csv(FILE_PATH, index=False)
    return pd.read_csv(FILE_PATH)

def save_data(df): 
    df.to_csv(FILE_PATH, index=False)

def load_users():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["username", "password", "role"]).to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def save_users(df): 
    df.to_csv(USERS_FILE, index=False)

# 3. Session State Initialize karna login session track karne ke liye
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# ================= AUTHENTICATION WELCOME SCREEN =================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://images.unsplash.com/photo-1586015555751-63bb77f4322a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="Secure Pharmacy Portal")
        st.title("🏥 Pharmacy Gateway")
        
        # UI Tabs for Login and Self Registration
        login_tab, register_tab = st.tabs(["🔐 Sign In", "📝 Self Registration"])
        
        # --- TAB A: LOGIN LOGIC ---
        with login_tab:
            st.subheader("Login to Your Account")
            with st.form("login_form"):
                user_input = st.text_input("Username", key="login_uid")
                pass_input = st.text_input("Password", type="password", key="login_pwd")
                submit_login = st.form_submit_button("Sign In")
                
                if submit_login:
                    users_df = load_users()
                    # Matching credentials in database
                    user_record = users_df[(users_df['username'] == user_input) & (users_df['password'] == pass_input)]
                    
                    if not user_record.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user_input
                        st.session_state['role'] = user_record.iloc[0]['role']
                        st.success("Access Granted!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password!")
        
        # --- TAB B: SELF REGISTRATION LOGIC ---
        with register_tab:
            st.subheader("Create a New Account")
            with st.form("registration_form"):
                reg_user = st.text_input("Choose Username (Unique)")
                reg_pass = st.text_input("Set Password", type="password")
                reg_confirm = st.text_input("Confirm Password", type="password")
                reg_role = st.selectbox("Select Access Role", ["Employee", "Admin"])
                submit_reg = st.form_submit_button("Register Account")
                
                if submit_reg:
                    users_df = load_users()
                    if reg_user == "" or reg_pass == "":
                        st.warning("Fields cannot be empty!")
                    elif reg_pass != reg_confirm:
                        st.error("❌ Password and Confirm Password do not match!")
                    elif reg_user in users_df['username'].values:
                        st.error("❌ This username is already taken! Try another one.")
                    else:
                        # Appending new registration entry to users database
                        new_user_data = pd.DataFrame({"username": [reg_user], "password": [reg_pass], "role": [reg_role]})
                        users_df = pd.concat([users_df, new_user_data], ignore_index=True)
                        save_users(users_df)
                        st.success(f"🎉 Account created successfully for '{reg_user}' as {reg_role}! Please switch to the 'Sign In' tab to log in.")

# ================= CORE APPLICATION (AFTER LOGIN) =================
else:
    df = load_data()
    
    # Navigation Dashboard Setup
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.sidebar.write(f"**Session User:** {st.session_state['username']}")
    st.sidebar.write(f"**Access Rights:** {st.session_state['role']}")
    
    if st.sidebar.button("🚪 Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['role'] = ""
        st.rerun()
        
    st.sidebar.divider()
    
    # Conditional Navigation Menu (Role-Based Access Control)
    if st.session_state['role'] == "Admin":
        menu = st.sidebar.radio("Navigation Menu", ["📊 Dashboard & Stock", "➕ Add New Medicine", "🛒 Sell Medicine Counter"])
    else:
        # Employees cannot see the "Add New Medicine" section
        menu = st.sidebar.radio("Navigation Menu", ["📊 Dashboard & Stock", "🛒 Sell Medicine Counter"])

    # --- SECTION 1: DASHBOARD ---
    if menu == "📊 Dashboard & Stock":
        st.title("📊 Pharmacy Analytics Dashboard")
        st.image("https://images.unsplash.com/photo-1555252333-9f8e92e65df9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Current Real-Time Stock")
            st.dataframe(df, use_container_width=True)
        with col2:
            st.subheader("⚠️ Critical Low Stock Alerts")
            low_stock_df = df[df['stock'] < 20]
            if not low_stock_df.empty:
                st.error("The following inventory items require immediate re-stocking:")
                st.dataframe(low_stock_df, use_container_width=True)
            else:
                st.success("All medical inventories are structurally stable.")

    # --- SECTION 2: ADD MEDICINE (Admin Privilege Only) ---
    elif menu == "➕ Add New Medicine":
        st.title("➕ Add New Medical Resource")
        st.image("https://images.unsplash.com/photo-1471864190281-a93a3070b6de?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
        
        with st.form("add_medicine_form"):
            med_name = st.text_input("Medicine Name & Dosage Power")
            category = st.selectbox("Form Factor / Category", ["Tablet", "Syrup", "Capsule", "Ointment", "Injection"])
            stock_qty = st.number_input("Inward Batch Stock Quantity", min_value=1, value=100)
            price_unit = st.number_input("Unit Retail Price (₹)", min_value=0.5, value=10.0, step=0.5)
            expiry = st.date_input("Batch Expiry Date")
            
            if st.form_submit_button("Commit to Database"):
                if med_name:
                    new_row = pd.DataFrame({"medicine_name": [med_name], "category": [category], "stock": [stock_qty], "price": [price_unit], "expiry_date": [expiry]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ Securely added batch for '{med_name}' to central inventory.")
                else:
                    st.warning("Validation Error: Medicine Name is required.")

    # --- SECTION 3: SELL MEDICINE (Point of Sale Counter) ---
    elif menu == "🛒 Sell Medicine Counter":
        st.title("🛒 Pharmacy Point of Sale (POS)")
        st.image("https://images.unsplash.com/photo-1576602976047-174e57a47881?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
        
        med_list = df['medicine_name'].tolist()
        if not med_list:
            st.info("Inventory Empty: Please log in as Admin to seed initial database items.")
        else:
            selected_med = st.selectbox("Select Outward Medicine Item", med_list)
            sell_qty = st.number_input("Dispensation Quantity", min_value=1, value=1)
            
            if st.button("Process Dispatch & Print Bill"):
                current_stock = df.loc[df['medicine_name'] == selected_med, 'stock'].values[0]
                price = df.loc[df['medicine_name'] == selected_med, 'price'].values[0]
                
                if sell_qty > current_stock:
                    st.error(f"❌ Allocation Fault: Requested {sell_qty} units, but only {current_stock} units exist.")
                else:
                    # Update stock via mutation
                    df.loc[df['medicine_name'] == selected_med, 'stock'] -= sell_qty
                    save_data(df)
                    total_bill = sell_qty * price
                    st.success(f"📊 Dispatch Confirmed! Total Transaction Value: ₹{total_bill:.2f}")
                    st.balloons()
