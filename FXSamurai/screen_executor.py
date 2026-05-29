# screen_executor.py (новая версия — Selenium)
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from config import ScreenConfig
from selenium.webdriver.support.ui import Select
import platform

# ── Глобальный драйвер — создаётся один раз, живёт всю сессию ──
_driver = None

def get_driver() -> webdriver.Chrome:
    global _driver

    if _driver is not None:
        try:
            _ = _driver.current_url   # проверяем что живой
            return _driver
        except Exception:
            _driver = None

    opts = Options()

    if platform.system() != "Darwin":  # не Mac
        opts.binary_location = "/usr/bin/google-chrome"

    # На маке — с окном (чтобы видеть что происходит при тесте)
    # На VPS — раскомментируй headless:
    opts.add_argument("--headless=new")
    # opts.add_argument("--disable-gpu")  # обязательно на VPS без GPU

    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=service, options=opts)
    return _driver


def login(terminal_url: str, account: str, password: str, server: str) -> bool:
    driver = get_driver()
    wait   = WebDriverWait(driver, 20)

    driver.get(terminal_url)
    time.sleep(3)

# ── Сервер ──
    try:
        # Кликаем на текущий выбранный сервер чтобы открыть список
        current = driver.find_element(By.CSS_SELECTOR, "a.js-server-selected")
        print(f"  Текущий сервер: {current.text}")
        current.click()
        time.sleep(0.5)

        # Ищем нужный пункт по data-server
        target = driver.find_element(By.CSS_SELECTOR, f"a[data-server='{server}']")
        print(f"  Кликаем: {target.get_attribute('data-server')}")
        target.click()
        time.sleep(0.3)
    except Exception as e:
        print(f"  ⚠️ Не удалось выбрать сервер: {e}")    

    # Проверяем iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Найдено iframes: {len(iframes)}")
    for i, frame in enumerate(iframes):
        print(f"  [{i}] src='{frame.get_attribute('src')}' id='{frame.get_attribute('id')}'")

    # Если iframe есть — переключаемся в первый
    if iframes:
        driver.switch_to.frame(iframes[0])
        print("Переключились в iframe[0]")

    # Теперь ищем поля
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"input-полей после switch: {len(inputs)}")
    for inp in inputs:
        print(f"  name='{inp.get_attribute('name')}' type='{inp.get_attribute('type')}'")

    try:
        acc_field = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[name='login']")
        ))
        acc_field.clear()
        acc_field.send_keys(account)

        pwd_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        pwd_field.clear()
        pwd_field.send_keys(password)

        btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        btn.click()
        time.sleep(5)

        # ── Проверяем что залогинились ──
        # После успешного логина MT5 WebTerminal меняет URL или показывает чарт
        if "login" in driver.current_url.lower():
            print("❌ Похоже логин не прошёл — всё ещё на странице входа")
            driver.save_screenshot("login_failed.png")
            return False

        print("✅ Логин выполнен")
        return True

    except Exception as e:
        print(f"❌ Ошибка логина: {e}")
        driver.save_screenshot("login_error.png")
        return False
    finally:
        # ✅ ВСЕГДА выходим из iframe после логина
        driver.switch_to.default_content()
        print("↩️ Вернулись в main frame")

def select_symbol(symbol: str) -> bool:
    driver = get_driver()
    driver.switch_to.default_content()

    def _click_row(timeout: int = 4) -> bool:
        """Кликает по строке и ждёт класс active."""
        row = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//tr[@title='{symbol}']")
            )
        )
        row.click()
        # Ждём подтверждения — появление класса active
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//tr[@title='{symbol}' and contains(@class,'active')]")
            )
        )
        return True

    # ── 1. Пробуем в главном фрейме ──
    try:
        _click_row()
        print(f"✅ Выбрана пара: {symbol} (main frame)")
        time.sleep(0.5)
        return True
    except Exception:
        pass

    # ── 2. Сканируем все iframe ──
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"  🔍 Ищем {symbol} в {len(iframes)} iframe...")


    for i, frame in enumerate(iframes):
        try:
            driver.switch_to.frame(frame)
            _click_row()
            print(f"✅ Выбрана пара: {symbol} (iframe[{i}])")
            driver.switch_to.default_content()
            time.sleep(0.5)
            return True
        except Exception:
            driver.switch_to.default_content()  # сбрасываем перед следующим


    print(f"❌ Не удалось выбрать пару {symbol}")
    driver.save_screenshot(f"select_{symbol}_failed.png")
    return False

def _clear_and_type(driver, selector: str, value: str):
    """Очищает поле и вводит значение."""
    field = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    field.click()
    field.send_keys(Keys.CONTROL + "a")
    field.send_keys(Keys.DELETE)
    field.send_keys(value)
    time.sleep(0.2)

def _switch_to_terminal() -> bool:
    """Переключается в iframe терминала MT5."""
    driver = get_driver()
    driver.switch_to.default_content()

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for i, frame in enumerate(iframes):
        try:
            driver.switch_to.frame(frame)
            # Проверяем что это терминал — есть Market Watch
            driver.find_element(By.CSS_SELECTOR, "div.market-watch")
            print(f"  ↪️ Терминал найден в iframe[{i}]")
            return True
        except Exception:
            driver.switch_to.default_content()

    print("  ❌ iframe терминала не найден")
    return False


def place_order(direction: str, stop: float, take_profit: float, symbol: str = None) -> bool:
    driver = get_driver()
    wait   = WebDriverWait(driver, 15)

    driver.switch_to.default_content()

    if symbol:
        select_symbol(symbol)
        time.sleep(0.5)

    _switch_to_terminal()

    try:
        # ── 1. Кнопка New Order ──
        new_order = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class,'icon-button') and .//span[text()='New Order']]")
        ))
        new_order.click()
        time.sleep(1.5)

        # ── 2. Volume — первый input внутри div.volume ──
        vol_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.volume input[type='text']")
        ))
        vol_input.click()
        # ── 2. Volume ──
        vol_input.send_keys(Keys.CONTROL + "a")
        vol_input.send_keys(str(ScreenConfig.lot_size))  # ✅ явное приведение к строке
        time.sleep(0.3)

        # ── 3. Stop Loss — input внутри div.sl ──
        sl_input = driver.find_element(By.CSS_SELECTOR, "div.sl input[type='text']")
        sl_input.click()
        sl_input.send_keys(Keys.CONTROL + "a")
        sl_input.send_keys(f"{stop:.5f}")
        time.sleep(0.3)

        # ── 4. Take Profit — input внутри div.tp ──
        tp_input = driver.find_element(By.CSS_SELECTOR, "div.tp input[type='text']")
        tp_input.click()
        tp_input.send_keys(Keys.CONTROL + "a")
        tp_input.send_keys(f"{take_profit:.5f}")
        time.sleep(0.3)

        # ── 5. Buy или Sell ──
        if direction == "LONG":
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class,'trade-button') and text()='Buy by Market']")
            ))
        else:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class,'trade-button') and text()='Sell by Market']")
            ))
        btn.click()
        time.sleep(1)

        # ── 6. OK ──
        try:
            ok_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'footer')]//button[text()='OK']")
            ))
            ok_btn.click()
            print(f"✅ Ордер {direction} выставлен")
        except Exception:
            print(f"✅ Ордер {direction} выставлен (без OK-диалога)")

        return True

    except Exception as e:
        print(f"❌ Ошибка place_order: {e}")
        try:
            driver.save_screenshot("error_screenshot.png")
            print("   Скриншот: error_screenshot.png")
        except Exception:
            pass
        return False