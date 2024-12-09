from telethon import events
from client import client
from config import SOURCE_DIALOG_ID, TARGET_DIALOG_ID, TARGET_TOPIC_ID

@client.on(events.NewMessage(chats=SOURCE_DIALOG_ID))
async def handler(event):
    try:
        print(f"New message detected from {SOURCE_DIALOG_ID}")
        # Forward complete message including media
        await client.send_message(
            entity=TARGET_DIALOG_ID,
            message=event.message,
            reply_to=TARGET_TOPIC_ID
        )
        print("Message forwarded successfully")
    except Exception as e:
        print(f"Error forwarding message: {e}")

async def main():
    me = await client.get_me()
    print(me.stringify())

    # Start listening for new messages
    print(f"Listening for new messages in dialog ID {SOURCE_DIALOG_ID}...")


with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
