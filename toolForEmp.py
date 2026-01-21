import streamlit as st
import MT5Manager

# UI for connection
server_ip = st.text_input("Server IP", "188.240.63.181:443")
manager_login = st.number_input("Manager Login", min_value=1)
manager_password = st.text_input("Manager Password", type="password")

if st.button("Connect"):
    manager = MT5Manager.ManagerAPI()
    if manager.Connect(server_ip, manager_login, manager_password, MT5Manager.ManagerAPI.EnPumpModes.PUMP_MODE_USERS, 30000):
        st.session_state['manager'] = manager
        st.success("Connected successfully!")
    else:
        st.error("Failed to connect")

if 'manager' in st.session_state:
    manager = st.session_state['manager']
    user_login = st.number_input("User Login", min_value=1)

    if st.button("Toggle Trading Rights"):
        user = manager.UserGet(user_login)
        if user:
            user.Rights ^= MT5Manager.MTUser.EnUsersRights.USER_RIGHT_ENABLED
            if manager.UserUpdate(user):
                st.success("Trading rights updated!")
            else:
                st.error(f"Failed: {MT5Manager.LastError()}")
        else:
            st.warning("User not found.")

    balance_amount = st.number_input("Balance Adjustment", value=0.0)
    if st.button("Adjust Balance"):
        comment = st.text_input("Comment for the operation", "Balance adjustment via UI")
        deal_id = manager.DealerBalance(user_login, balance_amount, MT5Manager.MTDeal.EnDealAction.DEAL_BALANCE, comment)
        if deal_id:
            st.success(f"Balance adjusted! Deal ID: {deal_id}")
        else:
            st.error(f"Failed: {MT5Manager.LastError()}")

    leverage = st.number_input("Set Leverage", min_value=1)
    if st.button("Update Leverage"):
        user = manager.UserGet(user_login)
        if user:
            user.Leverage = leverage
            if manager.UserUpdate(user):
                st.success(f"Leverage updated to {leverage}!")
            else:
                st.error(f"Failed: {MT5Manager.LastError()}")
        else:
            st.warning("User not found.")
