import streamlit as st
from telethon import events
import asyncio
import nest_asyncio
from client import client
from config import SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID
from datetime import datetime

# Enable nested event loops
nest_asyncio.apply()

# Initialize event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def add_log(message):
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

async def forward_handler(event):
    try:
        add_log(f"New message detected from {SOURCE_DIALOG_ID}")
        await client.send_message(
            entity=TARGET_DIALOG_ID,
            message=event.message,
            reply_to=TARGET_TOPIC_ID
        )
        add_log("Message forwarded successfully")
    except Exception as e:
        add_log(f"Error forwarding message: {e}")

async def init_client():
    await client.start()
    client.add_event_handler(forward_handler, events.NewMessage(chats=SOURCE_DIALOG_ID))
    me = await client.get_me()
    return me

def main():
    st.title("Telegram Message Forwarder")
    
    # Create log container
    log_container = st.empty()
    
    if st.button("Start Forwarding"):
        me = loop.run_until_complete(init_client())
        add_log(f"Logged in as: {me.first_name}")
        add_log(f"Listening for messages from {SOURCE_DIALOG_ID}")
        
        # Display logs
        if 'logs' in st.session_state:
            log_container.code('\n'.join(st.session_state.logs))
        
        # Keep client running
        try:
            loop.run_until_complete(client.run_until_disconnected())
        except Exception as e:
            add_log(f"Error: {e}")
            log_container.code('\n'.join(st.session_state.logs))

if __name__ == "__main__":
    main()