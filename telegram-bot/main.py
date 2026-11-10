import asyncio
import logging

from routers import routers
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config()
    bot = Bot(token=config.bot_token)
    print(config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    for router in routers:
        dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
