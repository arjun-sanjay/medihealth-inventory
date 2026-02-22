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


# ================= ADD MEDICINE ================= #
elif menu == "Add Medicine":
    st.header("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    cat = st.text_input("Category")
    qty = st.number_input("Quantity", min_value=1)
    exp = st.date_input("Expiry Date")
    price = st.number_input("Selling Price", min_value=1.0)

    if st.button("Add Medicine"):
        if name.strip() == "":
            st.warning("Medicine name cannot be empty!")
        else:
            cursor.execute("SELECT quantity FROM medicines WHERE name=%s", (name,))
            existing = cursor.fetchone()

            if existing:
                new_qty = existing[0] + qty
                cursor.execute(
                    "UPDATE medicines SET quantity=%s WHERE name=%s",
                    (new_qty, name)
                )
                conn.commit()
                st.success("Medicine already existed. Quantity Updated!")
            else:
                cursor.execute(
                    """INSERT INTO medicines
                    (name,category,quantity,expiry_date,selling_price)
                    VALUES(%s,%s,%s,%s,%s)""",
                    (name, cat, qty, exp, price)
                )
                conn.commit()
                st.success("Medicine Added Successfully!")


# ================= INVENTORY ================= #
elif menu == "Inventory":
    st.header("📦 Inventory")

    cursor.execute("SELECT * FROM medicines")
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(
            data,
            columns=["ID", "Name", "Category", "Quantity", "Expiry Date", "Price"]
        )
        st.dataframe(df, use_container_width=True)

        # 🔔 Low Stock Alert
        low_stock = df[df["Quantity"] <= 10]
        if not low_stock.empty:
            st.warning("⚠ Low Stock Medicines (Quantity ≤ 10)")
            st.dataframe(low_stock, use_container_width=True)

        # ⏰ Expiry Warning
        today = pd.to_datetime(date.today())
        df["Expiry Date"] = pd.to_datetime(df["Expiry Date"])

        expired = df[df["Expiry Date"] < today]
        expiring_soon = df[
            (df["Expiry Date"] >= today) &
            (df["Expiry Date"] <= today + pd.Timedelta(days=30))
        ]

        if not expired.empty:
            st.error("❌ Expired Medicines")
            st.dataframe(expired, use_container_width=True)

        if not expiring_soon.empty:
            st.warning("⏰ Expiring Within 30 Days")
            st.dataframe(expiring_soon, use_container_width=True)
    else:
        st.info("No medicines in inventory.")


# ================= SELL MEDICINE ================= #
elif menu == "Sell Medicine":
    st.header("🛒 Sell Medicine")

    cursor.execute("SELECT id,name FROM medicines")
    meds = cursor.fetchall()

    if not meds:
        st.warning("No medicines available!")
    else:
        med_dict = {m[1]: m[0] for m in meds}

        med = st.selectbox("Select Medicine", list(med_dict.keys()))
        customer = st.text_input("Customer Name")
        qty = st.number_input("Quantity", min_value=1)

        if st.button("Confirm Sale"):
            cursor.execute(
                "SELECT quantity, selling_price FROM medicines WHERE id=%s",
                (med_dict[med],)
            )
            result = cursor.fetchone()

            if result:
                current_qty, price = result

                if qty > current_qty:
                    st.error("Not enough stock available!")
                else:
                    total = qty * price

                    cursor.execute(
                        """INSERT INTO customer_sales
                        (medicine_id,customer_name,quantity,total_amount,sale_date)
                        VALUES(%s,%s,%s,%s,%s)""",
                        (med_dict[med], customer, qty, total, date.today())
                    )

                    new_stock = current_qty - qty
                    cursor.execute(
                        "UPDATE medicines SET quantity=%s WHERE id=%s",
                        (new_stock, med_dict[med])
                    )

                    conn.commit()
                    st.success("Sale Completed Successfully!")


# ================= DELETE MEDICINE ================= #
elif menu == "Delete Medicine":
    st.header("🗑 Delete Medicine")

    cursor.execute("SELECT id,name FROM medicines")
    meds = cursor.fetchall()

    if not meds:
        st.warning("No medicines available to delete.")
    else:
        med_dict = {m[1]: m[0] for m in meds}

        med_to_delete = st.selectbox(
            "Select Medicine to Delete",
            list(med_dict.keys())
        )

        if st.button("Delete Medicine"):
            cursor.execute(
                "DELETE FROM medicines WHERE id=%s",
                (med_dict[med_to_delete],)
            )
            conn.commit()
            st.success("Medicine Deleted Successfully!")


# ================= SALES REPORT ================= #
elif menu == "Sales Report":
    st.header("🧾 Sales Report")

    cursor.execute("""
        SELECT c.id, m.name, c.customer_name,
               c.quantity, c.total_amount, c.sale_date
        FROM customer_sales c
        JOIN medicines m ON c.medicine_id = m.id
        ORDER BY c.sale_date DESC
    """)

    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(
            data,
            columns=["ID", "Medicine", "Customer",
                     "Quantity", "Amount", "Date"]
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No sales recorded.")


# ================= SUMMARY VIEW ================= #
elif menu == "Summary View":
    st.header("📊 Sales Summary (VIEW)")

    cursor.execute("SELECT * FROM sales_summary")
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(
            data,
            columns=["Medicine", "Total Sold", "Revenue"]
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No summary data available.")
