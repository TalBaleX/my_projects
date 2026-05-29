# strategy.py

from twelvedata import TDClient
from dotenv import load_dotenv
import os
import pandas as pd
from indicators import compute_indicators
import time
from datetime import datetime, UTC

load_dotenv()

# ══════════════════════════════════════════════════════════════════
#  ЗАГРУЗКА ДАННЫХ
# ══════════════════════════════════════════════════════════════════

def fetch_data(symbol: str = "GBP/USD", interval: str = "15min", outputsize: int = 1000) -> pd.DataFrame:
    td = TDClient(apikey=os.getenv("apikey"))
    ts = td.time_series(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
        timezone="Europe/Berlin",
    )
    df = ts.as_pandas().sort_index(ascending=True)
    df["volume"] = 1.0  # заглушка для форекс
    return df


# ══════════════════════════════════════════════════════════════════
#  ГЕНЕРАЦИЯ СИГНАЛОВ
# ══════════════════════════════════════════════════════════════════

def generate_signals(result: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет колонку 'signal' к результату compute_indicators:
        'LONG'  — осциллятор перешёл из отрицательного в положительный + ema_200 < close
        'SHORT' — осциллятор перешёл из положительного в отрицательного + ema_200 > close
        None    — нет сигнала

    Также добавляет колонки stop и take_profit под каждый сигнал.
    """
    osc   = result["gmm_oscillator"]
    close = result["close"]
    ema   = result["ema_200"]
    upper = result["upper_atr"]
    lower = result["lower_atr"]

    prev_osc = osc.shift(1)

    # Сдвиг знака осциллятора
    crossed_up   = (prev_osc < 0) & (osc >= 0)   # отрицательный → положительный
    crossed_down = (prev_osc >= 0) & (osc < 0)   # положительный → отрицательный

    # Условия фильтрации по EMA
    trend_up   = close > ema   # цена выше EMA — бычий контекст
    trend_down = close < ema   # цена ниже EMA — медвежий контекст

    long_cond  = crossed_up   & trend_up
    short_cond = crossed_down & trend_down

    result = result.copy()
    result["signal"]      = None
    result["stop"]        = float("nan")
    result["take_profit"] = float("nan")

    result.loc[long_cond,  "signal"]      = "LONG"
    result.loc[long_cond,  "stop"]        = lower[long_cond]
    result.loc[long_cond,  "take_profit"] = upper[long_cond]

    result.loc[short_cond, "signal"]      = "SHORT"
    result.loc[short_cond, "stop"]        = upper[short_cond]
    result.loc[short_cond, "take_profit"] = lower[short_cond]

    return result


# ══════════════════════════════════════════════════════════════════
#  ВЫВОД СИГНАЛОВ В КОНСОЛЬ
# ══════════════════════════════════════════════════════════════════

def print_signals(result: pd.DataFrame, last_n: int = None) -> None:
    """
    Печатает все сигналы (или последние last_n сигналов) в читаемом виде.
    """
    signals = result[result["signal"].notna()].copy()

    if signals.empty:
        print("Сигналов не найдено.")
        return

    if last_n is not None:
        signals = signals.tail(last_n)

    print(f"\n{'='*62}")
    print(f"  ТОРГОВЫЕ СИГНАЛЫ  ({len(signals)} шт.)")
    print(f"{'='*62}")

    for ts, row in signals.iterrows():
        direction = row["signal"]
        arrow     = "▲ LONG " if direction == "LONG" else "▼ SHORT"
        rr        = abs(row["take_profit"] - row["close"]) / abs(row["close"] - row["stop"])

        print(
            f"\n{arrow}  {ts}\n"
            f"  Вход  (close):      {row['close']:.5f}\n"
            f"  Стоп:               {row['stop']:.5f}\n"
            f"  Тейк:               {row['take_profit']:.5f}\n"
            f"  GMM осциллятор:     {row['gmm_oscillator']:.4f}\n"
            f"  EMA 200:            {row['ema_200']:.5f}\n"
            f"  R:R:                1 : {rr:.2f}"
        )

    print(f"\n{'='*62}\n")


def print_last_bar(result: pd.DataFrame) -> None:
    """
    Отдельно выводит состояние последней свечи — удобно при live-мониторинге.
    """
    row = result.iloc[-1]
    ts  = result.index[-1]
    sig = row["signal"] if row["signal"] else "—"

    print(f"\n--- Последняя свеча: {ts} ---")
    print(f"  Close:          {row['close']:.5f}")
    print(f"  EMA 200:        {row['ema_200']:.5f}")
    print(f"  GMM осц.:       {row['gmm_oscillator']:.4f}  (режим {int(row['gmm_regime'])})")
    print(f"  Upper ATR:      {row['upper_atr']:.5f}")
    print(f"  Lower ATR:      {row['lower_atr']:.5f}")
    print(f"  ADX:            {row['adx']:.2f}")
    print(f"  Сигнал:         {sig}")


def wait_for_candle_close(interval_minutes: int = 15) -> None:
    """Спит до закрытия текущей свечи + 5 секунд (чтобы данные успели обновиться)."""
    now = datetime.now(UTC)
    seconds_passed = (now.minute % interval_minutes) * 60 + now.second
    seconds_to_wait = interval_minutes * 60 - seconds_passed + 120
    print(f"  Следующая проверка через {seconds_to_wait // 60}м {seconds_to_wait % 60}с ...")
    time.sleep(seconds_to_wait)

