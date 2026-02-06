# utils/filters.py
from pyrogram.types import Message

def match_media_filter(message: Message, filters_list: list[str]) -> bool:
    if not filters_list:
        return False  # Empty filters skip all
    if 'text' in filters_list and message.text:
        return True
    if 'image' in filters_list and message.photo:
        return True
    if 'video' in filters_list and message.video:
        return True
    if 'pdf' in filters_list and message.document and message.document.mime_type == 'application/pdf':
        return True
    return False
