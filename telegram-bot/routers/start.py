from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer("1")
