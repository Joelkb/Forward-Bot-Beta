import re
import logging
import asyncio
from vars import ADMINS
from utils import temp_utils
from database.data_base import db
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChannelInvalid, UsernameInvalid, UsernameNotModified
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

@Client.on_message((filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def forward_cmd(bot, message):
    if message.from_user.id not in ADMINS: return # admin only
    if message.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        source_chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if source_chat_id.isnumeric():
            source_chat_id  = int(("-100" + source_chat_id))
    elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        source_chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(source_chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')
    try:
        k = await bot.get_messages(source_chat_id, last_msg_id)
    except:
        return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
    if k.empty:
        return await message.reply('This may be group and iam not a admin of the group.')
    if lock.locked():
        return await message.reply_text('<b>Wait until previous process complete.</b>')
    user = await db.get_user(int(message.from_user.id))
    if user is not None:
        if user['target_chat'] is None:
            return await bot.send_message(
                chat_id=message.from_user.id,
                text="<b>Fist add your target channel ID using /set_target command !</b>"
            )
        else:
            pass
    else:
        await db.new_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await db.update_any(message.from_user.id, 'last_msg_id', f'{last_msg_id}')
    await db.update_any(message.from_user.id, 'source_chat_id', f'{source_chat_id}')
    temp_utils.UTILS[int(message.from_user.id)] = {
        'last_msg_id': int(last_msg_id),
        'source_chat_id': int(source_chat_id),
        'target_chat_id': int(user['target_chat'])
    }
    button = [[
        InlineKeyboardButton("YES", callback_data=f"forward#{message.from_user.id}")
    ],[
        InlineKeyboardButton("NO", callback_data="close")
    ]]
    target_chat = await bot.get_chat(chat_id=int(user['target_chat']))
    source_chat = await bot.get_chat(chat_id=int(source_chat_id))
    await message.reply_text(
        text=f"Do you want to start forwarding from {source_chat.title} to {target_chat.title} ?",
        reply_markup=InlineKeyboardMarkup(button)
    )