# Auto Forward Telegram Channel

## Requirements
- Python 3.6 or higher
- [Telethon](https://docs.telethon.dev/en/stable/basic/quick-start.html)


## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
1. Check [Telethon documentation](https://docs.telethon.dev/en/stable/basic/signing-in.html) to get your `api_id` and `api_hash`.
1. Create a `.env` file in the root directory and add the following:
    ```bash
    API_ID=your_api_id
    API_HASH=your_api_hash
    ```
1. Run the script to get source and target channel IDs:
    ```bash
    python get_channel_id.py
    ```

1. Update .env again using new channel ids and topics

    ```bash
    API_ID=your_api_id
    API_HASH=your_api_hash
    SOURCE_DIALOG_ID=your_source_channel_id
    TARGET_DIALOG_ID=your_target_channel_id
    TARGET_TOPIC_ID=1
    ```
1. Run the script
    ```bash
    python main.py
    ```