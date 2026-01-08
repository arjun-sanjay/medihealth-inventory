import base64
import mysql.connector
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="MEDIHEALTH", layout="wide")

# ---------------- CUSTOM CSS ---------------- #
st.markdown("""
<style>
.stApp { background-color:#0E1117; color:#FAFAFA; }
section[data-testid="stSidebar"] { background-color:#161B22; }
.stButton>button {
    background:linear-gradient(90deg,#4CAF50,#2E7D32);
    color:white;border-radius:10px;height:45px;border:none;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ---------------- #
USER_CREDENTIALS = {"admin": {"password": "admin123"}}

# ---------------- MYSQL ---------------- #
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Helloworld123",
    database="medicine_db"
)
cursor = conn.cursor()

# ---------------- LOGIN PAGE ---------------- #
def login():
    st.title("🔐 Login to MEDIHEALTH")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_CREDENTIALS and p == USER_CREDENTIALS[u]["password"]:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- SIDEBAR ---------------- #
menu = st.sidebar.radio(
    "📌 Navigation",
    [
        "🏠 Dashboard",
        "➕ Add Medicine",
        "📦 View Inventory",
        "🛒 Customer Purchase",
        "🧾 Sales Report",
        "⚠ Expiry Alerts",
        "📈 Demand Prediction"
    ]
)

# ---------------- DASHBOARD ---------------- #
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard")

    cursor.execute("SELECT COUNT(*) FROM medicines")
    st.metric("💊 Medicines", cursor.fetchone()[0])

    cursor.execute("SELECT SUM(quantity) FROM medicines")
    st.metric("📦 Total Stock", cursor.fetchone()[0] or 0)

# ---------------- ADD MEDICINE ---------------- #
elif menu == "➕ Add Medicine":
    st.subheader("➕ Add Medicine")
    name = st.text_input("Medicine Name")
    cat = st.text_input("Category")
    qty = st.number_input("Quantity", min_value=1)
    exp = st.date_input("Expiry Date")
    price = st.number_input("Selling Price", min_value=0.0)

    if st.button("Add"):
        cursor.execute(
            "INSERT INTO medicines VALUES (NULL,%s,%s,%s,%s,%s)",
            (name, cat, qty, exp, price)
        )
        conn.commit()
        st.success("Medicine added")

# ---------------- VIEW INVENTORY ---------------- #
elif menu == "📦 View Inventory":
    cursor.execute("SELECT * FROM medicines")
    df = pd.DataFrame(cursor.fetchall(), columns=[c[0] for c in cursor.description])
    st.dataframe(df, use_container_width=True)

# ---------------- CUSTOMER PURCHASE ---------------- #
elif menu == "🛒 Customer Purchase":
    st.subheader("🛒 Medicine Purchase")

    cursor.execute("SELECT id,name,selling_price,quantity FROM medicines")
    meds = cursor.fetchall()

    med_map = {m[1]: m for m in meds}
    med_name = st.selectbox("Select Medicine", med_map.keys())

    customer = st.text_input("Customer Name")
    qty = st.number_input("Quantity", min_value=1)

    med = med_map[med_name]
    med_id, _, price, stock = med

    total = qty * price
    st.info(f"💰 Total Amount: ₹ {total}")

    if st.button("Generate Bill"):
        if qty > stock:
            st.error("Not enough stock")
        else:
            cursor.execute(
                "INSERT INTO customer_sales VALUES (NULL,%s,%s,%s,%s,%s)",
                (med_id, customer, qty, total, date.today())
            )
            cursor.execute(
                "UPDATE medicines SET quantity=quantity-%s WHERE id=%s",
                (qty, med_id)
            )
            conn.commit()

            st.success("🧾 Purchase Successful")
            st.markdown(f"""
            ### 🧾 BILL
            **Customer:** {customer}  
            **Medicine:** {med_name}  
            **Quantity:** {qty}  
            **Total:** ₹ {total}
            """)

# ---------------- SALES REPORT ---------------- #
elif menu == "🧾 Sales Report":
    st.subheader("🧾 Customer Sales")
    cursor.execute("""
        SELECT c.id,m.name,c.customer_name,c.quantity,
               c.total_amount,c.sale_date
        FROM customer_sales c
        JOIN medicines m ON c.medicine_id=m.id
    """)
    df = pd.DataFrame(cursor.fetchall(),
        columns=["ID","Medicine","Customer","Qty","Amount","Date"])
    st.dataframe(df, use_container_width=True)

# ---------------- EXPIRY ALERT ---------------- #
elif menu == "⚠ Expiry Alerts":
    cursor.execute("SELECT * FROM medicines")
    df = pd.DataFrame(cursor.fetchall(), columns=[c[0] for c in cursor.description])
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])
    st.dataframe(df[df["expiry_date"] < pd.to_datetime(date.today())])

# ---------------- DEMAND PREDICTION ---------------- #
elif menu == "📈 Demand Prediction":
    cursor.execute("""
        SELECT m.name,c.quantity,c.sale_date
        FROM customer_sales c
        JOIN medicines m ON c.medicine_id=m.id
    """)
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Medicine","Qty","Date"])
        df["Date"] = pd.to_datetime(df["Date"])
        med = st.selectbox("Medicine", df["Medicine"].unique())
        d = df[df["Medicine"] == med]
        pred = int(d["Qty"].mean() * 30)
        st.metric("📦 Predicted Monthly Demand", pred)
