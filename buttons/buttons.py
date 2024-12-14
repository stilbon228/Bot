from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки
    builder.row(
        KeyboardButton(text="🗺️ Построить маршрут"),
        KeyboardButton(text="Мое местоположение")
    )
    builder.row(
        KeyboardButton(text="Помощь")
    )

    return builder.as_markup(resize_keyboard=True)
def get_location_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # Кнопка отправки геолокации
    builder.row(
        KeyboardButton(text="Отправить геолокацию", request_location=True)
    )
    builder.row(
        KeyboardButton(text="Назад")
    )

    return builder.as_markup(resize_keyboard=True)


def get_review_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для опроса с вариантами ответа.

    :return: Разметка клавиатуры с кнопками "Отлично" и "Плохо".
    """
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="👍 Отлично"),
        KeyboardButton(text="👎 Плохо")
    )

    builder.row(
        KeyboardButton(text="Назад")  # Кнопка для возврата
    )

    return builder.as_markup(resize_keyboard=True)