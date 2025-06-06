from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='➕ Добавить трату'), KeyboardButton(text='📜 История расходов')],
        [KeyboardButton(text='📊 Статистика'), KeyboardButton(text='ℹ️ Помощь')]
    ],
    resize_keyboard=True
)

stats_period_keyboard_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📅 Сегодня'), KeyboardButton(text='📆 Неделя')],
        [KeyboardButton(text='🗓 Месяц'), KeyboardButton(text='🔙 Назад')]
    ],
    resize_keyboard=True
)

history_period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📅 Сегодня", callback_data="his:Сегодня")],
    [InlineKeyboardButton(text="📆 Неделя", callback_data="his:Неделя")],
    [InlineKeyboardButton(text="🗓 Месяц", callback_data="his:Месяц")]
])

stats_period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📅 День", callback_data="stat:День"),
     InlineKeyboardButton(text="📆 Неделя", callback_data="stat:Неделя")],
    [InlineKeyboardButton(text="🗓 Месяц", callback_data="stat:Месяц"),
     InlineKeyboardButton(text="📅 Год", callback_data="stat:Год")],
    [InlineKeyboardButton(text="⏳ Все время", callback_data="stat:Все время")]
])

category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛒 Продукты", callback_data="cat:Продукты")],
    [InlineKeyboardButton(text="🍽 Рестораны", callback_data="cat:Рестораны")],
    [InlineKeyboardButton(text="👕 Одежда", callback_data="cat:Одежда")],
    [InlineKeyboardButton(text="🚗 Транспорт", callback_data="cat:Транспорт")],
    [InlineKeyboardButton(text="🎮 Развлечения", callback_data="cat:Развлечения")],
    [InlineKeyboardButton(text="🎁 Подарки", callback_data="cat:Подарки")],
    [InlineKeyboardButton(text="💳 Подписки", callback_data="cat:Подписки")],
    [InlineKeyboardButton(text="💊 Аптека", callback_data="cat:Аптека")]
])

skip_cancel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🔄 Пропустить'), KeyboardButton(text='❌ Отмена')]
    ],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='❌ Отмена')]],
    resize_keyboard=True
)
