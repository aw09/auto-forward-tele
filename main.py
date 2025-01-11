import streamlit as st
from telegram_service import TelegramService, TelegramClient
from datetime import datetime
import atexit
import time
import base64
from config import ENV
from config import SOURCE_DIALOG_ID, TARGET_DIALOG_ID
from telethon import events
import asyncio
import nest_asyncio

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

async def init_client():
    client = await TelegramService.get_instance()
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        print("❌ Client not authorized")
        return None
    return client

# Initialize session state
if 'initialized' not in st.session_state:
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

st.title("Telegram Message Forwarder")
st.write("Service is running in background. Check logs in the designated Telegram channel.")


async def maintain_connection():
    while True:
        try:
            if not st.session_state.client or not st.session_state.client.is_connected():
                print("Reconnecting to Telegram...")
                st.session_state.client = await TelegramService.get_instance()
                await st.session_state.client.start()
                await TelegramService.start_forwarding()
                st.session_state.retry_count = 0
                print("Connection restored")
            
            # Update heartbeat
            st.session_state.last_heartbeat = time.time()
            await asyncio.sleep(10)  # Check every 30 seconds
            
        except Exception as e:
            st.session_state.retry_count += 1
            if st.session_state.retry_count > st.session_state.max_retries:
                print(f"Max retries reached. Please refresh the page.")
                break
            await asyncio.sleep(st.session_state.retry_delay)

async def main():
    if not st.session_state.initialized:
        try:
            await maintain_connection()
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    while True:  # Keep service alive
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize client
            client = loop.run_until_complete(init_client())
            if not client:
                raise Exception("Failed to initialize client")
                
            # Start forwarding
            loop.run_until_complete(TelegramService.start_forwarding())
            
            # Run forever but handle interrupts
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                break
            except Exception as e:
                TelegramService.send_log(f"❌ Loop error: {str(e)}")
                
        except Exception as e:
            TelegramService.send_log(f"❌ Main error: {str(e)}")
            print(f"❌ Error: {str(e)}")
            
        finally:
            # Cleanup before potential restart
            try:
                loop.run_until_complete(TelegramService.cleanup())
                loop.close()
            except:
                pass
            
        # Wait before reconnecting
        time.sleep(5)
