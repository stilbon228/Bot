import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config.config import load_config  # Import function to load configuration
from handlers.router_handlers import router  # Import router for handling messages
from middle.middleware import ConfigMiddleware  # Import middleware for configuration

# Загрузка конфигурации из .env файла
config = load_config()

# Инициализация бота с токеном из конфигурации и создание диспетчера
bot = Bot(token=config.tg_bot.token)
dp = Dispatcher()


# Добавление middleware для доступа к конфигурации в обработчиках
dp.message.middleware(ConfigMiddleware(config))

# Регистрация роутера для обработки сообщений
dp.include_router(router)

# Запуск бота в асинхронном режиме
async def main():
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())  # Запускаем основную функцию