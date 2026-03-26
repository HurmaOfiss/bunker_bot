import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN
from handlers import register_handlers

logging.basicConfig(level=logging.INFO)

# Твой SOCKS5 прокси с авторизацией
PROXY_URL = "socks5://jtwbqWxBm8:aMoQTeD2J6@109.120.130.74:27942"

async def main():
    # Создаем сессию с прокси
    session = AiohttpSession(proxy=PROXY_URL)
    
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    await register_handlers(dp, bot)
    
    logging.info("✅ Бот запущен через SOCKS5 прокси!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
