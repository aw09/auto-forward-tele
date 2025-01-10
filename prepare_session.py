import base64
import os

# Create chunks directory if it doesn't exist
chunks_dir = 'session_chunks'
if not os.path.exists(chunks_dir):
    os.makedirs(chunks_dir)

# Read and encode session file
with open('anon.session', 'rb') as f:
    data = f.read()
    b64 = base64.b64encode(data).decode()

# Split into 30KB chunks
chunk_size = 30000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

# Write chunks to separate files
for i, chunk in enumerate(chunks):
    chunk_path = os.path.join(chunks_dir, f'chunk_{i}.txt')
    with open(chunk_path, 'w') as f:
        f.write(chunk)

# Write config file with chunk count
with open(os.path.join(chunks_dir, 'config.txt'), 'w') as f:
    f.write(str(len(chunks)))

print(f"Created {len(chunks)} chunks in {chunks_dir} directory")