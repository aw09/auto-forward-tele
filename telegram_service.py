import asyncio
import nest_asyncio
from telethon import events, TelegramClient
from config import ENV, SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID, API_ID, API_HASH, LOG_DIALOG_ID
import os
import json
from datetime import datetime
import filelock
import streamlit as st
import logging
from logging.handlers import RotatingFileHandler


if ENV == 'streamlit':
    API_ID = st.secrets.API_ID
    API_HASH = st.secrets.API_HASH
    SOURCE_DIALOG_ID = int(st.secrets.SOURCE_DIALOG_ID)
    TARGET_DIALOG_ID = int(st.secrets.TARGET_DIALOG_ID)
    TARGET_TOPIC_ID = int(st.secrets.TARGET_TOPIC_ID)

class TelegramService:
    _instance = None
    _logger = None
    _loop = None  # Add class variable
    _processed_msgs = set()  # Track processed message IDs
    
    @classmethod
    def get_loop(cls):
        if not hasattr(cls, '_loop') or not cls._loop:
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
            nest_asyncio.apply()
        return cls._loop
    
    @classmethod
    async def get_instance(cls):
        cls._logger = logging.getLogger("TelegramService")
        if not cls._instance:
            cls._instance = TelegramClient(
                'anon',
                API_ID,
                API_HASH,
                system_version="4.16.30-vxCUSTOM"
            )
            await cls._instance.connect()
        return cls._instance
    
    @classmethod
    def send_log(cls, message: str):
        """
        Synchronous entry point for sending log messages to the LOG_DIALOG_ID channel.
        """
        if not cls._instance:
            return  # No client yet

        try:
            loop = cls.get_loop()
            loop.create_task(cls._instance.send_message(LOG_DIALOG_ID, message))
        except Exception as e:
            if cls._logger:
                cls._logger.error(f"Error sending log: {e}")

    @classmethod
    async def send_log_async(cls, message: str):
        """Async version of send_log for use in event handlers"""
        if not cls._instance:
            return
        try:
            await cls._instance.send_message(LOG_DIALOG_ID, message)
        except Exception as e:
            if cls._logger:
                cls._logger.error(f"Error sending log: {e}")

    @classmethod
    async def start_forwarding(cls):
        client = await cls.get_instance()
        
        @client.on(events.NewMessage(chats=[SOURCE_DIALOG_ID]))
        async def forward_handler(event):
            try:
                await cls.send_log_async(f"🔔 New message {event.message.id} from {event.message.sender_id}")
                print(f"🔔 New message {event.message.id} from {event.message.sender_id}")
                
                if event.message.id in cls._processed_msgs:
                    return
                
                result = await client.send_message(
                    TARGET_DIALOG_ID,
                    event.message,
                    reply_to=TARGET_TOPIC_ID
                )
                cls._processed_msgs.add(event.message.id)
                await cls.send_log_async(f"✅ Message forwarded successfully")
                print(f"✅ Message forwarded successfully")
            except Exception as e:
                await cls.send_log_async(f"❌ Error: {str(e)}")
                print(f"❌ Error: {str(e)}")

        # Start heartbeat task
        asyncio.create_task(cls._heartbeat_task(client))

    @classmethod
    async def _heartbeat_task(cls, client):
        while True:
            await asyncio.sleep(60*60)
            try:
                await client.send_message(LOG_DIALOG_ID, f"Heartbeat {datetime.now()}")
            except Exception as e:
                cls._logger.error(f"Heartbeat error: {e}")

    @classmethod
    async def cleanup(cls):
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None
            if os.path.exists(cls._lock_file):
                os.remove(cls._lock_file)