from dotenv import load_dotenv
import os
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str  # Telegram Bot API token




@dataclass
class YandexAPI:
    api_key: str


@dataclass
class Config:
    tg_bot: TgBot
    yandex: YandexAPI  #


def load_config():  # Загружаем данные из файла .env
    load_dotenv()
    return Config(
        tg_bot=TgBot(token=os.getenv("TG_BOT_TOKEN")),
        yandex=YandexAPI(api_key=os.getenv("YANDEX_API_KEY"))
    )