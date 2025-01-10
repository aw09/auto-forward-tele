import os
from binascii import unhexlify

# Run this locally to get session hex
with open('anon.session', 'rb') as f:
    session_content = f.read().hex()

# Write the hex to a file
with open('anon.session.hex', 'w') as f:
    f.write(session_content)