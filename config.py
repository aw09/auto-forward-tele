from dotenv import load_dotenv
import os

load_dotenv()

ENV = os.getenv('ENV', 'streamlit')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SOURCE_DIALOG_ID = int(os.getenv('SOURCE_DIALOG_ID'))
TARGET_DIALOG_ID = int(os.getenv('TARGET_DIALOG_ID'))
TARGET_TOPIC_ID = int(os.getenv('TARGET_TOPIC_ID'))
