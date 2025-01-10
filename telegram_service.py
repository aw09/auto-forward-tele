import asyncio
import nest_asyncio
from telethon import events, TelegramClient
from config import ENV, SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID, API_ID, API_HASH
import os
import json
from datetime import datetime
import filelock
import streamlit as st


if ENV == 'streamlit':
    API_ID = st.secrets.API_ID
    API_HASH = st.secrets.API_HASH
    SOURCE_DIALOG_ID = int(st.secrets.SOURCE_DIALOG_ID)
    TARGET_DIALOG_ID = int(st.secrets.TARGET_DIALOG_ID)
    TARGET_TOPIC_ID = int(st.secrets.TARGET_TOPIC_ID)

class TelegramService:
    _lock_file = "telegram.lock"
    _instance = None
    _loop = None
    
    @classmethod
    def get_loop(cls):
        if not cls._loop:
            nest_asyncio.apply()
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
        return cls._loop

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            lock = filelock.FileLock(cls._lock_file)
            try:
                with lock.acquire(timeout=1):
                    cls._instance = TelegramClient(
                        'anon',
                        API_ID,
                        API_HASH,
                        system_version="4.16.30-vxCUSTOM",
                        sequential_updates=True,
                        loop=cls.get_loop()
                    )
                    await cls._instance.connect()
            except filelock.Timeout:
                raise Exception("Service already running")
        return cls._instance

    @classmethod
    async def setup_handlers(cls, log_callback):
        client = await cls.get_instance()
        
        @client.on(events.NewMessage(chats=SOURCE_DIALOG_ID))
        async def forward_handler(event):
            try:
                log_callback(f"New message detected from {SOURCE_DIALOG_ID}")
                await client.send_message(
                    entity=TARGET_DIALOG_ID,
                    message=event.message,
                    reply_to=TARGET_TOPIC_ID
                )
                log_callback("Message forwarded successfully")
            except Exception as e:
                log_callback(f"Error forwarding message: {str(e)}")

    @classmethod
    async def cleanup(cls):
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None
            if os.path.exists(cls._lock_file):
                os.remove(cls._lock_file)