from utils import temp_utils
from database.data_base import db
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pyrogram import enums
import logging
import asyncio
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

async def start_forward(bot, userid):
    util = temp_utils.UTILS.get(int(userid))
    if util is not None:
        source_chat_id = util.get('source_chat_id')
        last_msg_id = util.get('last_msg_id')
        TARGET_DB = util.get('target_chat_id')
    else:
        user = await db.get_user(int(userid))
        if user and user['on_process'] and not user['is_complete']:
            source_chat_id = user['source_chat']
            last_msg_id = user['last_msg_id']
            TARGET_DB = user['target_chat']
        else:
            return
    btn = [[
        InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
    ]]
    active_msg = await bot.send_message(
        chat_id=int(userid),
        text="<b>Starting Forward Process...</b>",
        reply_markup = InlineKeyboardMarkup(btn)
    )
    skipped = int(temp_utils.CURRENT)
    total = 0
    forwarded = 0
    empty = 0
    notmedia = 0
    unsupported = 0
    left = 0
    status = 'Idle'
    async with lock:
        try:
            btn = [[
                InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
            ]]
            status = 'Forwarding...'
            await active_msg.edit(
                text=f"<b>Forwarding on progress...\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            current = temp_utils.CURRENT
            temp_utils.CANCEL = False
            await db.update_any(userid, 'on_process', True)
            await db.update_any(userid, 'is_complete', False)
            async for msg in bot.iter_messages(source_chat_id, int(last_msg_id), int(temp_utils.CURRENT)):
                if temp_utils.CANCEL:
                    status = 'Cancelled !'
                    await active_msg.edit(f"<b>Successfully Cancelled!\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>")
                    break
                left = int(last_msg_id)-int(total)
                total = current
                current += 1
                if current % 20 == 0:
                    btn = [[
                        InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
                    ]]
                    await db.update_any(userid, 'fetched', total)
                    status = 'Sleeping for 30 seconds.'
                    await active_msg.edit(
                        text=f"<b>Forwarding on progress...\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    await asyncio.sleep(30)
                    status = 'Forwarding...'
                    await active_msg.edit( 
                        text=f"<b>Forwarding on progress...\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>", 
                        reply_markup=InlineKeyboardMarkup(btn) 
                    )
                if msg.empty:
                    empty+=1
                    continue
                elif not msg.media:
                    notmedia += 1
                    continue
                elif msg.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                try:
                    await msg.copy(
                        chat_id=int(TARGET_DB)
                    )
                    forwarded+=1
                    await asyncio.sleep(1)
                except FloodWait as e:
                    btn = [[
                        InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
                    ]]
                    await active_msg.edit(
                        text=f"<b>Got FloodWait.\n\nWaiting for {e.value} seconds.</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    await asyncio.sleep(e.value)
                    await msg.copy(
                        chat_id=int(TARGET_DB)
                    )
                    forwarded+=1
                    continue
            status = 'Completed !'
        except Exception as e:
            logger.exception(e)
            await active_msg.edit(f'<b>Error:</b> <code>{e}</code>')
        else:
            await db.update_any(userid, 'on_process', False)
            await db.update_any(userid, 'is_complete', True)
            await active_msg.edit(f"<b>Successfully Completed Forward Process !\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>")