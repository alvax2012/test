# coding: utf-8
import asyncio
import os
from datetime import timedelta

import requests
import scrapetube
import telegram
import yt_dlp
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

channel_id = os.getenv("YOUTUBE_CHANNEL") or ""
performer = "iXBT Games"
process_one_video = os.getenv("PROCESS_ONE_VIDEO", "True") == "True"

tg_bot_token = os.getenv("TG_BOT_TOKEN") or ""
tg_chat_id = os.getenv("TG_CHAT_ID") or ""

tg_local_mode = os.getenv("TG_LOCAL_MODE", "False") == "True"
tg_base_url = os.getenv("TG_BASE_URL") or ""
tg_base_file_url = os.getenv("TG_BASE_FILE_URL") or ""

# Используем scrapetube для получения списка последних N видео и стримов
def get_last_videos(channel_id, limit: int):
    videos = scrapetube.get_channel(channel_id, limit=limit, content_type="videos")
    streams = scrapetube.get_channel(channel_id, limit=limit, content_type="streams")

    # Инвертируем списки чтобы обрабатывать в порядке добавления на канал
    videos = list(videos)[::-1]
    streams = list(streams)[::-1
                            ]
    videos = [*videos, *streams]

    videos = [
        {"id": v["videoId"], "url": f"https://www.youtube.com/watch?v={v['videoId']}"}
        for v in videos
    ]
    return videos

# Собираем описание с тайм-кодами из списка глав
def chapters_to_str(chapters):
    chap_array = []
    for chapter in chapters:
        td = timedelta(seconds=chapter["start_time"])
        chap_array.append(f"{td} - {chapter['title']}")
    return "\n".join(chap_array)


logger.info("Trying to get links for 5 last videos and streams")
try:
    videos = get_last_videos(channel_id, 5)
except Exception as e:
    logger.error(f"Can`t get video urls: {e}")
    exit(0)

# Настройки для yt_dlp
logger.info("Init youtube downloader")
ydl_opts = {
    "format": "m4a/bestaudio/worst",
    "outtmpl": "cache/%(id)s.%(ext)s",
    "keepvideo": False,
    "noplaylist": True,
    "continue_dl": True,
    "verbose": False,
    "quiet": True,
    "noprogress": True,
}
ydl = yt_dlp.YoutubeDL(ydl_opts)

# Инициализируем телеграм бота
logger.info("Init telegram bot")

if tg_local_mode:
    bot = telegram.Bot(
        token=tg_bot_token,
        base_url=tg_base_url,
        base_file_url=tg_base_file_url,
        local_mode=True,
    )
else:
    bot = telegram.Bot(token=tg_bot_token)

# Ф-я отправки обложки и аудио с тайм-кодами (если они есть)
async def send(chat_id, v_info):
    id = v_info["id"]
    title = v_info["title"]
    duration = v_info["duration"]
    performer = v_info["performer"]

    msg = ""
    if v_info.get("chapters", None):
        msg = chapters_to_str(v_info["chapters"])

    logger.info("sending thumbnail")
    # message = await bot.send_photo(
    #     chat_id=chat_id,
    #     photo=open(f"cache/{id}.jpg", "rb"),
    #     disable_notification=True,
    # )  # pyright: ignore

    logger.info("sending audio")
    with open(f"cache/{id}.m4a", "rb") as audio_file, open(
        f"cache/thumb.jpg", "rb"
    ) as thumbnail_file:
        message = await bot.send_audio(
            chat_id=chat_id,
            # reply_to_message_id=message.message_id,
            duration=duration,
            audio=audio_file,
            thumbnail=thumbnail_file,
            title=title,
            performer=performer,
            read_timeout=120,
            write_timeout=120,
            caption=msg,
        )  # pyright: ignore

        # message = await bot.send_message()


    pass


for video in videos:
    video_id, video_url = video["id"], video["url"]

    # Пропускаем видео если есть файл-метка в папке cache
    if os.path.exists(f"cache/{video_id}"):
        continue

    # Пробуем извлечь информацию о видео по ссылке
    # Пропускаем видео если не получилось
    try:
        logger.info("Extract info for: {}", video_id)
        video_info = ydl.extract_info(video_url, download=False)
        video_info["performer"] = performer
    except Exception as e:
        logger.info("Can`t get info for {}: {}", video_id, e)
        continue

    # Пропускаем стримы которые еще в эфире
    if video_info.get("is_live", None):
        continue

    # Скачиваем обложку в cache
    response = requests.get(video_info["thumbnail"])
    if response.status_code == 200:
        with open(f"cache/{video_id}.jpg", "wb") as f:
            f.write(response.content)
    else:
        logger.warning("Can't get thumbnail for: {}", video_id)
        continue

    # Скачиваем аудио поток
    logger.info("Downloading: {}", video_id)
    ydl.download([video_url])

    # Отправляем сообщения в телеграм
    logger.info("Sending telegram message")
    asyncio.run(send(chat_id=tg_chat_id, v_info=video_info))

    # Если дошли до этого места - считаем, что всё хорошо
    # Создаём файл-метку, которая означает, что видео обработано
    open(f"cache/{video_id}", "w").close()
    # Удаляем обложку и аудио
    # os.remove(f"cache/{video_id}.jpg")
    # os.remove(f"cache/{video_id}.m4a")

    # Выходим если обрабатываем одно видео за один запуск скрипта
    if process_one_video:
        break
