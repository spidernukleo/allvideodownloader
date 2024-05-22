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
from pytube import YouTube
import re

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
            await bot.send_message(update.chat.id, "Grazie per aver aggiunto Video Downloader Bot!\n\nDa ora potrai mandare il link di un qualsiasi video su <b>youtube</b>, <b>instagram</b> o <b>tiktok</b> e lo manderò in questa chat in pochissimo tempo! ⬇️\n\nPer qualsiasi problema @nukleodev")
            
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
            text="🎞 Benvenuto in Video Downloader Bot!\n\nCome funziona ❓\nÈ semplice: mandami il link di un video su <b>youtube</b>, <b>instagram</b> o <b>tiktok</b> e lo scaricherò per te rimandandotelo in pochissimo tempo!\n\nPremi il bottone qua sotto per aggiungere il bot ai tuoi gruppi! ⬇️\n\nCreato da @nukleodev"
            await bot.send_message(chatid, text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Aggiungimi ora!",url="https://t.me/all_videodownloaderbot?startgroup")]]))
        else:
            await bot.send_message(chatid, "Grazie per aver aggiunto Video Downloader Bot!\n\nDa ora potrai mandare il link di un qualsiasi video su <b>youtube</b>, <b>instagram</b> o <b>tiktok</b> e lo manderò in questa chat in pochissimo tempo!\n\nPer qualsiasi problema @nukleodev")

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
                asyncio.create_task(scaricaMandaYT(bot, link, chatid))
            elif "tiktok.com" in link:
                await message.reply("❗ Supporto solo youtube per ora")
            elif "x.com" in link or "twitter.com" in link:
                await message.reply("❗ Supporto solo youtube per ora")
            elif "instagram.com" in link:
                await message.reply("❗ Supporto solo youtube per ora")

    return

async def scaricaMandaYT(bot, url, chatid):
    try:
        yt = YouTube(url)
        if yt.length>600: return await bot.send_message(chatid, "❗ Posso scaricare video fino a 10 minuti massimo, per chiarimenti contatta @nukleodev")
        video_stream = yt.streams.get_highest_resolution()
        video_stream.download(".")
        await bot.send_video(chatid, yt.title+".mp4", caption="<a href='t.me/all_videodownloaderbot'>🔗 All Video Downloader</a>")
        os.remove(yt.title+".mp4")
    except Exception as e:
        return await bot.send_message(chatid, "❗ Non sono riuscito a scaricare il video, riprova più tardi o contatta @nukleodev")

def extract_first_social_media_link(text):
    patterns = [
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)',             
        r'(https?://youtu\.be/[\w-]+)',                                    
        r'(https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/[\d]+)',          
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
