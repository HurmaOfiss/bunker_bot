import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

# Укажите здесь ваш рабочий прокси (пример для HTTP)
PROXY_URL = "http://127.0.0.1:1080"


async def main():
    # Создаем сессию с прокси
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # ... (ваш код с регистрацией хендлеров)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())