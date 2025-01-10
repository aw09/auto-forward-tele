import streamlit as st
from telethon import events
import asyncio
import nest_asyncio
from client import client
from config import SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID

# Enable nested event loops
nest_asyncio.apply()

# Initialize event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def forward_handler(event):
    try:
        print(f"New message detected from {SOURCE_DIALOG_ID}")
        await client.send_message(
            entity=TARGET_DIALOG_ID,
            message=event.message,
            reply_to=TARGET_TOPIC_ID
        )
        print("Message forwarded successfully")
    except Exception as e:
        print(f"Error forwarding message: {e}")

async def init_client():
    await client.start()
    client.add_event_handler(forward_handler, events.NewMessage(chats=SOURCE_DIALOG_ID))
    me = await client.get_me()
    return me

def main():
    st.title("Telegram Message Forwarder")
    
    if st.button("Start Forwarding"):
        me = loop.run_until_complete(init_client())
        st.write(f"Logged in as: {me.first_name}")
        st.write(f"Listening for messages from {SOURCE_DIALOG_ID}")
        
        # Keep client running
        try:
            loop.run_until_complete(client.run_until_disconnected())
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()