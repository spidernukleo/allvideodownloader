import asyncio
import os
import sys
import time
import redis
from pyrogram import Client, idle
from pyrogram.enums import ParseMode, ChatType, ChatMemberStatus
from pyrogram.handlers import MessageHandler, ChatMemberUpdatedHandler
from pyrogram.session.session import Session
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import subprocess, random
import requests
import bs4
from pytube import YouTube


# Genera sessione pyro
async def pyro(token):
    Session.notice_displayed = True

    API_HASH = ''
    API_ID = ''

    bot_id = str(token).split(':')[0]
    app = Client(
        'sessioni/session_bot' + str(bot_id),
        api_hash=API_HASH,
        api_id=API_ID,
        bot_token=token,
        workers=20,
        sleep_threshold=30
    )
    return app


async def chat_handler(bot, update):
    old_member = update.old_chat_member
    new_member = update.new_chat_member
    if old_member and not old_member.user.id == bot_id: return
    if new_member and not new_member.user.id == bot_id: return 
    if update.chat.type == ChatType.CHANNEL:
        try:
            await bot.leave_chat(chat_id=update.chat.id)
        except Exception as e:
            print(str(e))
        return
    if (not update.old_chat_member or update.old_chat_member.status == ChatMemberStatus.BANNED): # controllo se l'evento è specificamente di aggiunta
        members=await bot.get_chat_members_count(update.chat.id)
        if members<50:
            await bot.send_message(update.chat.id, "Mi dispiace, il bot è abilitato solamente per gruppi con almeno 50 utenti, riaggiungilo quando avrai raggiunto quella soglia, per qualsiasi chiarimento @nukleodev")
            await bot.leave_chat(chat_id=update.chat.id)
        elif update.chat.type == ChatType.GROUP:
            await bot.send_message(update.chat.id, "Mi dispiace, il bot è abilitato solamente per SUPERGRUPPI, riaggiungilo quando avrai reso questo gruppo un supergruppo, per qualsiasi chiarimento @nukleodev")
            await bot.leave_chat(chat_id=update.chat.id)
        else:
            await bot.send_message(update.chat.id, "Grazie per aver aggiunto Video Downloader Bot!\n\nDa ora potrai mandare il link di un qualsiasi video su <b>youtube</b>, <b>instagram</b>, <b>X</b> o <b>tiktok</b> e lo manderò in questa chat in pochissimo tempo! ⬇️\n\nPer qualsiasi problema @nukleodev")
            
    return

async def bot_handler(bot, message):
    if message.media or message.service or message.from_user.is_bot: return
    text = str(message.text)
    if text == '/start' or text == '/start@all_videodownloaderbot':
        userid = message.from_user.id
        last_time=redis.get(userid)
        if last_time:
            elapsed_time = time.time() - float(last_time)
            if elapsed_time<3: return
        redis.set(userid, time.time())
        chatid = message.chat.id
        tipo = message.chat.type
        if tipo==ChatType.PRIVATE:
            text="🎞 Benvenuto in Video Downloader Bot!\n\nCome funziona ❓\nÈ semplice: mandami il link di un video su <b>youtube</b>, <b>instagram</b>, <b>X</b> o <b>tiktok</b> e lo scaricherò per te rimandandotelo in pochissimo tempo!\n\nPremi il bottone qua sotto per aggiungere il bot ai tuoi gruppi! ⬇️\n\nCreato da @nukleodev"
            await bot.send_message(chatid, text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Aggiungimi ora!",url="https://t.me/all_videodownloaderbot?startgroup")]]))
        else:
            await bot.send_message(chatid, "Grazie per aver aggiunto Video Downloader Bot!\n\nDa ora potrai mandare il link di un qualsiasi video su <b>youtube</b>, <b>instagram</b>, <b>X</b> o <b>tiktok</b> e lo manderò in questa chat in pochissimo tempo!\n\nPer qualsiasi problema @nukleodev")

    else:
        link = extract_first_social_media_link(text)
        if link:
            userid = message.from_user.id
            chatid = message.chat.id
            last_time=redis.get(userid)
            if last_time:
                elapsed_time = time.time() - float(last_time)
                if elapsed_time<10:
                    await bot.send_reaction(chatid, message.id, "👎")
                    return
            redis.set(userid, time.time())
            await bot.send_reaction(chatid, message.id, "👀")
            if "youtube.com" in link or "youtu.be" in link:
                asyncio.create_task(scaricaMandaYT(bot, link, chatid, message.id))
            elif "tiktok.com" in link:
                '''asyncio.create_task(scaricaMandaTT(bot, link, chatid, message.id))'''
                print("entrato qua tiktikok")
            elif "x.com" in link or "twitter.com" in link:
                asyncio.create_task(scaricaMandaX(bot, link, chatid, message.id))
            elif "instagram.com" in link:
                await message.reply("❗ Supporto solo youtube per ora")

    return



async def scaricaMandaYT(bot, url, chatid, replyid):
    try:
        nome = str(random.randint(1,1000000))
        yt = YouTube(url)
        if yt.length >= 1800:
            return await bot.send_message(chatid, "❗ Durata massima video: 30 minuti.", reply_to_message_id=replyid)
        else:
            stream = yt.streams.get_highest_resolution()
            stream.download(filename=nome+".mp4")
        asyncio.create_task(send_video_async(bot, chatid, nome+".mp4", replyid))
    except Exception as e:
        await bot.send_message(chatid, "❗ Non sono riuscito a scaricare il video, riprova più tardi o contatta @nukleodev", reply_to_message_id=replyid)

async def scaricaMandaX(bot, url, chatid, replyid):
    try:
        api_url = f"https://twitsave.com/info?url={url}"
        response = requests.get(api_url)
        data = bs4.BeautifulSoup(response.text, "html.parser")
        download_button = data.find_all("div", class_="origin-top-right")[0]
        quality_buttons = download_button.find_all("a")
        highest_quality_url = quality_buttons[0].get("href")
        nome = str(random.randint(1,1000000))+".mp4"
        response = requests.get(highest_quality_url, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        with open(nome, "wb") as file:
            for data in response.iter_content(block_size):
                file.write(data)
        asyncio.create_task(send_video_async(bot, chatid, nome, replyid))
    except Exception as e:
        return await bot.send_message(chatid, "❗ Non sono riuscito a scaricare il video, riprova più tardi, assicurati che l'account non sia privato e che il post contenga effettivamente un video o contatta @nukleodev", reply_to_message_id=replyid)



async def send_video_async(bot, chatid, nome, replyid):
    try:
        await bot.send_video(chatid, nome, caption="<a href='t.me/all_videodownloaderbot'>🔗 All Video Downloader</a>", reply_to_message_id=replyid)
        os.remove(nome)
    except Exception as e:
        return await bot.send_message(chatid, "❗ Non sono riuscito a inviare il video, riprova più tardi o contatta @nukleodev", reply_to_message_id=replyid)


async def mandaPost(bot, chat_to, chat_from, msg_id):
    try:
        await bot.copy_message(chat_id=chat_to,from_chat_id=chat_from, message_id=msg_id)
    except Exception as e:
        print(str(e))

def extract_first_social_media_link(text):
    patterns = [
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)',
        r'(https?://youtu\.be/[\w-]+)',
        r'(https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/[\d]+)',
        r'(https?://vm\.tiktok\.com/[\w-]+)',  # Added pattern for TikTok short links
        r'(https?://(?:www\.)?instagram\.com/p/[\w-]+)',
        r'(https?://(?:www\.)?instagram\.com/reel/[\w-]+)',
        r'(https?://(?:www\.)?instagram\.com/tv/[\w-]+)',
        r'(https?://(?:www\.)?x\.com/[\w.-]+/status/[\d]+)',
        r'(https?://(?:www\.)?twitter\.com/[\w.-]+/status/[\d]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

async def main(bot_id):
    print(f'Genero sessione [{bot_id}] > ', end='')
    SESSION = await pyro(token=TOKEN)
    HANDLERS = {
        'msg': MessageHandler(bot_handler),
        'chat': ChatMemberUpdatedHandler(chat_handler)
    }
    SESSION.add_handler(HANDLERS['msg'])
    SESSION.add_handler(HANDLERS['chat'])


    print('avvio > ', end='')
    await SESSION.start()

    print('avviati!')
    await idle()

    print('Stopping > ', end='')
    await SESSION.stop()

    loop.stop()
    print('stopped!\n')
    exit()


if __name__ == '__main__':
    TOKEN = ''
    bot_id = int(TOKEN.split(':')[0])
    loop = asyncio.get_event_loop()
    redis = redis.Redis(host='localhost', port=6379, db=7)
    loop.run_until_complete(main(bot_id))
    exit()
