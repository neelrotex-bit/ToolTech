import streamlit as st

# =========================================================
# SAFE MT5 IMPORT (CRITICAL)
# =========================================================
try:
    import MT5Manager
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


# =========================================================
# STREAMLIT CLOUD SAFE MODE
# =========================================================
if not MT5_AVAILABLE:
    st.set_page_config(page_title="MT5 Admin Tool", page_icon="⚠️")
    st.title("MT5 Admin Tool")

    st.error("MT5 Manager API is not available on this platform.")

    st.info(
        "This application requires:\n"
        "- Windows OS\n"
        "- MetaTrader 5 Manager SDK\n\n"
        "Streamlit Cloud does NOT support MT5 Manager.\n\n"
        "To use MT5 features, run this app on:\n"
        "• Local Windows machine\n"
        "• Windows VPS\n"
        "• Or via FastAPI backend on Windows"
    )

    st.stop()


# =========================================================
# MAIN MT5 APPLICATION (WINDOWS ONLY)
# =========================================================
st.set_page_config(page_title="MT5 Admin Tool", page_icon="📊")
st.title("MT5 Admin Tool")

# ---------------------------------------------------------
# Connection UI
# ---------------------------------------------------------
server_ip = st.text_input("Server IP", "")
manager_login = st.number_input("Manager Login", min_value=1, step=1)
manager_password = st.text_input("Manager Password", type="password")

if st.button("Connect"):
    manager = MT5Manager.ManagerAPI()

    connected = manager.Connect(
        server_ip,
        int(manager_login),
        manager_password,
        MT5Manager.ManagerAPI.EnPumpModes.PUMP_MODE_USERS,
        30000
    )

    if connected:
        st.session_state["manager"] = manager
        st.success("Connected successfully!")
    else:
        st.error(f"Failed to connect: {MT5Manager.LastError()}")

# ---------------------------------------------------------
# User Operations
# ---------------------------------------------------------
if "manager" in st.session_state:
    manager = st.session_state["manager"]

    st.divider()
    st.subheader("User Management")

    user_login = st.number_input("User Login", min_value=1, step=1)

    # Toggle Trading Rights
    if st.button("Toggle Trading Rights"):
        user = manager.UserGet(int(user_login))
        if user:
            user.Rights ^= MT5Manager.MTUser.EnUsersRights.USER_RIGHT_ENABLED
            if manager.UserUpdate(user):
                st.success("Trading rights updated!")
            else:
                st.error(f"Failed: {MT5Manager.LastError()}")
        else:
            st.warning("User not found.")

    st.divider()

    # Balance Adjustment
    balance_amount = st.number_input("Balance Adjustment", value=0.0)
    comment = st.text_input("Comment for the operation", "Balance adjustment via UI")

    if st.button("Adjust Balance"):
        deal_id = manager.DealerBalance(
            int(user_login),
            float(balance_amount),
            MT5Manager.MTDeal.EnDealAction.DEAL_BALANCE,
            comment
        )
        if deal_id:
            st.success(f"Balance adjusted! Deal ID: {deal_id}")
        else:
            st.error(f"Failed: {MT5Manager.LastError()}")

    st.divider()

    # Leverage Update
    leverage = st.number_input("Set Leverage", min_value=1, step=1)

    if st.button("Update Leverage"):
        user = manager.UserGet(int(user_login))
        if user:
            user.Leverage = int(leverage)
            if manager.UserUpdate(user):
                st.success(f"Leverage updated to {leverage}!")
            else:
                st.error(f"Failed: {MT5Manager.LastError()}")
        else:
            st.warning("User not found.")
