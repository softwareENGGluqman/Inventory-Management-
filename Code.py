import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Pharmacy Inventory", page_icon="💊", layout="wide")

FILE_PATH = 'inventory.csv'

# Data Load aur Save karne ke functions
def load_data():
    return pd.read_csv(FILE_PATH)

def save_data(df):
    df.to_csv(FILE_PATH, index=False)

# Load current dataset
df = load_data()

# App Header
st.title("💊 Pharmacy Inventory Management System")
st.markdown("Manage your medicines, track stock levels, and update sales instantly.")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation Menu", ["📊 Dashboard & Stock", "➕ Add New Medicine", "🛒 Sell Medicine (Update Stock)"])

# ----------------- SECTION 1: DASHBOARD -----------------
if menu == "📊 Dashboard & Stock":
    st.subheader("📦 Current Inventory")
    # Dataframe ko table ke roop mein dikhana
    st.dataframe(df, use_container_width=True)
    
    st.divider()
    
    # Low Stock Alert Logic (Agar stock 20 se kam hai)
    st.subheader("⚠️ Low Stock Alerts")
    low_stock_df = df[df['stock'] < 20]
    
    if not low_stock_df.empty:
        st.error("Attention! The following medicines are running out of stock:")
        st.dataframe(low_stock_df, use_container_width=True)
    else:
        st.success("All medicines have sufficient stock.")

# ----------------- SECTION 2: ADD MEDICINE -----------------
elif menu == "➕ Add New Medicine":
    st.subheader("Enter New Medicine Details")
    
    with st.form("add_medicine_form"):
        med_name = st.text_input("Medicine Name & Power (e.g., Crocin 650mg)")
        category = st.selectbox("Category", ["Tablet", "Syrup", "Capsule", "Injection", "Ointment", "Drops"])
        stock_qty = st.number_input("Initial Stock Quantity", min_value=1, value=50)
        price_unit = st.number_input("Price per unit (₹)", min_value=1.0, value=10.0, step=0.5)
        expiry = st.date_input("Expiry Date")
        
        submit_btn = st.form_submit_button("Add to Inventory")
        
        if submit_btn:
            if med_name == "":
                st.warning("Please enter a medicine name.")
            else:
                # Naya data dataframe mein add karna aur CSV mein save karna
                new_row = pd.DataFrame({
                    "medicine_name": [med_name], 
                    "category": [category], 
                    "stock": [stock_qty], 
                    "price": [price_unit], 
                    "expiry_date": [expiry]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"✅ '{med_name}' has been successfully added to the inventory!")

# ----------------- SECTION 3: SELL MEDICINE -----------------
elif menu == "🛒 Sell Medicine (Update Stock)":
    st.subheader("Record a Sale")
    
    med_list = df['medicine_name'].tolist()
    selected_med = st.selectbox("Select Medicine to Sell", med_list)
    sell_qty = st.number_input("Quantity Sold", min_value=1, value=1, step=1)
    
    if st.button("Confirm Sale"):
        current_stock = df.loc[df['medicine_name'] == selected_med, 'stock'].values[0]
        
        if sell_qty > current_stock:
            st.error(f"❌ Transaction Failed: Not enough stock! Only {current_stock} units available.")
        else:
            # Stock minus karna aur update karna
            df.loc[df['medicine_name'] == selected_med, 'stock'] -= sell_qty
            save_data(df)
            st.success(f"✅ Sale successful! {sell_qty} units of '{selected_med}' sold. Stock updated.")

