import streamlit as st
from telegram_service import TelegramService
from datetime import datetime
import atexit

# Initialize session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
    st.session_state.initialized = False
    st.session_state.client = None

def cleanup():
    if st.session_state.client:
        TelegramService.get_loop().run_until_complete(TelegramService.cleanup())

atexit.register(cleanup)

def add_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")
    if 'log_placeholder' in st.session_state:
        st.session_state.log_placeholder.code('\n'.join(st.session_state.logs))

st.title("Telegram Message Forwarder")

# Create log placeholder
if 'log_placeholder' not in st.session_state:
    st.session_state.log_placeholder = st.empty()

# Initialize service only once
if not st.session_state.initialized:
    try:
        loop = TelegramService.get_loop()
        st.session_state.client = loop.run_until_complete(TelegramService.get_instance())
        loop.run_until_complete(TelegramService.setup_handlers(add_log))
        me = loop.run_until_complete(st.session_state.client.get_me())
        add_log(f"Service running as: {me.first_name}")
        st.session_state.initialized = True
    except Exception as e:
        add_log(f"Service error: {str(e)}")

# Display logs
if st.session_state.logs:
    st.session_state.log_placeholder.code('\n'.join(st.session_state.logs))