import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated,
    UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import API_ID, API_HASH, ERROR_MESSAGE, DB_CHANNEL
from database.db import db
from TechVJ.strings import HELP_TXT


class batch_temp(object):
    IS_BATCH = {}


async def downstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(chat, message.id, f"Downloaded: {txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


async def upstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(chat, message.id, f"Uploaded: {txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    buttons = [
        [InlineKeyboardButton("❣️ Developer", url="https://t.me/UpperAssam")],
        [
            InlineKeyboardButton('🔍 Support Group', url='https://t.me/UnknownBotzChat'),
            InlineKeyboardButton('🤖 Update Channel', url='https://t.me/UnknownBotz')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await client.send_message(
        chat_id=message.chat.id,
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot.\n\nUse /login to access restricted content.\nCheck /help for usage instructions.</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )


@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(chat_id=message.chat.id, text=f"{HELP_TXT}")


@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await client.send_message(chat_id=message.chat.id, text="Batch Successfully Cancelled.")


@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return

    if batch_temp.IS_BATCH.get(message.from_user.id) == False:
        return await message.reply_text("One task is already processing. Use /cancel to stop it.")

    datas = message.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    fromID = int(temp[0].strip())
    try:
        toID = int(temp[1].strip())
    except:
        toID = fromID

    batch_temp.IS_BATCH[message.from_user.id] = False

    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(message.from_user.id):
            break

        user_data = await db.get_session(message.from_user.id)
        if user_data is None:
            await message.reply("Please /login to continue.")
            batch_temp.IS_BATCH[message.from_user.id] = True
            return

        try:
            acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID)
            await acc.connect()
        except:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply("Session expired. Use /logout and /login again.")

        if "https://t.me/c/" in message.text:
            chatid = int("-100" + datas[4])
            try:
                await handle_private(client, acc, message, chatid, msgid)
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

        elif "https://t.me/b/" in message.text:
            username = datas[4]
            try:
                await handle_private(client, acc, message, username, msgid)
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

        else:
            username = datas[3]
            try:
                msg = await client.get_messages(username, msgid)
            except UsernameNotOccupied:
                await client.send_message(message.chat.id, "The username is not occupied.", reply_to_message_id=message.id)
                return
            try:
                await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
            except:
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    if ERROR_MESSAGE:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        await asyncio.sleep(3)

    batch_temp.IS_BATCH[message.from_user.id] = True


def get_message_type(msg):
    for attr in ["document", "video", "animation", "sticker", "voice", "audio", "photo", "text"]:
        if getattr(msg, attr, None):
            return attr.capitalize()
    return None


async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    msg = await acc.get_messages(chatid, msgid)
    if not msg or msg.empty:
        return

    msg_type = get_message_type(msg)
    if not msg_type:
        return

    chat = message.chat.id
    user_tag = f"From: {message.from_user.first_name}"

    smsg = await client.send_message(chat, '**Downloading**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))

    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if ERROR_MESSAGE:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
        return await smsg.delete()

    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))
    caption = (msg.caption or msg.text or "") + f"\n\n{user_tag}"

    send_args = dict(
        caption=caption,
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.MARKDOWN,
        progress=progress,
        progress_args=[message, "up"]
    )

    try:
        if msg_type == "Document":
            await client.send_document(chat, file, **send_args)
            await client.send_document(DB_CHANNEL, file, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
        elif msg_type == "Video":
            await client.send_video(chat, file, **send_args)
            await client.send_video(DB_CHANNEL, file, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
        elif msg_type == "Photo":
            await client.send_photo(chat, file, **send_args)
            await client.send_photo(DB_CHANNEL, file, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
        elif msg_type == "Audio":
            await client.send_audio(chat, file, **send_args)
            await client.send_audio(DB_CHANNEL, file, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
        elif msg_type == "Voice":
            await client.send_voice(chat, file, **send_args)
            await client.send_voice(DB_CHANNEL, file, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
        elif msg_type == "Animation":
            await client.send_animation(chat, file, **send_args)
            await client.send_animation(DB_CHANNEL, file, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
        elif msg_type == "Sticker":
            await client.send_sticker(chat, file, reply_to_message_id=message.id)
            await client.send_sticker(DB_CHANNEL, file)
    except Exception as e:
        if ERROR_MESSAGE:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    if os.path.exists(file):
        os.remove(file)

    await client.delete_messages(chat, [smsg.id])
