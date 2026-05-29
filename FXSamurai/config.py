# config.py
from dotenv import load_dotenv
import os

load_dotenv()

class BrokerConfig:
    terminal_url = "https://mt5.roboforex.com"
    account      = os.getenv("mt5_account")   # номер счёта
    password     = os.getenv("mt5_password")
    server       = os.getenv("mt5_server")    # например "RoboForex-ECN"

class TelegramConfig:
    token    = os.getenv("telega")
    chat_id  = "@samurai_fx_sam"
    enabled  = True

class StrategyConfig:
    symbol     = "GBP/USD"
    interval   = "15min"
    outputsize = 1000

class ScreenConfig:
    """
    Координаты элементов в окне браузера с WebTerminal MT5.
    Запусти calibrate.py чтобы найти нужные точки.
    """
   # Шаг 1: кнопка открытия формы
    new_order_btn = (793, 193)   # заполнить через calibrate.py

    # Шаг 2: поле лота
    lot_field     = (228, 324)

    # Шаг 3: поля SL и TP
    sl_field      = (121, 400)
    tp_field      = (264, 403)

    # Шаг 4: кнопки направления
    buy_button    = (266, 557)
    sell_button   = (129, 556)

    # Шаг 5: подтверждение
    done_btn      = (187, 413)

    click_delay   = 0.5   # пауза между действиями (сек)
    lot_size      = "0.01"