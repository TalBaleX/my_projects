"""
Forex ADX Analyzer
Режимы: LIVE (запуск ~14:20 Berlin) и BACKTEST (диапазон дат)
Таймфрейм: 15m | Сессия: Нью-Йорк (13:00–22:00 UTC)
Результаты сохраняются в CSV
"""

from twelvedata import TDClient
from dotenv import load_dotenv
import os
import pandas as pd
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from typing import Optional, List
import pytz
import time as time_module
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

# ──────────────────────────────────────────────────────────
# КОНФИГ
# ──────────────────────────────────────────────────────────
SYMBOLS = ["EUR/JPY", "EUR/USD", "GBP/JPY", "GBP/USD",
           "USD/CAD", "USD/CHF", "USD/JPY", "XAU/USD"]

# Twelve Data принимает символы и со слешем и без, но лучше явно указать
# Оставляем как есть, API сам сконвертирует

ADX_PERIOD   = 14
ADX_WINDOW   = 5          # ±5 свечей вокруг экстремума ADX
TF           = "15min"

BERLIN_TZ    = pytz.timezone("Europe/Berlin")
UTC_TZ       = pytz.utc

# Нью-Йоркская сессия: 13:00–22:00 UTC (= 08:00–17:00 ET)
NY_OPEN_UTC  = 13
NY_CLOSE_UTC = 22

# Бектест — диапазон дат (включительно)
BT_START = date(2026, 5, 2)
BT_END   = date(2026, 5, 2)

# Время среза для бектеста и лайва (Berlin)
ANALYSIS_TIME_BERLIN = "14:20"   # HH:MM

# Задержки между запросами (в секундах)
DELAY_BETWEEN_SYMBOLS = 0.5   # между символами
DELAY_BETWEEN_DAYS = 90       # между днями в бектесте (90 секунд = 1.5 минуты)

# ──────────────────────────────────────────────────────────
# DATACLASSES
# ──────────────────────────────────────────────────────────
@dataclass
class ADXLevel:
    date: str                # дата анализа (YYYY-MM-DD)
    symbol: str              # символ
    candle_time: datetime    # время свечи
    adx_value: float
    price_high: float
    price_low: float
    price_close: float
    kind: str                # "local_max" | "local_min"
    price_label: str         # "price_high" | "price_low" | "price_mid"
    divergence: str          # описание закономерности
    
    def to_dict(self):
        d = asdict(self)
        d['candle_time'] = d['candle_time'].strftime('%Y-%m-%d %H:%M:%S')
        return d

# ──────────────────────────────────────────────────────────
# TWELVEDATA — получение свечей
# ──────────────────────────────────────────────────────────

def get_td_client() -> TDClient:
    api_key = os.getenv("TWELVEDATA_API_KEY", "")
    if not api_key:
        raise ValueError("TWELVEDATA_API_KEY не найден в .env")
    return TDClient(apikey=api_key)


def fetch_candles(td: TDClient, symbol: str, start_dt: datetime, end_dt: datetime) -> Optional[pd.DataFrame]:
    """
    Загружает 15-минутные свечи за диапазон [start_dt, end_dt] (UTC).
    Возвращает DataFrame с колонками: datetime, open, high, low, close, volume.
    """
    try:
        # Twelve Data принимает символы как есть, с / или без
        ts = td.time_series(
            symbol=symbol,
            interval=TF,
            start_date=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_date=end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            timezone="UTC",
            outputsize=500,
        )
        df = ts.as_pandas()
        if df is None or df.empty:
            return None
        df = df.sort_index()
        df.index = pd.to_datetime(df.index, utc=True)
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception as e:
        # Молчим об ошибках, чтобы не спамить
        return None

# ──────────────────────────────────────────────────────────
# ADX CALCULATION
# ──────────────────────────────────────────────────────────

def calc_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.Series:
    high  = df["high"]
    low   = df["low"]
    close = df["close"]

    tr  = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)

    dm_plus  = high.diff()
    dm_minus = -low.diff()
    dm_plus  = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0.0)
    dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0.0)

    atr    = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    di_p   = 100 * dm_plus.ewm(alpha=1/period, min_periods=period, adjust=False).mean() / atr
    di_m   = 100 * dm_minus.ewm(alpha=1/period, min_periods=period, adjust=False).mean() / atr

    dx     = 100 * (di_p - di_m).abs() / (di_p + di_m).replace(0, 1)
    adx    = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return adx.rename("adx")

# ──────────────────────────────────────────────────────────
# ПОИСК ЭКСТРЕМУМОВ ADX + АНАЛИЗ ЦЕНЫ
# ──────────────────────────────────────────────────────────

def find_adx_extremes(df: pd.DataFrame, adx: pd.Series, symbol: str, target_date: str, window: int = ADX_WINDOW) -> List[ADXLevel]:
    """
    Ищет локальные максимумы и минимумы ADX.
    Для каждого экстремума определяет, что делала цена в этот момент.
    """
    results: List[ADXLevel] = []
    n = len(adx)
    adx_vals = adx.values
    idx      = adx.index

    for i in range(window, n - window):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        seg = adx_vals[lo:hi]
        cur = adx_vals[i]

        is_max = cur == seg.max() and cur > adx_vals[i-1] and cur > adx_vals[i+1]
        is_min = cur == seg.min() and cur < adx_vals[i-1] and cur < adx_vals[i+1]

        if not (is_max or is_min):
            continue

        kind = "local_max" if is_max else "local_min"

        # Цена в ±window свечей
        price_window = df.iloc[lo:hi]
        candle       = df.iloc[i]
        p_high       = price_window["high"].max()
        p_low        = price_window["low"].min()
        candle_mid   = (candle["high"] + candle["low"]) / 2
        range_size   = p_high - p_low if p_high != p_low else 1

        # Где цена в момент экстремума ADX относительно диапазона окна
        rel = (candle_mid - p_low) / range_size  # 0=низ, 1=верх

        if rel >= 0.65:
            price_label = "price_high"
        elif rel <= 0.35:
            price_label = "price_low"
        else:
            price_label = "price_mid"

        # Анализ закономерности
        divergence = _classify_pattern(kind, price_label, adx_vals, df, i, window)

        results.append(ADXLevel(
            date=target_date,
            symbol=symbol,
            candle_time=idx[i].to_pydatetime(),
            adx_value=round(float(cur), 2),
            price_high=round(float(candle["high"]), 5),
            price_low=round(float(candle["low"]), 5),
            price_close=round(float(candle["close"]), 5),
            kind=kind,
            price_label=price_label,
            divergence=divergence,
        ))

    return results


def _classify_pattern(kind: str, price_label: str,
                      adx_vals, df: pd.DataFrame, i: int, window: int) -> str:
    """
    Классифицирует рыночный паттерн на основе позиции ADX и цены.
    """
    if kind == "local_max":
        # Высокий ADX = сильный тренд
        if price_label == "price_high":
            return "Бычий тренд: высокий ADX + цена вверху → тренд в силе"
        elif price_label == "price_low":
            return "Медвежий тренд: высокий ADX + цена внизу → тренд в силе"
        else:
            return "Высокий ADX, цена в середине → возможна консолидация после тренда"

    else:  # local_min
        # Низкий ADX = слабый тренд / накопление
        # Смотрим направление движения цены вокруг этого минимума ADX
        lo = max(0, i - window)
        hi = min(len(df), i + window + 1)
        prices_close = df["close"].values[lo:hi]
        price_start  = prices_close[0]
        price_end    = prices_close[-1]
        trend_dir    = "up" if price_end > price_start else "down"

        if price_label == "price_high":
            if trend_dir == "up":
                return "Дивергенция: ADX min + цена на хае → возможный разворот вниз (слабеющий бычий тренд)"
            else:
                return "ADX min + цена на хае но движение вниз → медвежье давление при слабом тренде"
        elif price_label == "price_low":
            if trend_dir == "down":
                return "Дивергенция: ADX min + цена на лое → возможный разворот вверх (слабеющий медвежий тренд)"
            else:
                return "ADX min + цена на лое но движение вверх → бычье давление при слабом тренде"
        else:
            return "ADX min + цена в середине → флет/накопление, жди пробоя"

# ──────────────────────────────────────────────────────────
# ФОРМАТИРОВАНИЕ ВЫВОДА (только для консоли, минимум спама)
# ──────────────────────────────────────────────────────────

def print_progress(current_day: int, total_days: int, symbol_index: int, total_symbols: int):
    """Печатает прогресс без спама"""
    if symbol_index == 0:
        print(f"  День {current_day}/{total_days} | Обработка: {symbol_index+1}/{total_symbols}", end="", flush=True)
    else:
        print(f"\r  День {current_day}/{total_days} | Обработка: {symbol_index+1}/{total_symbols}", end="", flush=True)

# ──────────────────────────────────────────────────────────
# СОХРАНЕНИЕ В CSV
# ──────────────────────────────────────────────────────────

def save_to_csv(all_results: List[ADXLevel], filename: str = "adx_analysis_results.csv"):
    """Сохраняет результаты в CSV файл"""
    if not all_results:
        print("\n  Нет результатов для сохранения")
        return
    
    df = pd.DataFrame([r.to_dict() for r in all_results])
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"\n  Результаты сохранены в {filename} (всего записей: {len(df)})")

# ──────────────────────────────────────────────────────────
# АНАЛИЗ ДНЯ
# ──────────────────────────────────────────────────────────

def analyze_day(td: TDClient, target_date: date, day_index: int, total_days: int, 
                all_results: List[ADXLevel], verbose: bool = False) -> List[ADXLevel]:
    """Анализирует все пары за один торговый день и возвращает результаты"""
    
    # Временной диапазон: 00:00 Berlin → ANALYSIS_TIME_BERLIN Berlin
    berlin_start = BERLIN_TZ.localize(
        datetime.combine(target_date, datetime.strptime("00:00", "%H:%M").time())
    ).astimezone(UTC_TZ)

    berlin_end = BERLIN_TZ.localize(
        datetime.combine(target_date, datetime.strptime(ANALYSIS_TIME_BERLIN, "%H:%M").time())
    ).astimezone(UTC_TZ)

    if verbose:
        print(f"\n{'═'*70}")
        print(f"  ДАТА: {target_date.strftime('%d.%m.%Y (%A)')}")
        print(f"{'═'*70}")
    
    day_results = []
    
    for sym_idx, symbol in enumerate(SYMBOLS):
        # Показываем прогресс
        print_progress(day_index, total_days, sym_idx, len(SYMBOLS))
        
        df = fetch_candles(td, symbol, berlin_start, berlin_end)
        
        if df is None or len(df) < ADX_PERIOD * 2:
            time_module.sleep(DELAY_BETWEEN_SYMBOLS)
            continue
        
        adx = calc_adx(df)
        levels = find_adx_extremes(df, adx, symbol, target_date.strftime("%Y-%m-%d"))
        
        if levels:
            day_results.extend(levels)
            if verbose and levels:
                print(f"\n  {symbol}: найдено {len(levels)} экстремумов")
        
        # Пауза между символами
        time_module.sleep(DELAY_BETWEEN_SYMBOLS)
    
    if day_results:
        all_results.extend(day_results)
        if verbose:
            print(f"\n  Итого за день: {len(day_results)} сигналов")
    
    return day_results

# ──────────────────────────────────────────────────────────
# РЕЖИМ LIVE
# ──────────────────────────────────────────────────────────

def run_live():
    print("\n" + "█"*70)
    print("  РЕЖИМ: LIVE (результаты в консоль + CSV)")
    print("█"*70)
    
    td = get_td_client()
    today = datetime.now(BERLIN_TZ).date()
    
    all_results = []
    analyze_day(td, today, 1, 1, all_results, verbose=True)
    
    if all_results:
        save_to_csv(all_results, f"adx_live_{today.strftime('%Y%m%d')}.csv")
    else:
        print("\n  Сигналов не найдено")

# ──────────────────────────────────────────────────────────
# РЕЖИМ BACKTEST
# ──────────────────────────────────────────────────────────

def run_backtest(start: date = BT_START, end: date = BT_END):
    print("\n" + "█"*70)
    print(f"  РЕЖИМ: BACKTEST  {start.strftime('%d.%m.%Y')} → {end.strftime('%d.%m.%Y')}")
    print(f"  Задержка между днями: {DELAY_BETWEEN_DAYS} секунд")
    print("█"*70)
    
    td = get_td_client()
    
    # Собираем все даты для анализа (пропуская выходные)
    all_dates = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Пн-Пт
            all_dates.append(current)
        current += timedelta(days=1)
    
    total_days = len(all_dates)
    print(f"\n  Всего торговых дней для анализа: {total_days}\n")
    
    all_results: List[ADXLevel] = []
    
    for day_idx, target_date in enumerate(all_dates, 1):
        print(f"\n  Обработка: {target_date.strftime('%Y-%m-%d')} ({day_idx}/{total_days})")
        
        analyze_day(td, target_date, day_idx, total_days, all_results, verbose=False)
        
        # Пауза между днями
        if day_idx < total_days:
            print(f"\n  Ожидание {DELAY_BETWEEN_DAYS} секунд перед следующим днём...")
            for remaining in range(DELAY_BETWEEN_DAYS, 0, -1):
                print(f"\r  Следующий день через: {remaining} секунд", end="", flush=True)
                time_module.sleep(1)
            print("\r" + " " * 50 + "\r", end="")  # очищаем строку
    
    print("\n" + "═"*70)
    print(f"  АНАЛИЗ ЗАВЕРШЁН")
    print(f"  Найдено сигналов: {len(all_results)}")
    print("═"*70)
    
    if all_results:
        # Сохраняем в CSV
        filename = f"adx_backtest_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.csv"
        save_to_csv(all_results, filename)
        
        # Показываем статистику по типам сигналов
        df_stats = pd.DataFrame([r.to_dict() for r in all_results])
        print("\n  Статистика по типам сигналов:")
        print(f"    Всего локальных максимумов ADX: {len(df_stats[df_stats['kind'] == 'local_max'])}")
        print(f"    Всего локальных минимумов ADX: {len(df_stats[df_stats['kind'] == 'local_min'])}")
        print(f"\n    Топ-5 символов по активности:")
        print(df_stats['symbol'].value_counts().head().to_string())
    else:
        print("\n  Сигналов не найдено за весь период")

# ──────────────────────────────────────────────────────────
# ТОЧКА ВХОДА
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "live"
    
    if mode == "live":
        run_live()
    
    elif mode == "backtest":
        # Опционально: python forex_analyzer.py backtest 2026-04-01 2026-05-02
        if len(sys.argv) >= 4:
            s = date.fromisoformat(sys.argv[2])
            e = date.fromisoformat(sys.argv[3])
        else:
            s, e = BT_START, BT_END
        run_backtest(s, e)
    
    else:
        print(f"Неизвестный режим: {mode}. Используй: live | backtest")
        sys.exit(1)