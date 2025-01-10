import streamlit as st
from telegram_service import TelegramService
from datetime import datetime
import atexit
import time
import base64
from config import ENV


if ENV == 'streamlit':
    # Reconstruct session from chunks
    chunks = []
    total_chunks = int(st.secrets.SESSION_CHUNKS)
    for i in range(total_chunks):
        chunks.append(st.secrets[f'SESSION_CHUNK_{i}'])
    
    session_data = ''.join(chunks)
    session_bytes = base64.b64decode(session_data)
    
    with open('anon.session', 'wb') as f:
        f.write(session_bytes)

# Initialize session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
    st.session_state.initialized = False
    st.session_state.client = None
    st.session_state.retry_count = 0

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

if 'log_placeholder' not in st.session_state:
    st.session_state.log_placeholder = st.empty()

# Initialize service with retry
MAX_RETRIES = 3
while not st.session_state.initialized and st.session_state.retry_count < MAX_RETRIES:
    try:
        loop = TelegramService.get_loop()
        st.session_state.client = loop.run_until_complete(TelegramService.get_instance())
        
        # Validate connection
        if not st.session_state.client.is_connected():
            raise Exception("Client not connected")
            
        loop.run_until_complete(TelegramService.setup_handlers(add_log))
        me = loop.run_until_complete(st.session_state.client.get_me())
        
        if not me:
            raise Exception("Authentication failed")
            
        add_log(f"Service running as: {me.first_name}")
        st.session_state.initialized = True
        
    except Exception as e:
        st.session_state.retry_count += 1
        add_log(f"Service error (attempt {st.session_state.retry_count}): {str(e)}")
        if st.session_state.retry_count < MAX_RETRIES:
            time.sleep(2)  # Wait before retry
        else:
            add_log("Maximum retry attempts reached. Please check your credentials.")

if st.session_state.logs:
    st.session_state.log_placeholder.code('\n'.join(st.session_state.logs))