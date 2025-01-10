from client import client
from telethon.tl.functions.channels import GetForumTopicsRequest

CHECK_ROOM_NAME = [
    # You need to specify the room name here
]
ACTIVATE_CHECK_ROOM = True

async def get_list_room():
    async for dialog in client.iter_dialogs():
        if CHECK_ROOM_NAME:
            if dialog.name in CHECK_ROOM_NAME or not ACTIVATE_CHECK_ROOM:
                print(f"Room '{dialog.name}' has ID : {dialog.id}")
                if dialog.is_group:
                    await get_topics(dialog.id, dialog.name)
        else:
            print(f"Room '{dialog.name}' has ID : {dialog.id}")
            if dialog.is_group:
                await get_topics(dialog.id, dialog.name)

async def get_topics(group_id: int, group_name: str, limit=100):
    try:
        topics = await client(GetForumTopicsRequest(
            channel=group_id,
            offset_date=0,
            offset_id=0,
            offset_topic=0,
            limit=limit
        ))
        
        print(f"Group '{group_name}' has {len(topics.topics)} topics")
        for topic in topics.topics:
            print(f"Topic ID: {topic.id}, Title: {topic.title}")
            
    except Exception as e:
        print(f"Error getting topics: {e}")


async def main():
    await get_list_room()

with client:
    client.loop.run_until_complete(main())