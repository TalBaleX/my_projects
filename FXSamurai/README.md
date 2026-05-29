indicators.py — не трогаем
strategy.py — не трогаем  
config.py — упрощён
telegram_bot.py — починен
screen_executor.py — новый
main.py — переписан
calibrate.py — разовый инструмент

pip install pyautogui pyperclip twelvedata python-dotenv requests pandas numpy selenium webdriver-manager

Остальные файлы — это модули, их не запускают напрямую:

indicators.py — математика, вызывается из strategy.py
strategy.py — данные и сигналы, вызывается из main.py
config.py — настройки, читается всеми
telegram_bot.py — отправка, вызывается из main.py
screen_executor.py — клики, вызывается из main.py

# Системные пакеты

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-pip python3.11-venv
wget curl unzip git
chromium-browser chromium-chromedriver

# Виртуальное окружение

python3.11 -m venv venv
source venv/bin/activate
pip install selenium webdriver-manager twelvedata python-dotenv requests

sudo systemctl daemon-reload
sudo systemctl enable tradingbot
sudo systemctl start tradingbot
sudo systemctl stop tradingbot

sudo systemctl restart tradingbot.service
sudo systemctl status tradingbot.service

# Смотреть логи:

journalctl -u tradingbot -f

# Убедись что Chrome запускается

chromium-browser --headless --dump-dom https://example.com | head -20

# Запусти бот вручную первый раз чтобы увидеть ошибки

source venv/bin/activate
python main.py

apikey=apitwelvedata
telega=telega
mt5_account=account
mt5_password=passwort
mt5_server=RoboForex-ECN
