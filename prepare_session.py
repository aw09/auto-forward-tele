import base64
import os
from config import API_HASH, API_ID, SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID, LOG_DIALOG_ID, LOG_TOPIC_ID

# Create .streamlit directory if it doesn't exist
secrets_dir = '.streamlit'
if not os.path.exists(secrets_dir):
    os.makedirs(secrets_dir)

# Write Telegram API credentials to secrets.toml
with open(os.path.join(secrets_dir, 'secrets.toml'), 'w') as f:
    f.write(f'API_ID = "{API_ID}"\n')
    f.write(f'API_HASH = "{API_HASH}"\n')
    f.write(f'SOURCE_DIALOG_ID = "{SOURCE_DIALOG_ID}"\n')
    f.write(f'TARGET_DIALOG_ID = "{TARGET_DIALOG_ID}"\n')
    f.write(f'TARGET_TOPIC_ID = "{TARGET_TOPIC_ID}"\n')
    f.write(f'LOG_DIALOG_ID = "{LOG_DIALOG_ID}"\n')
    f.write(f'LOG_TOPIC_ID = "{LOG_TOPIC_ID}"\n')

# Read and encode session file
with open('anon.session', 'rb') as f:
    data = f.read()
    b64 = base64.b64encode(data).decode()

# Split into 30KB chunks
chunk_size = 30000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

# Write to secrets.toml
secrets_path = os.path.join(secrets_dir, 'secrets.toml')
with open(secrets_path, 'a') as f:  # Append mode to preserve existing secrets
    f.write(f'\nSESSION_CHUNKS = "{len(chunks)}"\n')
    for i, chunk in enumerate(chunks):
        f.write(f'SESSION_CHUNK_{i} = "{chunk}"\n')

print(f"Added {len(chunks)} session chunks to {secrets_path}")