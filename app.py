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
USER = "arjun"
PASS = "asdzxcqwe"

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
     "Sell Medicine", "Delete Medicine",
     "Sales Report", "Summary View"]
)

# ================= DASHBOARD ================= #
if menu == "Dashboard":
    st.title("📊 Dashboard")

    cursor.execute("SELECT COUNT(*) FROM medicines")
    total_meds = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity) FROM medicines")
    total_stock = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total_amount) FROM customer_sales")
    total_sales = cursor.fetchone()[0] or 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Medicines", total_meds)
    col2.metric("Total Stock", total_stock)
    col3.metric("Total Sales (₹)", total_sales)

    # 🗑 Delete Expired Medicines Button
    if st.button("🗑 Delete All Expired Medicines"):
        cursor.execute(
            "DELETE FROM medicines WHERE expiry_date < %s",
            (date.today(),)
        )
        conn.commit()
        st.success("Expired medicines deleted successfully!")


# ================= ADD MEDICINE ================= #
elif menu == "Add Medicine":
    st.header("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    cat = st.text_input("Category")
    qty = st.number_input("Quantity", min_value=1)
    exp = st.date_input("Expiry Date")
    price = st.number_input("Selling Price", min_value=1.0)

    if st.button("Add Medicine"):
        cursor.execute("SELECT quantity FROM medicines WHERE name=%s", (name,))
        existing = cursor.fetchone()

        if existing:
            new_qty = existing[0] + qty
            cursor.execute(
                "UPDATE medicines SET quantity=%s WHERE name=%s",
                (new_qty, name)
            )
        else:
            cursor.execute(
                """INSERT INTO medicines
                (name,category,quantity,expiry_date,selling_price)
                VALUES(%s,%s,%s,%s,%s)""",
                (name, cat, qty, exp, price)
            )

        conn.commit()
        st.success("Medicine Saved Successfully!")


# ================= INVENTORY ================= #
elif menu == "Inventory":
    st.header("📦 Inventory")

    cursor.execute("SELECT * FROM medicines")
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(
            data,
            columns=["ID", "Name", "Category", "Quantity", "Expiry", "Price"]
        )
        st.dataframe(df, use_container_width=True)

        # Low stock
        low = df[df["Quantity"] <= 10]
        if not low.empty:
            st.warning("Low stock medicines")
            st.dataframe(low)

        # Expiry
        df["Expiry"] = pd.to_datetime(df["Expiry"])
        expired = df[df["Expiry"] < pd.to_datetime(date.today())]
        if not expired.empty:
            st.error("Expired medicines")
            st.dataframe(expired)
    else:
        st.info("No data")


# ================= SELL ================= #
elif menu == "Sell Medicine":
    st.header("🛒 Sell Medicine")

    cursor.execute("SELECT id,name FROM medicines")
    meds = cursor.fetchall()

    if meds:
        med_dict = {m[1]: m[0] for m in meds}

        med = st.selectbox("Medicine", list(med_dict.keys()))
        customer = st.text_input("Customer")
        qty = st.number_input("Quantity", min_value=1)

        if st.button("Confirm Sale"):
            cursor.execute(
                "SELECT quantity, selling_price FROM medicines WHERE id=%s",
                (med_dict[med],)
            )
            stock, price = cursor.fetchone()

            if qty > stock:
                st.error("Not enough stock")
            else:
                total = qty * price

                cursor.execute(
                    """INSERT INTO customer_sales
                    (medicine_id,customer_name,quantity,total_amount,sale_date)
                    VALUES(%s,%s,%s,%s,%s)""",
                    (med_dict[med], customer, qty, total, date.today())
                )

                cursor.execute(
                    "UPDATE medicines SET quantity=%s WHERE id=%s",
                    (stock - qty, med_dict[med])
                )

                conn.commit()
                st.success("Sale completed")
    else:
        st.warning("No medicines")


# ================= DELETE ================= #
elif menu == "Delete Medicine":
    st.header("🗑 Delete Medicine")

    cursor.execute("SELECT id,name FROM medicines")
    meds = cursor.fetchall()

    if meds:
        med_dict = {m[1]: m[0] for m in meds}
        med = st.selectbox("Select", list(med_dict.keys()))

        if st.button("Delete"):
            cursor.execute(
                "DELETE FROM medicines WHERE id=%s",
                (med_dict[med],)
            )
            conn.commit()
            st.success("Deleted successfully!")
    else:
        st.warning("No medicines")


# ================= REPORT ================= #
elif menu == "Sales Report":
    st.header("Sales Report")

    cursor.execute("""
        SELECT c.id, m.name, c.customer_name,
               c.quantity, c.total_amount, c.sale_date
        FROM customer_sales c
        JOIN medicines m ON c.medicine_id = m.id
    """)

    df = pd.DataFrame(cursor.fetchall(),
                      columns=["ID","Medicine","Customer","Qty","Amount","Date"])
    st.dataframe(df)


# ================= SUMMARY ================= #
elif menu == "Summary View":
    st.header("Summary")

    cursor.execute("SELECT * FROM sales_summary")
    df = pd.DataFrame(cursor.fetchall(),
                      columns=["Medicine","Sold","Revenue"])
    st.dataframe(df)
