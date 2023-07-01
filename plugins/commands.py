from utils import temp_utils
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from script import scripts
from vars import ADMINS
from database.data_base import db
import asyncio
import re
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

@Client.on_message(filters.command("start"))
async def start_message(bot, message):
    user = await db.is_user_exist(message.from_user.id)
    if not user:
        await db.new_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    else:
        pass
    btn = [[
            InlineKeyboardButton("About", callback_data="about"),
            InlineKeyboardButton("Souce Code", callback_data="source")
        ],[
            InlineKeyboardButton("Close", callback_data="close"),
            InlineKeyboardButton("Help", callback_data="help")
        ]]
    await message.reply_text(
        text=scripts.START_TXT.format(message.from_user.mention, temp_utils.USER_NAME, temp_utils.BOT_NAME),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(btn)
    )


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


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('Logs.txt')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def skip_msgs(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp_utils.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")

@Client.on_message(filters.command('set_target'))
async def set_target(bot, message):
    content = message.text
    try:
        target_id = content.split(" ", 1)[1]
    except:
        return await message.reply_text(
            text="<b>Hey give a channel ID where I'm admin along with the command !</b>"
        )
    try:
        target_id = int(target_id)
    except:
        return await message.reply_text(
            text="Give me a valid chat ID"
        )
    if target_id and target_id is not None:
        await db.update_any(message.from_user.id, 'target_chat', int(target_id))
        return await message.reply_text(
            text=f"Successfully set target chat ID to {target_id}"
        )
    else:
        return await message.reply_text(
            text="Give me a valid chat ID"
        )
