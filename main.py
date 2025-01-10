import streamlit as st
from telegram_service import TelegramService
from datetime import datetime
import atexit
import time
import base64
from config import ENV
from config import SOURCE_DIALOG_ID, TARGET_DIALOG_ID
from telethon import events
import asyncio
import nest_asyncio

# Initialize logging first
TelegramService.setup_logging()

# Initialize event loop once at startup
nest_asyncio.apply()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

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


async def async_debug_checks():
    try:
        # Check source dialog
        source = await st.session_state.client.get_entity(SOURCE_DIALOG_ID)
        add_log(f"Source channel found: {source.title}")
        
        # Check target dialog
        target = await st.session_state.client.get_entity(TARGET_DIALOG_ID)
        add_log(f"Target channel found: {target.title}")
        
        # Check permissions
        participant = await st.session_state.client.get_permissions(target)
        add_log(f"Bot permissions in target: {participant.to_dict()}")
        
        # Add test message event handler
        @st.session_state.client.on(events.NewMessage())
        async def debug_handler(event):
            add_log(f"Debug: Message received from {event.chat_id}")
        
        add_log("Debug event handler registered")
        
    except Exception as e:
        add_log(f"Debug check failed: {str(e)}")


# Initialize session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
    st.session_state.initialized = False
    st.session_state.client = None
    st.session_state.retry_count = 0
    st.session_state.last_heartbeat = time.time()
    st.session_state.max_retries = 5
    st.session_state.retry_delay = 5

def cleanup():
    if st.session_state.client:
        TelegramService.get_loop().run_until_complete(TelegramService.cleanup())

atexit.register(cleanup)

def add_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # File logging
    try:
        TelegramService._logger.info(message)
    except Exception as e:
        print(f"Logging error: {e}")
    
    # UI logging
    try:
        if 'logs' in st.session_state:
            st.session_state.logs.append(f"[{timestamp}] {message}")
            if 'log_placeholder' in st.session_state:
                st.session_state.log_placeholder.code('\n'.join(st.session_state.logs))
    except Exception:
        pass

st.title("Telegram Message Forwarder")

if 'log_placeholder' not in st.session_state:
    st.session_state.log_placeholder = st.empty()

async def maintain_connection():
    while True:
        try:
            if not st.session_state.client or not st.session_state.client.is_connected():
                add_log("Reconnecting to Telegram...")
                st.session_state.client = await TelegramService.get_instance()
                await st.session_state.client.start()
                await TelegramService.start_forwarding(add_log)
                st.session_state.retry_count = 0
                add_log("Connection restored")
            
            # Update heartbeat
            st.session_state.last_heartbeat = time.time()
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            st.session_state.retry_count += 1
            if st.session_state.retry_count > st.session_state.max_retries:
                add_log(f"Max retries reached. Please refresh the page.")
                break
            await asyncio.sleep(st.session_state.retry_delay)

async def main():
    if not st.session_state.initialized:
        try:
            await maintain_connection()
        except Exception as e:
            add_log(f"Error: {str(e)}")
            st.error("Connection lost. Click below to reconnect.")
            
    if st.button("Reconnect"):
        st.session_state.initialized = False
        st.session_state.retry_count = 0
        st.experimental_rerun()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

# Remove run_until_disconnected() since Streamlit handles the lifecycle
if st.session_state.logs:
    st.session_state.log_placeholder.code('\n'.join(st.session_state.logs))