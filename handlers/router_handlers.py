import re
import os
import time
import requests
import xml.etree.ElementTree as ET
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from selenium import webdriver
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from buttons.buttons import get_main_keyboard, get_location_keyboard, get_review_keyboard
from lexicon import LEXICON_RU

router = Router()


class RouteStates(StatesGroup):
    waiting_for_route = State()


@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(LEXICON_RU["/start"], reply_markup=get_main_keyboard())


@router.message(Command(commands='review'))
async def review_command(message: Message):
    await message.answer(LEXICON_RU["/review"], reply_markup=get_review_keyboard())


@router.message(F.text == "👍 Отлично")
async def review_positive(message: Message):
    await message.answer(LEXICON_RU["review_positive"])


@router.message(F.text == "👎 Плохо")
async def review_negative(message: Message):
    await message.answer(LEXICON_RU["review_negative"])


@router.message(F.text == "Назад")
async def go_back_from_review(message: Message):
    await message.answer(LEXICON_RU["go_back"], reply_markup=get_main_keyboard())


@router.message(F.text == "🗺️ Построить маршрут")
async def route_menu(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU["route_menu"])
    await state.set_state(RouteStates.waiting_for_route)


@router.message(F.text == "Помощь")
@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(LEXICON_RU["/help"], reply_markup=get_main_keyboard())


@router.message(F.text == "📍 Мое местоположение")
async def request_location(message: Message):
    await message.answer(LEXICON_RU["request_location"], reply_markup=get_location_keyboard())


@router.message(F.location)
async def handle_location(message: Message):
    location = message.location
    if location:
        response_message = (
            LEXICON_RU["handle_location"].format(latitude=location.latitude, longitude=location.longitude))
        await message.answer(response_message, reply_markup=get_main_keyboard())
    else:
        await message.answer(LEXICON_RU["handle_location_error"], reply_markup=get_main_keyboard())


def get_coordinates(api_key: str, address: str) -> tuple[float, float]:
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": api_key,
        "geocode": address,
        "format": "json"
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("response"):
            geo_object = data["response"]["GeoObjectCollection"]["featureMember"]
            if geo_object:
                point = geo_object[0]["GeoObject"]["Point"]["pos"].split()
                lat, lon = float(point[1]), float(point[0])
                return (lat, lon)

    return (None, None)


def parse_route(url: str) -> str:
    ua = UserAgent()
    user_agent = ua.random
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        meta_tag = soup.find('meta', property='og:image:secure_url')
        if meta_tag and 'content' in meta_tag.attrs:
            image_url = meta_tag['content']
            match = re.search(r'pl=([^&]+)', image_url)
            if match:
                pl_param = match.group(1)
                coordinates = re.findall(r'-?\d+\.\d+', pl_param)

                if len(coordinates) % 2 != 0:
                    print("Количество координат нечётное.")
                    return None

                route_points = [(float(coordinates[i]), float(coordinates[i + 1])) for i in
                                range(0, len(coordinates), 2)]

                gpx = ET.Element("gpx", version="1.1", creator="Yandex Maps Parser")
                trk = ET.SubElement(gpx, "trk")
                ET.SubElement(trk, "name").text = "Yandex Maps Route"
                trkseg = ET.SubElement(trk, "trkseg")

                for lon, lat in route_points:
                    trkpt = ET.SubElement(trkseg, "trkpt", lat=str(lat), lon=str(lon))
                    ET.SubElement(trkpt, "ele").text = "0"
                    ET.SubElement(trkpt, "time").text = "2023-10-01T00:00:00Z"

                gpx_data = ET.tostring(gpx, encoding='utf-8', method='xml')
                gpx_file_path = f"route_{int(time.time())}.gpx"

                with open(gpx_file_path, "wb") as gpx_file:
                    gpx_file.write(gpx_data)

                return gpx_file_path

    finally:
        driver.quit()


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

        route_types = {
            "auto": "rtt=auto",
            "pedestrian": "rtt=pd",
            "scooter": "rtt=sc",
            "motorcycle": "rtt=bc"
        }

        gpx_files = []

        for mode, rtt in route_types.items():
            route_url = (
                f"https://yandex.ru/maps/?ll={origin_coords[1]},{origin_coords[0]}"
                f"&mode=routes&rtext={origin_coords[0]},{origin_coords[1]}~{destination_coords[0]},{destination_coords[1]}&{rtt}&ruri=~&z=16"
            )
            gpx_file_path = parse_route(route_url)
            if gpx_file_path:
                gpx_files.append((mode, gpx_file_path))

        for mode, gpx_file_path in gpx_files:
            with open(gpx_file_path, 'rb') as file:
                await message.reply_document(FSInputFile(gpx_file_path), caption=f"GPX файл для {mode} маршрута.")

        for _, gpx_file_path in gpx_files:
            os.remove(gpx_file_path)

        response_message = (
            LEXICON_RU["route_info"].format(origin=origin,
                                            origin_coords_0=origin_coords[0],
                                            origin_coords_1=origin_coords[1],
                                            destination=destination,
                                            destination_coords_0=destination_coords[0],
                                            destination_coords_1=destination_coords[1])

        )

        await state.clear()
        await message.reply(response_message)

    except Exception as e:
        await message.reply(LEXICON_RU["error"].format(e=e))