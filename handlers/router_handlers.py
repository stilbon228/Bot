import re
from database.database import insert_user_route
import xml.etree.ElementTree as ET
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from fake_useragent import UserAgent
from aiogram import Router, F  # Импортируем необходимые классы и функции из aiogram
from aiogram.filters import Command  # Импортируем фильтр команд для обработки команд в сообщениях
from aiogram.types import Message, FSInputFile  # Импортируем типы сообщений и файлов для отправки документов
import requests  # Библиотека для выполнения HTTP-запросов
import os  # Модуль для работы с операционной системой

from buttons.buttons import get_main_keyboard, get_location_keyboard, \
    get_review_keyboard  # Импортируем функцию для создания клавиатуры
from lexicon import LEXICON_RU

router = Router()  # Создаем экземпляр маршрутизатора


# Класс состояний для построения маршрута
class RouteStates(StatesGroup):
    waiting_for_route = State()  # Ожидание ввода адресов для маршрута


# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        LEXICON_RU["/start"],
        reply_markup=get_main_keyboard()
    )


# Обработчик команды /review
@router.message(Command(commands='review'))
async def review_command(message: Message):
    """
    Обработчик команды /review.

    :param message: Сообщение от пользователя.
    """
    await message.answer(
        LEXICON_RU["/review"],
        reply_markup=get_review_keyboard()  # Отправляем клавиатуру с вариантами ответа
    )


# Обработчик положительного отзыва
@router.message(F.text == "👍 Отлично")
async def review_positive(message: Message):
    """
    Обработчик положительного отзыва.

    :param message: Сообщение от пользователя.
    """
    await message.answer(LEXICON_RU["review_positive"])


# Обработчик отрицательного отзыва
@router.message(F.text == "👎 Плохо")
async def review_negative(message: Message):
    """
    Обработчик отрицательного отзыва.

    :param message: Сообщение от пользователя.
    """
    await message.answer(LEXICON_RU["review_negative"])


# Обработчик кнопки "Назад" из опроса
@router.message(F.text == "Назад")
async def go_back_from_review(message: Message):
    """
    Обработчик кнопки 'Назад' из опроса.

    :param message: Сообщение от пользователя.
    """
    # Проверяем текущее состояние, чтобы определить, откуда возвращается пользователь

    await message.answer(
        LEXICON_RU["go_back"],
        reply_markup=get_main_keyboard()  # Возвращаем главную клавиатуру
    )


# Обработчик кнопки "Построить маршрут"
@router.message(F.text == "🗺️ Построить маршрут")
async def route_menu(message: Message, state: FSMContext):
    await message.answer(
        LEXICON_RU["route_menu"]
    )
    await state.set_state(RouteStates.waiting_for_route)  # Устанавливаем состояние ожидания маршрута


# Обработчик команды /help (или кнопки "Помощь")
@router.message(F.text == "Помощь")
@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        LEXICON_RU["/help"],
        reply_markup=get_main_keyboard()
    )


# Обработчик кнопки "Мое местоположение"
@router.message(F.text == "📍 Мое местоположение")
async def request_location(message: Message):
    await message.answer(
        LEXICON_RU["request_location"],
        reply_markup=get_location_keyboard()
    )


# Обработчик получения геолокации
@router.message(F.location)
async def handle_location(message: Message):
    location = message.location

    if location:
        response_message = (
            LEXICON_RU["handle_location"].format(latitude=location.latitude, longitude=location.longitude)
        )

        await message.answer(
            response_message,
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            LEXICON_RU["handle_location_error"],
            reply_markup=get_main_keyboard()
        )


# Функция для получения координат по адресу
def get_coordinates(api_key: str, address: str) -> tuple[float, float]:
    """
    Получить координаты по адресу с использованием Yandex Geocoder API.

    :param api_key: API ключ для доступа к Yandex API.
    :param address: Адрес для геокодирования.
    :return: Кортеж с широтой и долготой.
    """
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": api_key,
        "geocode": address,
        "format": "json"
    }

    response = requests.get(url, params=params)  # Выполняем GET-запрос к API

    if response.status_code == 200:
        data = response.json()  # Парсим ответ в формате JSON
        if data.get("response"):
            geo_object = data["response"]["GeoObjectCollection"]["featureMember"]
            if geo_object:
                point = geo_object[0]["GeoObject"]["Point"]["pos"].split()
                lat, lon = float(point[1]), float(point[0])  # Извлекаем широту и долготу из ответа
                return (lat, lon)
            else:
                return (None, None)
        else:
            return (None, None)
    else:
        raise Exception(f"Ошибка при запросе Geocoder API: {response.status_code}")  # Обработка ошибок


# Функция для парсинга маршрута и сохранения в GPX-файл
def parse_route(url: str) -> str:
    """
    Парсит маршрут по URL и сохраняет его в GPX-файл.

    :param url: URL маршрута на Яндекс.Картах.
    :return: Путь к сохраненному GPX-файлу.
    """
    ua = UserAgent()  # Генерация случайного user-agent для обхода защиты сайтов от ботов
    user_agent = ua.random

    options = webdriver.ChromeOptions()  # Настройки для Chrome WebDriver
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")  # Запуск в headless режиме (без графического интерфейса)
    options.add_argument("--no-sandbox")  # Опционально для повышения стабильности работы драйвера
    options.add_argument("--disable-dev-shm-usage")  # Опционально для устранения проблем с памятью

    driver = webdriver.Chrome(options=options)  # Инициализация драйвера Chrome

    try:
        driver.get(url)  # Переход по указанному URL

        time.sleep(5)  # Ожидание загрузки страницы

        soup = BeautifulSoup(driver.page_source, 'html.parser')  # Парсинг HTML-кода страницы с помощью BeautifulSoup

        meta_tag = soup.find('meta', property='og:image:secure_url')  # Поиск элемента <meta> с нужным атрибутом

        if meta_tag and 'content' in meta_tag.attrs:
            image_url = meta_tag['content']  # Извлечение URL изображения из мета-тега

            match = re.search(r'pl=([^&]+)', image_url)  # Извлечение параметра pl из URL изображения
            if match:
                pl_param = match.group(1)

                coordinates = re.findall(r'-?\d+\.\d+', pl_param)  # Извлечение координат из параметра pl

                if len(coordinates) % 2 != 0:
                    print("Количество координат нечётное, возможно, данные повреждены.")
                else:
                    route_points = [(float(coordinates[i]), float(coordinates[i + 1])) for i in
                                    range(0, len(coordinates), 2)]  # Формирование списка точек маршрута

                    gpx = ET.Element("gpx", version="1.1", creator="Yandex Maps Parser")
                    trk = ET.SubElement(gpx, "trk")
                    ET.SubElement(trk, "name").text = "Yandex Maps Route"
                    trkseg = ET.SubElement(trk, "trkseg")

                    for lon, lat in route_points:
                        trkpt = ET.SubElement(trkseg, "trkpt", lat=str(lat), lon=str(lon))
                        ET.SubElement(trkpt, "ele").text = "0"
                        ET.SubElement(trkpt,
                                      "time").text = "2023-10-01T00:00:00Z"

                    gpx_data = ET.tostring(gpx, encoding='utf-8', method='xml')
                    with open("route.gpx", "wb") as gpx_file:
                        gpx_file.write(gpx_data)

                    print("Маршрут успешно сохранён в route.gpx")
                    return "route.gpx"
            else:
                print("Параметр pl не найден в URL.")
        else:
            print("Элемент <meta> не найден.")
    finally:
        driver.quit()  # Закрытие драйвера


# Обработчик запроса на построение маршрута
@router.message(RouteStates.waiting_for_route)
async def process_route_request(message: Message, state: FSMContext, config):
    try:
        if "->" not in message.text:
            await message.reply(LEXICON_RU["invalid_format"])
            return

        origin, destination = map(str.strip, message.text.split("->"))

        origin_coords = get_coordinates(config.yandex.api_key, origin)
        destination_coords = get_coordinates(config.yandex.api_key, destination)

        if not origin_coords[0] or not destination_coords[0]:
            await message.reply(LEXICON_RU["address_not_found"])
            return

        route_url_1 = (
            f"https://yandex.ru/maps/?ll={origin_coords[1]},{origin_coords[0]}&mode=routes&rtext={origin_coords[0]},{origin_coords[1]}~{destination_coords[0]},{destination_coords[1]}=pd&ruri=~&z=16"
        )

        gpx_file_path = parse_route(route_url_1)
        with open(gpx_file_path, 'r') as file:
            gpx_data = file.read()

        insert_user_route(message.from_user.id, f"{origin} -> {destination}", gpx_data)

        await message.reply_document(FSInputFile(gpx_file_path), caption=LEXICON_RU["gpx_caption"])

        response_message = (
            LEXICON_RU["route_info"].format(origin=origin, origin_coords_0=origin_coords[0],
                                            origin_coords_1=origin_coords[1], destination=destination,
                                            destination_coords_0=destination_coords[0],
                                            destination_coords_1=destination_coords[1], route_url_1=route_url_1)
        )

        os.remove(gpx_file_path)
        await state.clear()

        await message.reply(response_message)

    except Exception as e:
        await message.reply(LEXICON_RU["error"].format(e=e))