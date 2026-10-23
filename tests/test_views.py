import json
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
import requests

from src.views import generate_main_page_data, get_greeting


def test_get_greeting() -> None:
    """Тестирует выдачу приветствий в зависимости от времени суток по ТЗ."""
    assert get_greeting(datetime(2020, 5, 20, 8, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2020, 5, 20, 14, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2020, 5, 20, 19, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2020, 5, 20, 23, 30, 0)) == "Доброй ночи"


@pytest.fixture
def mock_transactions() -> list:
    """Фикстура с тестовыми транзакциями для главной страницы."""
    return [
        {"Дата операции": "20.05.2020 16:44:00", "Номер карты": "*4556", "Сумма операции": -2500.0, "Категория": "Одежда"},
        {"Дата операции": "20.05.2020 16:42:04", "Номер карты": "*4556", "Сумма операции": -1200.0, "Категория": "Супермаркеты"},
        {"Дата операции": "20.05.2020 15:44:39", "Номер карты": "*1111", "Сумма операции": -500.0, "Категория": "Фастфуд"},
        {"Дата операции": "28.04.2020 01:23:42", "Номер карты": "*4556", "Сумма операции": -9000.0, "Категория": "Аренда"},
    ]


@patch("src.views.requests.get")
def test_generate_main_page_data_success(mock_get: Any, mock_transactions: list) -> None:
    """Тест успешной генерации JSON главной страницы при работающем API."""
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 0.011, "EUR": 0.010}}

    json_str = generate_main_page_data(
        "2020-05-20 18:00:00",
        mock_transactions,
        ["USD", "EUR"],
        ["AAPL"]
    )
    result = json.loads(json_str)

    assert result["greeting"] == "Добрый вечер"
    assert len(result["cards"]) == 2

    # Ищем чисто по твоему родному ключу last_digits из operations.xlsx
    card_4556 = next(c for c in result["cards"] if c.get("last_digits") == "4556")
    assert card_4556.get("total_spent") == 3700.0

    assert len(result["top_transactions"]) == 5


@patch("src.views.requests.get")
def test_generate_main_page_data_api_failure(mock_get: Any, mock_transactions: list) -> None:
    """Тест обработки падения внешних API — приложение выдает дефолтные курсы."""
    mock_get.side_effect = requests.RequestException("API Down")

    json_str = generate_main_page_data(
        "2020-05-20 12:00:00",
        mock_transactions,
        ["USD"],
        ["AAPL"]
    )
    result = json.loads(json_str)

    assert result["greeting"] == "Добрый день"
