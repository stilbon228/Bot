from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo

def get_main_keyboard():
    keyboard = [
        [
            KeyboardButton(text="🗺️ Построить маршрут"),
            KeyboardButton(text="📍 Мое местоположение")
        ],
        [
            KeyboardButton(text="Помощь"),


        ]
    ]
    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)
    return markup
def get_location_keyboard():
    keyboard = [
        [
            KeyboardButton(text="Отправить геолокацию", request_location=True)
        ],
        [
            KeyboardButton(text='Назад')
        ]

    ]
    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return markup
def get_review_keyboard():
    keyboard = [
        [
            KeyboardButton(text="👍 Отлично"),
            KeyboardButton(text="👎 Плохо")
        ],
        [
            KeyboardButton(text="Назад")
        ]
    ]
    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return markup