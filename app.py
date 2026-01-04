import base64
import mysql.connector
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date, timedelta

# ---------------- LOGIN CREDENTIALS ---------------- #
USER_CREDENTIALS = {
    "admin": {"password": "admin123"},
}

# ---------------- MYSQL CONNECTION ---------------- #
conn = mysql.connector.connect(
    host="localhost",
    user="root",         
    password="Helloworld123",  
    database="medicine_db"
)
cursor = conn.cursor()

# ---------------- LOGIN PAGE ---------------- #
def login():
    st.set_page_config(page_title="Login", layout="centered")

    st.markdown(
        """
        <div style='text-align:center;'>
            <img src='data:image/png;base64,{}' width='300'/>
        </div>
        """.format(base64.b64encode(open("logo.png", "rb").read()).decode()),
        unsafe_allow_html=True
    )

    st.markdown("<h1 style='text-align:center;'>Login to MEDIHEALTH</h1>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USER_CREDENTIALS.get(username)
        if user and password == user["password"]:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid credentials")

# ---------------- SESSION ---------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- SIDEBAR ---------------- #
st.sidebar.image("logo.png", width=220)
st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
st.sidebar.markdown("<h1 style='color:skyblue;'>MEDIHEALTH</h1>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "Navigation",
    ["Add Medicine", "View Inventory", "Log Usage", "Expiry Alerts", "Demand Prediction"]
)

# ---------------- ADD MEDICINE ---------------- #
if menu == "Add Medicine":
    st.subheader("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=1)
    expiry = st.date_input("Expiry Date")

    if st.button("Add Medicine"):
        cursor.execute(
            "INSERT INTO medicines (name, category, quantity, expiry_date) VALUES (%s, %s, %s, %s)",
            (name, category, quantity, expiry)
        )
        conn.commit()
        st.success("Medicine added successfully")

# ---------------- VIEW INVENTORY ---------------- #
elif menu == "View Inventory":
    st.subheader("📦 Inventory")

    cursor.execute("SELECT * FROM medicines")
    data = cursor.fetchall()
    cols = [c[0] for c in cursor.description]
    df = pd.DataFrame(data, columns=cols)

    st.dataframe(df, use_container_width=True)

# ---------------- LOG USAGE ---------------- #
elif menu == "Log Usage":
    st.subheader("📝 Log Medicine Usage")

    cursor.execute("SELECT id, name FROM medicines")
    meds = cursor.fetchall()

    if not meds:
        st.warning("No medicines found")
    else:
        med_names = {name: mid for mid, name in meds}

        selected_med = st.selectbox("Select Medicine", med_names.keys())
        used_qty = st.number_input("Used Quantity", min_value=1)
        usage_date = st.date_input("Usage Date", date.today())

        if st.button("Log Usage"):
            med_id = med_names[selected_med]

            cursor.execute(
                "INSERT INTO usage_logs (medicine_id, used_qty, usage_date) VALUES (%s, %s, %s)",
                (med_id, used_qty, usage_date)
            )

            cursor.execute(
                "UPDATE medicines SET quantity = quantity - %s WHERE id = %s",
                (used_qty, med_id)
            )

            conn.commit()
            st.success("Usage logged successfully")

# ---------------- EXPIRY ALERTS ---------------- #
elif menu == "Expiry Alerts":
    st.subheader("⚠ Expiry Alerts")

    today = date.today()
    alert_date = today + timedelta(days=30)

    cursor.execute("SELECT * FROM medicines")
    data = cursor.fetchall()
    cols = [c[0] for c in cursor.description]
    df = pd.DataFrame(data, columns=cols)
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])

    expired = df[df["expiry_date"] < pd.to_datetime(today)]
    near_expiry = df[(df["expiry_date"] >= pd.to_datetime(today)) &
                     (df["expiry_date"] <= pd.to_datetime(alert_date))]

    st.markdown("### ❌ Expired Medicines")
    st.dataframe(expired, use_container_width=True)

    st.markdown("### ⚠ Near Expiry (30 Days)")
    st.dataframe(near_expiry, use_container_width=True)

# ---------------- DEMAND PREDICTION ---------------- #
elif menu == "Demand Prediction":
    st.subheader("📈 Demand Prediction")

    cursor.execute("""
        SELECT m.name, u.used_qty, u.usage_date
        FROM usage_logs u
        JOIN medicines m ON u.medicine_id = m.id
    """)
    data = cursor.fetchall()

    if not data:
        st.warning("No usage data available")
    else:
        df = pd.DataFrame(data, columns=["name", "used_qty", "usage_date"])
        df["usage_date"] = pd.to_datetime(df["usage_date"])

        selected_med = st.selectbox("Select Medicine", df["name"].unique())
        med_df = df[df["name"] == selected_med]

        daily_usage = med_df.groupby("usage_date")["used_qty"].sum().reset_index()

        avg_daily = daily_usage["used_qty"].mean()
        predicted_monthly = int(avg_daily * 30)

        st.metric("📦 Predicted Monthly Demand", predicted_monthly)

        fig, ax = plt.subplots()
        ax.plot(daily_usage["usage_date"], daily_usage["used_qty"])
        ax.set_title("Daily Usage Trend")
        ax.set_xlabel("Date")
        ax.set_ylabel("Quantity Used")
        st.pyplot(fig)
