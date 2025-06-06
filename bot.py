from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from config import BOT_TOKEN
from database import init_db, add_expense, get_expenses_by_period, get_stats_by_period
from kb import main_keyboard, stats_period_keyboard, category_keyboard, skip_cancel, cancel_keyboard, history_period_keyboard
import asyncio
import logging
from pprint import pprint

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Логирование ошибок и действий
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


class AddExpense(StatesGroup):
    choosing_category = State()
    entering_amount = State()
    entering_description = State()

class HistoryPeriod(StatesGroup):
    choosing_period = State()

class StatsPeriod(StatesGroup):
    choosing_period = State()

####################################Функция старт####################################################

@dp.message(CommandStart())
async def start(message: Message):
    logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} запустил бота")

    await message.answer("Привет! Я помогу тебе следить за расходами 💰", reply_markup=main_keyboard)

####################################Функция отмены####################################################

@dp.message(F.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Что желаешь сделать? 💰", reply_markup=main_keyboard)

##################################Добавить трату#####################################################

# Обработка кнопки "Добавить трату"
@dp.message(F.text == "➕ Добавить трату")
async def start_add_expense(message: Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} начал добавлять трату")
    await message.answer("Выбери категорию:", reply_markup=category_keyboard)
    await state.set_state(AddExpense.choosing_category)


# Получение категории
@dp.callback_query(F.data.startswith("cat:"))
async def category_entered(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    await state.update_data(category=category)

    logging.info(f"Пользователь {callback.from_user.username}/{callback.from_user.id} выбрал категорию: {category}")

    await callback.message.delete()
    await callback.message.answer(f"Выбрана категория: {category}")
    bot_msg = await callback.message.answer("Теперь введи сумму траты (только число):", reply_markup=cancel_keyboard)

    await state.update_data(sum_msg_id=bot_msg.message_id)
    await state.set_state(AddExpense.entering_amount)
    await callback.answer()


# Получение суммы
@dp.message(AddExpense.entering_amount, F.text)
async def amount_entered(message: Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
        await state.update_data(amount=amount)

        logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} ввел сумму: {amount}")
        await message.delete()

        data = await state.get_data()
        sum_msg_id = data.get("sum_msg_id")
        if sum_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=sum_msg_id)
            except Exception:
                pass

        await message.answer(f"Сумма: {amount}")
        des_msg = await message.answer(f"Хочешь добавить описание к трате? Отправь его сообщением или нажми «Пропустить».", reply_markup=skip_cancel)
        await state.update_data(des_msg_id=des_msg.message_id)

        await state.set_state(AddExpense.entering_description)
    else:
        logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} ввел некорректную сумму")
        await message.answer("Некорректно введена сумма. Попробуйте заново!", reply_markup=cancel_keyboard)


# Обработка описания
@dp.message(AddExpense.entering_description)
async def description_entered(message: Message, state: FSMContext):
    user_data = await state.get_data()

    if message.text != "🔄 Пропустить":
        description = message.text
        await message.answer(f"Описание: {description}")
        logging.info(
            f"Пользователь {message.from_user.username}/{message.from_user.id} ввел описание: {description}")

    else:
        description =  ""
        logging.info(
            f"Пользователь {message.from_user.username}/{message.from_user.id} пропустил описание")

    await message.delete()
    des_msg_id = user_data.get("des_msg_id")
    if des_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=des_msg_id)
        except Exception:
            pass

    await add_expense(
        user_id=message.from_user.id,
        category=user_data["category"],
        amount=user_data["amount"],
        description=description
    )
    await message.answer("✅ Трата добавлена!", reply_markup=main_keyboard)
    await state.clear()
    logging.info(
        f"Пользователь {message.from_user.username}/{message.from_user.id} добавил трату: {user_data['category']} - {user_data['amount']} ₽ - {description}")


####################################История расходов####################################################

# Обработка кнопки "История расходов"
@dp.message(F.text == "📜 История расходов")
async def start_history(message: Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} запросил историю расходов")
    await message.answer("Выбери период:", reply_markup=history_period_keyboard)
    await state.set_state(HistoryPeriod.choosing_period)


# Получение категории, запрос истории, обработка и отправка ее пользователю
@dp.callback_query(F.data.startswith("his:"))
async def history_period_entered(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split(":")[1]
    await state.update_data(period=period)

    logging.info(f"Пользователь {callback.from_user.username}/{callback.from_user.id} выбрал период истории: {period}")

    await callback.message.delete()
    await callback.message.answer(f"Выбран период: {period}\nЗагружаем историю...")
    user_history_data = await get_expenses_by_period(callback.from_user.id, period)
    logging.info(f"Пользователь {callback.from_user.username}/{callback.from_user.id} отправил запрос об истории расходов в БД")

    history_message = f"История трат за {period.lower()}:\n"
    for date, expenses in user_history_data.items():
        history_message += f"\n{date}:\n"
        for expense in expenses:
            time = expense[0]
            category, amount, description = expense[1]
            history_message += f"  {time}: {category} - {amount}₽ - {description}\n"

    await callback.message.answer(history_message)

####################################Статистика расходов####################################################

# Обработка кнопки "Статистика"
@dp.message(F.text == "📊 Статистика")
async def start_stats(message: Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} запросил статистику")
    await message.answer("Выбери период для статистики:", reply_markup=stats_period_keyboard)
    await state.set_state(StatsPeriod.choosing_period)


# Получение периода и отправка статистики
@dp.callback_query(F.data.startswith("stat:"))
async def stats_period_entered(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split(":")[1]
    await state.update_data(period=period)

    logging.info(
        f"Пользователь {callback.from_user.username}/{callback.from_user.id} выбрал период статистики: {period}")

    await callback.message.delete()
    await callback.message.answer(f"Выбран период: {period}\nСчитаем статистику...")

    category_totals = await get_stats_by_period(callback.from_user.id, period)
    total_amount = sum(category_totals.values())

    stats_message = f"📊 Статистика за {period.lower()}:\n\n"
    stats_message += f"Всего потрачено: {total_amount}₽\n\n"

    if category_totals:
        stats_message += "По категориям:\n"
        for category, amount in category_totals.items():
            percentage = (amount / total_amount) * 100 if total_amount > 0 else 0
            stats_message += f"  {category}: {amount}₽ ({percentage:.1f}%)\n"
    else:
        stats_message += "Нет данных о расходах за выбранный период."

    await callback.message.answer(stats_message, reply_markup=main_keyboard)
    await state.clear()
    await callback.answer()

####################################Помощь####################################################

# Обработка кнопки "Помощь"
@dp.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    help_text = """
🤖 <b>Помощь по боту учета расходов</b> 💰

<b>Основные команды:</b>
➕ Добавить трату - внести новую трату
📜 История расходов - просмотр истории трат
📊 Статистика - просмотр статистики по категориям

<b>Как добавить трату:</b>
1. Нажмите "➕ Добавить трату"
2. Выберите категорию
3. Введите сумму (только число)
4. При желании добавьте описание или пропустите этот шаг

<b>История расходов:</b>
Показывает все ваши траты за выбранный период с детализацией по времени.

<b>Статистика:</b>
Показывает общую сумму расходов и распределение по категориям в процентах.

<b>Доступные периоды:</b>
- День
- Неделя
- Месяц
- Год
- Все время

Для начала работы просто выберите нужное действие в меню.
"""
    await message.answer(help_text, parse_mode="HTML", reply_markup=main_keyboard)
    logging.info(f"Пользователь {message.from_user.username}/{message.from_user.id} запросил помощь")

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
