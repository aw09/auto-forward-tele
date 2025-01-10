import asyncio
import nest_asyncio
from telethon import events, TelegramClient
from config import ENV, SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID, API_ID, API_HASH
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
    _loop = None
    _logger = None
    
    @classmethod
    def get_loop(cls):
        if not cls._loop:
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
            nest_asyncio.apply()
        return cls._loop

    @classmethod
    async def get_instance(cls):
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
    def setup_logging(cls):
        if not cls._logger:
            cls._logger = logging.getLogger('telegram_service')
            cls._logger.setLevel(logging.INFO)
            handler = RotatingFileHandler('telegram.log', maxBytes=1024*1024, backupCount=5)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            cls._logger.addHandler(handler)
        return cls._logger
    
    @classmethod
    async def start_forwarding(cls, log_callback=None):
        cls.setup_logging()
        client = await cls.get_instance()
        
        @client.on(events.NewMessage(chats=[SOURCE_DIALOG_ID]))
        async def forward_handler(event):
            try:
                # Core forwarding logic
                cls._logger.info(f"Message received from {event.chat_id}")
                await client.send_message(
                    TARGET_DIALOG_ID,
                    event.message,
                    reply_to=TARGET_TOPIC_ID
                )
                cls._logger.info("Message forwarded successfully")
                
                # Optional UI logging
                if log_callback:
                    try:
                        log_callback(f"Message forwarded from {event.chat_id}")
                    except streamlit.runtime.scriptrunner_utils.StopException:
                        cls._logger.info("UI disconnected, continuing in background")
                    except Exception as e:
                        cls._logger.error(f"UI logging failed: {e}")
                        
            except Exception as e:
                cls._logger.error(f"Forward failed: {e}")

    @classmethod
    async def cleanup(cls):
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None
            if os.path.exists(cls._lock_file):
                os.remove(cls._lock_file)