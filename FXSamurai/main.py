# main.py
import time
from datetime import datetime
import platform
import pyautogui
import bot_config
from risk import RiskManager
from ocr import read_balance, read_text
import analyse

pyautogui.FAILSAFE = True

print("Запуск через 5 секунд...")
time.sleep(5)

def wait_until_second(target_second=31):
    while True:
        now = datetime.now()
        if now.second == target_second:
            return
        time.sleep(0.05)

# start_balance = None
# for _ in range(5):
#     start_balance = read_balance(bot_config.BALANCE_REGION, prev_balance=start_balance)
#     if start_balance is not None:
#         break
#     time.sleep(0.5)

# if start_balance is None:
#     print("Ошибка OCR после 5 попыток. Проверь BALANCE_REGION и ocr_debug/.")
#     raise SystemExit(1)

# rm = RiskManager(
#     start_balance=start_balance,
#     risk_percent=bot_config.RISK_PERCENT,
#     stop_loss_ratio=bot_config.STOP_LOSS_RATIO,
#     min_trade=bot_config.MIN_TRADE,
#     base_x=bot_config.BASE_X,
#     multiplier=bot_config.MULTIPLIER,
#     checkpoint_stop_ratio=getattr(bot_config, "CHECKPOINT_STOP_RATIO", 0.83),
# )
# last_balance = start_balance

# print(f"Стартовый баланс: {start_balance}")

try:
    while True:
        # balance = read_balance(bot_config.BALANCE_REGION, prev_balance=last_balance)
        # print("Баланс:", balance)

        # if balance is None:
        #     print("[OCR WARN] Невалидное чтение, пропуск итерации")
        #     time.sleep(1)
        #     continue

        # if rm.should_stop(balance):
        #     print("STOP: риск-лимит")
        #     break

        # rm.update_checkpoint(balance)
        # amount = rm.trade_amount(balance)
        # print(f"Сумма сделки: {amount}")

        # pyautogui.click(bot_config.AMOUNT_FIELD)
        # if platform.system() == "Darwin":
        #     pyautogui.hotkey("command", "a")
        # else:
        #     pyautogui.hotkey("ctrl", "a")
        # pyautogui.press("backspace")
        # pyautogui.write(f"{amount:.2f}")

        # pyautogui.click(bot_config.BUY_BUTTON)  # стратегия решает BUY/SELL

        # last_balance = balance
        wait_until_second(31)

        try:
            asset = read_text(bot_config.ASSET_TOP_FOREX)
            print("Инструмент:", asset)

            analyse.get_asset(asset)

        except Exception as e:
            print("[ERROR LOOP]", e)

        # маленькая защита от двойного запуска в одну секунду
        time.sleep(bot_config.TRADE_DURATION)

except pyautogui.FailSafeException:
    print("Остановлено FAILSAFE (курсор в углу экрана).")
except KeyboardInterrupt:
    print("Остановлено пользователем.")
except Exception as e:
    print(f"[FATAL] Необработанная ошибка: {e}")
finally:
    print("Бот завершил работу.")
