import streamlit as st
import time
import MT5Manager

REFRESH_SECONDS = 2

st.set_page_config(page_title="MT5 Manager Panel", layout="wide")
st.title("MT5 Manager – Full Control Panel")

# ---------------- LIVE MODE ----------------
if "live" not in st.session_state:
    st.session_state.live = False

c1, c2 = st.columns([1, 4])
with c1:
    st.checkbox("Live Mode", key="live")
with c2:
    st.caption(f"Auto refresh every {REFRESH_SECONDS}s")

if st.session_state.live:
    time.sleep(REFRESH_SECONDS)
    st.rerun()

# ---------------- CONNECTION ----------------
st.header("Server Connection")

server = st.text_input("Server", "188.240.63.181:443")
mgr_login = st.number_input("Manager Login", min_value=1012, step=1)
mgr_pass = st.text_input("Manager Password", type="password")

if st.button("Connect"):
    api = MT5Manager.ManagerAPI()
    ok = api.Connect(
        server,
        int(mgr_login),
        mgr_pass,
        MT5Manager.ManagerAPI.EnPumpModes.PUMP_MODE_USERS
        | MT5Manager.ManagerAPI.EnPumpModes.PUMP_MODE_POSITIONS,
        30000,
    )
    if ok:
        st.session_state.api = api
        st.success("Connected to MT5 server")
    else:
        st.error(MT5Manager.LastError())

if "api" not in st.session_state:
    st.stop()

api = st.session_state.api

# ---------------- CLIENT ----------------
st.divider()
st.header("Client Management")

login = st.number_input("Client Login", min_value=100082, step=1)
user = api.UserGet(int(login))

if not user:
    st.warning("Client not found") 
    st.stop()

RIGHTS = MT5Manager.MTUser.EnUsersRights

# ---------------- HELPERS ----------------
def enable_account(user):
    user.Rights |= RIGHTS.USER_RIGHT_ENABLED
    user.Rights |= RIGHTS.USER_RIGHT_EXPERT
    user.Rights |= RIGHTS.USER_RIGHT_TRAILING
    api.UserUpdate(user)

def disable_account(user):
    user.Rights &= ~RIGHTS.USER_RIGHT_ENABLED
    user.Rights &= ~RIGHTS.USER_RIGHT_EXPERT
    user.Rights &= ~RIGHTS.USER_RIGHT_TRAILING
    api.UserUpdate(user)

def toggle_right(flag):
    if user.Rights & flag:
        user.Rights &= ~flag
    else:
        user.Rights |= flag
    api.UserUpdate(user)

# ---------------- ACCOUNT STATUS ----------------
st.subheader("Account Status")

account_enabled = bool(user.Rights & RIGHTS.USER_RIGHT_ENABLED)

if st.toggle("Enable this account", value=account_enabled):
    enable_account(user)
    st.success("Account enabled (login + trading allowed)")
else:
    disable_account(user)
    st.error("Account disabled (login + trading blocked)")

# ---------------- TRADING PERMISSIONS ----------------
st.subheader("Trading Permissions")

c1, c2, c3 = st.columns(3)

with c1:
    st.checkbox(
        "Enable Trading",
        value=bool(user.Rights & RIGHTS.USER_RIGHT_ENABLED),
        on_change=lambda: toggle_right(RIGHTS.USER_RIGHT_ENABLED),
        disabled=not account_enabled,
    )

with c2:
    st.checkbox(
        "Enable Algo Trading (EA)",
        value=bool(user.Rights & RIGHTS.USER_RIGHT_EXPERT),
        on_change=lambda: toggle_right(RIGHTS.USER_RIGHT_EXPERT),
        disabled=not account_enabled,
    )

with c3:
    st.checkbox(
        "Enable Trailing Stops",
        value=bool(user.Rights & RIGHTS.USER_RIGHT_TRAILING),
        on_change=lambda: toggle_right(RIGHTS.USER_RIGHT_TRAILING),
        disabled=not account_enabled,
    )

# ---------------- BALANCE OPERATIONS ----------------
st.divider()
st.subheader("Balance / Credit Operations")

amount = st.number_input("Amount", min_value=0.0, step=1.0)
comment = st.text_input("Comment", "Manager operation")

OPS = {
    "Balance": MT5Manager.MTDeal.EnDealAction.DEAL_BALANCE,
    "Credit": MT5Manager.MTDeal.EnDealAction.DEAL_CREDIT,
    "Bonus": MT5Manager.MTDeal.EnDealAction.DEAL_BONUS,
    "Charge": MT5Manager.MTDeal.EnDealAction.DEAL_CHARGE,
    "Correction": MT5Manager.MTDeal.EnDealAction.DEAL_CORRECTION,
}

op = st.selectbox("Operation", OPS.keys())

c1, c2 = st.columns(2)
with c1:
    if st.button("Add", disabled=amount <= 0):
        api.DealerBalance(int(login), amount, OPS[op], comment)
        st.success("Operation executed")

with c2:
    if st.button("Remove", disabled=amount <= 0):
        api.DealerBalance(int(login), -amount, OPS[op], comment)
        st.success("Operation executed")

# ---------------- ACCOUNT METRICS ----------------
st.divider()
st.subheader("Account Overview")

acc = api.UserAccountGet(int(login))
if acc:
    bal = acc.Balance
    eq = acc.Equity
    mar = acc.Margin
    pnl = eq - bal
    level = (eq / mar * 100) if mar > 0 else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Balance", f"{bal:,.2f}")
    m2.metric("Equity", f"{eq:,.2f}")
    m3.metric("Floating PnL", f"{pnl:,.2f}")
    m4.metric("Margin", f"{mar:,.2f}")
    m5.metric("Margin %", f"{level:,.2f}")

# ---------------- OPEN POSITIONS ----------------
st.divider()
st.subheader("Open Positions")

try:
    positions = api.PositionGetByLogins([int(login)])
except:
    positions = []

if positions:
    rows = [{
        "Ticket": p.Position,
        "Symbol": p.Symbol,
        "Type": "BUY" if p.Action == MT5Manager.MTPosition.EnPositionAction.POSITION_BUY else "SELL",
        "Volume": p.Volume,
        "Open Price": p.PriceOpen,
        "Current Price": p.PriceCurrent,
        "Profit": p.Profit,
    } for p in positions]

    st.dataframe(rows, width="stretch")
else:
    st.info("No open positions")
