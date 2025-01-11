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
    _loop = asyncio.new_event_loop()  # Single event loop instance
    _processed_msgs = set()
    _heartbeat_task = None

    @classmethod
    def get_loop(cls):
        return cls._loop

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            cls._instance = TelegramClient(
                'anon',
                API_ID,
                API_HASH,
                system_version="4.16.30-vxCUSTOM",
                loop=cls._loop  # Pass loop to client
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
    async def start_forwarding(cls):
        client = await cls.get_instance()
        
        # Start heartbeat only once
        if not cls._heartbeat_task or cls._heartbeat_task.done():
            cls._heartbeat_task = cls._loop.create_task(cls._heartbeat())
        
        @client.on(events.NewMessage(chats=[SOURCE_DIALOG_ID]))
        async def forward_handler(event):
            try:
                cls.send_log(f"🔔 New message {event.message.id} from {event.message.sender_id}")
                
                # Check if message already processed
                if event.message.id in cls._processed_msgs:
                    return
                
                # Forward message
                result = await client.send_message(
                    TARGET_DIALOG_ID,
                    event.message,
                    reply_to=TARGET_TOPIC_ID
                )
                
                # Track processed message
                cls._processed_msgs.add(event.message.id)
                
                # Keep cache size manageable (last 1000 messages)
                if len(cls._processed_msgs) > 1000:
                    cls._processed_msgs = set(list(cls._processed_msgs)[-1000:])
                
                cls.send_log(f"✅ Message {event.message.id} forwarded")
                
            except Exception as e:
                cls.send_log(f"❌ Error forwarding message {event.message.id}: {str(e)}")

    @classmethod
    async def _heartbeat(cls):
        client = await cls.get_instance()
        while True:
            try:
                await client.send_message(LOG_DIALOG_ID, "Heartbeat ✓")
                await asyncio.sleep(60, loop=cls._loop)  # Pass loop to sleep
            except Exception as e:
                if cls._logger:
                    cls._logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5, loop=cls._loop)

    @classmethod
    async def cleanup(cls):
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None
            if os.path.exists(cls._lock_file):
                os.remove(cls._lock_file)