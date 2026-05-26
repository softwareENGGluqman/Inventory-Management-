import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
import base64

# 1. Page Configuration
st.set_page_config(page_title="Pharmacy Pro Portal", page_icon="🏥", layout="wide")

FILE_PATH = 'inventory.csv'
USERS_FILE = 'users.csv'

# 2. Database Safety & Persistence Functions
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

# PDF Bill Generator Function
def generate_pdf_bill(customer, med, qty, price, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Udgir Pharmacy & Care", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="---------------------------------------------------------", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Customer Name: {customer}", ln=True)
    pdf.cell(200, 10, txt=f"Medicine Dispensed: {med}", ln=True)
    pdf.cell(200, 10, txt=f"Quantity: {qty} units", ln=True)
    pdf.cell(200, 10, txt=f"Unit Price: Rs. {price}", ln=True)
    pdf.cell(200, 10, txt="---------------------------------------------------------", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Total Bill Amount: Rs. {total}", ln=True)
    pdf.output("invoice.pdf")
    return "invoice.pdf"

# 3. Session State Init
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# ================= AUTHENTICATION SCREEN =================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏥 Pharmacy Gateway")
        login_tab, register_tab = st.tabs(["🔐 Sign In", "📝 Register"])
        
        with login_tab:
            with st.form("login_form"):
                user_input = st.text_input("Username")
                pass_input = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In"):
                    users_df = load_users()
                    user_record = users_df[(users_df['username'] == user_input) & (users_df['password'] == pass_input)]
                    if not user_record.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user_input
                        st.session_state['role'] = user_record.iloc[0]['role']
                        st.rerun()
                    else:
                        st.error("❌ Invalid Credentials!")
        
        with register_tab:
            with st.form("registration_form"):
                reg_user = st.text_input("Choose Username")
                reg_pass = st.text_input("Set Password", type="password")
                reg_role = st.selectbox("Select Role", ["Employee", "Admin"])
                if st.form_submit_button("Register"):
                    users_df = load_users()
                    if reg_user in users_df['username'].values:
                        st.error("❌ Username taken!")
                    else:
                        new_user_data = pd.DataFrame({"username": [reg_user], "password": [reg_pass], "role": [reg_role]})
                        users_df = pd.concat([users_df, new_user_data], ignore_index=True)
                        save_users(users_df)
                        st.success("🎉 Registered! Go to Sign In.")

# ================= CORE APPLICATION =================
else:
    df = load_data()
    
    st.sidebar.title(f"👤 {st.session_state['username']}")
    st.sidebar.write(f"**Role:** {st.session_state['role']}")
    
    if st.sidebar.button("🚪 Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.sidebar.divider()
    
    if st.session_state['role'] == "Admin":
        menu = st.sidebar.radio("Menu", ["📈 Analytics Dashboard", "➕ Add Medicine", "🛒 POS Counter", "💾 Data Backup"])
    else:
        menu = st.sidebar.radio("Menu", ["🛒 POS Counter", "📈 Analytics Dashboard"])

    # --- TAB 1: ANALYTICS & VISUALIZATION ---
    if menu == "📈 Analytics Dashboard":
        st.title("📈 Inventory Analytics")
        st.write("Visual representation of current stock and categories.")
        
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Current Stock Levels")
                chart_data = df.set_index('medicine_name')['stock']
                st.bar_chart(chart_data)
            
            with col2:
                st.subheader("Medicines by Category")
                cat_data = df['category'].value_counts()
                st.line_chart(cat_data)
        else:
            st.info("Database is empty. Add medicines to see analytics.")

    # --- TAB 2: ADD MEDICINE ---
    elif menu == "➕ Add Medicine":
        st.title("➕ Inward Inventory")
        with st.form("add_medicine_form"):
            med_name = st.text_input("Medicine Name")
            category = st.selectbox("Category", ["Tablet", "Syrup", "Ointment", "Injection"])
            stock_qty = st.number_input("Stock Quantity", min_value=1, value=100)
            price_unit = st.number_input("Unit Price (₹)", min_value=1.0, value=10.0)
            expiry = st.date_input("Expiry Date")
            
            if st.form_submit_button("Save to Database"):
                if med_name:
                    new_row = pd.DataFrame({"medicine_name": [med_name], "category": [category], "stock": [stock_qty], "price": [price_unit], "expiry_date": [expiry]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ Added {med_name}!")
                else:
                    st.warning("Name required.")

    # --- TAB 3: SELL MEDICINE (PDF GENERATION) ---
    elif menu == "🛒 POS Counter":
        st.title("🛒 Generate Sale & Invoice")
        
        med_list = df['medicine_name'].tolist()
        if not med_list:
            st.warning("Inventory empty!")
        else:
            customer_name = st.text_input("Customer Name", value="Irfan Khan")
            selected_med = st.selectbox("Select Medicine", med_list)
            sell_qty = st.number_input("Quantity", min_value=1, value=1)
            
            if st.button("Generate Bill"):
                current_stock = df.loc[df['medicine_name'] == selected_med, 'stock'].values[0]
                price = df.loc[df['medicine_name'] == selected_med, 'price'].values[0]
                
                if sell_qty > current_stock:
                    st.error(f"❌ Not enough stock! Only {current_stock} left.")
                else:
                    df.loc[df['medicine_name'] == selected_med, 'stock'] -= sell_qty
                    save_data(df)
                    total = sell_qty * price
                    st.success(f"Sale complete! Total: ₹{total}")
                    
                    # Generate PDF
                    pdf_file = generate_pdf_bill(customer_name, selected_med, sell_qty, price, total)
                    with open(pdf_file, "rb") as f:
                        st.download_button("⬇️ Download PDF Invoice", f, file_name="invoice.pdf")

    # --- TAB 4: BACKUP & RESTORE (Admin Permanent Storage Solution) ---
    elif menu == "💾 Data Backup":
        st.title("💾 Database Management")
        st.info("Download your database before the server restarts, and upload it back to restore all data.")
        
        # Download Database
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="⬇️ Download Permanent Backup (CSV)", data=csv_data, file_name='inventory_backup.csv', mime='text/csv')
        
        st.divider()
        st.subheader("Restore Database")
        uploaded_file = st.file_uploader("Upload Backup CSV", type=["csv"])
        if uploaded_file is not None:
            restored_df = pd.read_csv(uploaded_file)
            save_data(restored_df)
            st.success("✅ Database Restored Successfully! Refreshing...")
            st.rerun()
