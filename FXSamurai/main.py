# main.py
import time
from datetime import datetime, UTC
from strategy import (
    fetch_data,
    generate_signals,
    print_signals,
    print_last_bar,
    wait_for_candle_close,
)
from indicators import compute_indicators
from telegram_bot import TelegramNotifier
from screen_executor import login, place_order, select_symbol
from config import StrategyConfig, TelegramConfig, BrokerConfig



def run():
    login(BrokerConfig.terminal_url,
          BrokerConfig.account,
          BrokerConfig.password,
          BrokerConfig.server)
    
    # Конвертируем "GBP/USD" → "GBPUSD"
    symbol_mt5 = StrategyConfig.symbol.replace("/", "")
    select_symbol(symbol_mt5)

    telegram = TelegramNotifier() if TelegramConfig.enabled else None
    print("🚀 Мониторинг запущен. Ctrl+C — остановка.\n")

    last_signal_ts = None

    while True:
        try:
            now = datetime.now(UTC).strftime("%H:%M:%S")
            print(f"[{now}] Проверяем {StrategyConfig.symbol}...")

            df     = fetch_data(StrategyConfig.symbol,
                                StrategyConfig.interval,
                                StrategyConfig.outputsize)
            result = compute_indicators(df)
            result = generate_signals(result)

            bar    = result.iloc[[-2]]
            last   = bar.iloc[0]
            bar_ts = bar.index[0]  # ← timestamp предпоследней свечи

            

            if last["signal"] and bar_ts != last_signal_ts:  # ← проверка дубля
                last_signal_ts = bar_ts  # ← запоминаем
                print_signals(bar)

                if telegram:
                    rr = abs(last["take_profit"] - last["close"]) / abs(last["close"] - last["stop"])
                    telegram.send_signal({
                        "timestamp":   datetime.now(UTC),
                        "symbol":      StrategyConfig.symbol,   # <-- добавил
                        "direction":   last["signal"],
                        "entry":       last["close"],
                        "stop":        last["stop"],
                        "take_profit": last["take_profit"],
                        "rr_ratio":    rr,
                        "gmm_osc":     last["gmm_oscillator"],
                        "adx":         last["adx"],
                })

                place_order(last["signal"], last["stop"], last["take_profit"], symbol_mt5)

            else:
                print_last_bar(bar)

            interval_minutes = int(StrategyConfig.interval.replace("min", ""))
            wait_for_candle_close(interval_minutes)

        except KeyboardInterrupt:
            print("\n🛑 Остановлено.")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e} — повтор через 60 сек.")
            try:
                login(BrokerConfig.terminal_url,
                      BrokerConfig.account,
                      BrokerConfig.password,
                      BrokerConfig.server)
                select_symbol(StrategyConfig.symbol.replace("/", ""))
            except Exception:
                pass
            time.sleep(60)


if __name__ == "__main__":
    run()