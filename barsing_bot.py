from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Dispatcher, Bot, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from aiogram.dispatcher import FSMContext
from bs4 import BeautifulSoup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import os
import requests

load_dotenv('.env')

bot = Bot(token=os.environ.get('token'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


currency_buttons = [
    InlineKeyboardButton('USD', callback_data="usd"),
    InlineKeyboardButton('EUR', callback_data="eur"),
    InlineKeyboardButton('RUB', callback_data="rub"),
    InlineKeyboardButton('KZT', callback_data="kzt"),
]
currency_keyboard = InlineKeyboardMarkup().add(*currency_buttons)

class Money(StatesGroup):
    money = State()

@dp.callback_query_handler(lambda call: call.data == "usd")  
async def handle_usd_callback(call: types.CallbackQuery, state: FSMContext):
    await usd(call.message, state)

@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer("Здравствуйте! Я бот, который обменяет ваши деньги. Введите кол-во денег")
    await Money.money.set()

@dp.message_handler(commands="currency")
async def currency(message: types.Message):
    await message.answer("Теперь выберите валюту для обмена", reply_markup=currency_keyboard)

@dp.message_handler(state=Money.money)
async def money(message: types.Message, state: FSMContext):
    await state.update_data(money=message.text)
    await message.answer("Значение сохранено. Выберите валюту для обмена.", reply_markup=currency_keyboard)
    await Money.next()  # Переходим к следующему состоянию


@dp.message_handler(commands="usd", state=Money.money)
async def usd(message: types.Message, state: FSMContext):
    url = 'https://www.nbkr.kg/index.jsp?lang=RUS'
    response = requests.get(url=url)
    soup = BeautifulSoup(response.text, 'lxml')
    currencies = soup.find_all('td', class_='exrate')
    usd = float(currencies[0].text.replace(',', '.'))

    data = await state.get_data()
    money = data.get('money')

    if money is not None:
        try:
            money = float(money)
            result = money * usd
            await message.answer(f"Результат: {result}")
        except ValueError:
            await message.answer("Введено некорректное значение денег")
    else:
        await message.answer("Не удалось получить значение денег")

    await state.finish()


executor.start_polling(dp)