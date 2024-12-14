from aiogram.types import TelegramObject
from aiogram import BaseMiddleware
from typing import Callable, Any


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config):
        super().__init__()
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        # Добавляем конфигурацию в данные
        data["config"] = self.config
        return await handler(event, data)