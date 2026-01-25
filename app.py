import mysql.connector
import pandas as pd
import streamlit as st
from datetime import date

st.set_page_config(page_title="MEDIHEALTH", layout="wide")

# ---------------- MYSQL CONNECTION ---------------- #
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Helloworld123",
    database="medihealth_db"
)
cursor = conn.cursor()

# ---------------- LOGIN ---------------- #
USER = "admin"
PASS = "admin123"

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 MEDIHEALTH Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == USER and p == PASS:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------------- SIDEBAR ---------------- #
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Medicine", "Inventory",
     "Sell Medicine", "Sales Report", "Summary View"]
)

# ---------------- DASHBOARD ---------------- #
if menu == "Dashboard":
    st.title("📊 Dashboard")

    cursor.execute("SELECT COUNT(*) FROM medicines")
    st.metric("Total Medicines", cursor.fetchone()[0])

    cursor.execute("SELECT SUM(quantity) FROM medicines")
    st.metric("Total Stock", cursor.fetchone()[0] or 0)

    cursor.execute("SELECT SUM(total_amount) FROM customer_sales")
    st.metric("Total Sales (₹)", cursor.fetchone()[0] or 0)

# ---------------- ADD MEDICINE ---------------- #
elif menu == "Add Medicine":
    st.header("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    cat = st.text_input("Category")
    qty = st.number_input("Quantity", min_value=1)
    exp = st.date_input("Expiry Date")
    price = st.number_input("Selling Price", min_value=1.0)

    if st.button("Add Medicine"):
        cursor.execute(
            "INSERT INTO medicines(name,category,quantity,expiry_date,selling_price) VALUES(%s,%s,%s,%s,%s)",
            (name, cat, qty, exp, price)
        )
        conn.commit()
        st.success("Medicine Added")

# ---------------- INVENTORY ---------------- #
elif menu == "Inventory":
    st.header("📦 Inventory")
    cursor.execute("SELECT * FROM medicines")
    df = pd.DataFrame(cursor.fetchall(),
        columns=["ID","Name","Category","Qty","Expiry","Price"])
    st.dataframe(df, use_container_width=True)

# ---------------- SELL MEDICINE ---------------- #
elif menu == "Sell Medicine":
    st.header("🛒 Sell Medicine")

    cursor.execute("SELECT id,name FROM medicines")
    meds = cursor.fetchall()
    med_dict = {m[1]: m[0] for m in meds}

    med = st.selectbox("Medicine", med_dict.keys())
    customer = st.text_input("Customer Name")
    qty = st.number_input("Quantity", min_value=1)

    if st.button("Confirm Sale"):
        cursor.execute(
            "INSERT INTO customer_sales(medicine_id,customer_name,quantity,sale_date) VALUES(%s,%s,%s,%s)",
            (med_dict[med], customer, qty, date.today())
        )
        conn.commit()
        st.success("Sale Completed")

# ---------------- SALES REPORT (JOIN) ---------------- #
elif menu == "Sales Report":
    st.header("🧾 Sales Report")
    cursor.execute("""
        SELECT c.id,m.name,c.customer_name,c.quantity,c.total_amount,c.sale_date
        FROM customer_sales c
        JOIN medicines m ON c.medicine_id = m.id
    """)
    df = pd.DataFrame(cursor.fetchall(),
        columns=["ID","Medicine","Customer","Qty","Amount","Date"])
    st.dataframe(df, use_container_width=True)

# ---------------- VIEW ---------------- #
elif menu == "Summary View":
    st.header("📊 Sales Summary (VIEW)")
    cursor.execute("SELECT * FROM sales_summary")
    df = pd.DataFrame(cursor.fetchall(),
        columns=["Medicine","Total Sold","Revenue"])
    st.dataframe(df, use_container_width=True)
