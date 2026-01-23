from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os
import sys

# --- Чтение и проверка переменных окружения ---
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")

if API_TOKEN is None:
    print("Ошибка: переменная окружения API_TOKEN не установлена!")
    sys.exit(1)
if ADMIN_ID_STR is None:
    print("Ошибка: переменная окружения ADMIN_ID не установлена!")
    sys.exit(1)

# Убираем кавычки и пробелы, приводим к int
try:
    ADMIN_ID = int(ADMIN_ID_STR.replace('"', '').strip())
except ValueError:
    print(f"Ошибка: ADMIN_ID должно быть числом. Получено: {ADMIN_ID_STR}")
    sys.exit(1)

# --- Инициализация бота ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- Стейты ---
class Application(StatesGroup):
    name = State()
    contact = State()
    text = State()

# --- Клавиатура ---
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❓ Задать вопрос")
    kb.add("📝 Оставить заявку")
    return kb

# --- Обработчики ---
@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте!\n\n"
        "Вы обратились в компанию *SHEVELEV*, монтаж отопления и водопровода.\n"
        "Работаем с частными лицами, индивидуальный подход к каждому объекту.\n\n"
        "Выберите, что вас интересует:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

faq = types.InlineKeyboardMarkup(row_width=1)
faq.add(
    types.InlineKeyboardButton("💰 Сколько стоит", callback_data="price"),
    types.InlineKeyboardButton("⏱ Как быстро", callback_data="time"),
    types.InlineKeyboardButton("📅 Когда можно встретиться", callback_data="meet")
)

@dp.message_handler(text="❓ Задать вопрос")
async def ask(message: types.Message):
    await message.answer("Выберите вопрос или напишите свой:", reply_markup=faq)

@dp.callback_query_handler(lambda c: c.data in ["price", "time", "meet"])
async def faq_answer(call: types.CallbackQuery):
    answers = {
        "price": "Стоимость рассчитывается индивидуально после осмотра и уточнения объёма работ.",
        "time": "Сроки зависят от сложности объекта, обычно выполняем работы в кратчайшие сроки.",
        "meet": "Время выезда согласовывается индивидуально, подстраиваемся под клиента."
    }
    await call.message.answer(answers[call.data])
    await call.answer()

@dp.message_handler(text="📝 Оставить заявку")
async def start_form(message: types.Message):
    await Application.name.set()
    await message.answer("Укажите ваше имя:")

@dp.message_handler(state=Application.name)
async def form_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Application.contact.set()
    await message.answer("Контактный телефон или Telegram:")

@dp.message_handler(state=Application.contact)
async def form_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await Application.text.set()
    await message.answer("Кратко опишите задачу:")

@dp.message_handler(state=Application.text)
async def form_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = (
        f"📩 *Новая заявка SHEVELEV*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Контакт: {data['contact']}\n"
        f"📝 Задача: {message.text}"
    )
    await bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    await message.answer("Заявка отправлена. Мы свяжемся с вами.")
    await state.finish()

# --- Запуск бота ---
if __name__ == "__main__":
    print(f"Бот запускается! ADMIN_ID = {ADMIN_ID}")
    executor.start_polling(dp, skip_updates=True)
