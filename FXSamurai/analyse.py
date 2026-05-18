# analyse.py (test 1.0.0)
# 1m чисто прайс экшн внутри 5m

from twelvedata import TDClient
from dotenv import load_dotenv
import os

from dataclasses import dataclass
from datetime import datetime
from datetime import datetime, timedelta
import time

import pandas as pd


load_dotenv()

# # Initialize client with your API key
td = TDClient(apikey=os.getenv("apikey"))




@dataclass
class Candle:
    t: datetime
    o: float
    h: float
    l: float
    c: float
    rsi: float | None = None
    stc: float | None = None

candles: list[Candle]

def fetch_candles(symbol: str, interval="1min", outputsize=10) -> list[Candle]:
    data = td.time_series(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
        timezone="Europe/Berlin",
        order="ASC",  # чтобы были от старых к новым
    ).as_json()
    
    if isinstance(data, tuple):
        values = list(data)
    elif isinstance(data, list):
        values = data
    else:
        values = data.get("values", [])

    candles = []
    for r in values:
        candles.append(Candle(
            t=datetime.fromisoformat(r["datetime"]),
            o=float(r["open"]),
            h=float(r["high"]),
            l=float(r["low"]),
            c=float(r["close"]),
        ))
    return candles

def _floor_time(t: datetime, tf: str) -> datetime:
    if tf.endswith("m"):
        n = int(tf[:-1])
        minute = (t.minute // n) * n
        return t.replace(minute=minute, second=0, microsecond=0)
    if tf.endswith("h"):
        n = int(tf[:-1])
        hour = (t.hour // n) * n
        return t.replace(hour=hour, minute=0, second=0, microsecond=0)
    if tf == "1w":
        # неделя с понедельника 00:00
        start = t - timedelta(days=t.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if tf == "1mo":
        return t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown timeframe: {tf}")

def aggregate_by_timeframe(candles: list[Candle], tf: str) -> list[Candle]:
    if not candles:
        return []

    # важно: ожидаем, что candles отсортированы по времени по возрастанию
    out = []
    cur_bucket = None
    cur = None

    for c in candles:
        bucket = _floor_time(c.t, tf)
        if cur_bucket != bucket:
            if cur is not None:
                out.append(cur)
            cur_bucket = bucket
            cur = Candle(t=bucket, o=c.o, h=c.h, l=c.l, c=c.c)
        else:
            cur.h = max(cur.h, c.h)
            cur.l = min(cur.l, c.l)
            cur.c = c.c

    if cur is not None:
        out.append(cur)

    return out

def attach_indicators(candles: list[Candle]) -> list[Candle]:
    if not candles:
        return candles

    df = pd.DataFrame([{
        "t": c.t, "o": c.o, "h": c.h, "l": c.l, "c": c.c
    } for c in candles]).set_index("t")

    # RSI 14
    delta = df["c"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # STC 23,50,10,3,3
    ema_fast = df["c"].ewm(span=23, adjust=False).mean()
    ema_slow = df["c"].ewm(span=50, adjust=False).mean()
    macd = ema_fast - ema_slow

    low = macd.rolling(10).min()
    high = macd.rolling(10).max()
    k = 100 * (macd - low) / (high - low)
    k = k.fillna(0)

    d1 = k.ewm(span=3, adjust=False).mean()

    low2 = d1.rolling(10).min()
    high2 = d1.rolling(10).max()
    k2 = 100 * (d1 - low2) / (high2 - low2)
    k2 = k2.fillna(0)

    df["stc"] = k2.ewm(span=3, adjust=False).mean()

    # переносим обратно в свечи
    for c in candles:
        c.rsi = None if pd.isna(df.at[c.t, "rsi"]) else float(df.at[c.t, "rsi"])
        c.stc = None if pd.isna(df.at[c.t, "stc"]) else float(df.at[c.t, "stc"])

    return candles


# FACTORS


def factor_week_trend(candles1W):
    last = candles1W[-1]
    max = last.h
    min = last.l
    if max - last.c > last.c - min:
        return 1.1
    elif max - last.c < last.c - min:
        return 0.9
    else:
        return 1.0

def factor_week_trend_rsi(candles1W):
    last = candles1W[-1]
    if (70 - last.rsi) > (last.rsi - 30):
        return 1.1
    elif (70 - last.rsi) < (last.rsi - 30):
        return 0.9
    else:
        return 1.0
    
def factor_week_trend_stc(candles1W):
    last = candles1W[-1]
    if ((75 - last.stc) > (last.stc - 25)):
        return 1.1
    elif ((75 - last.stc) < (last.stc - 25)):
        return 0.9
    else:
        return 1.0
    

    
def factor_hour_trend(candles1H):
    last = candles1H[-1]
    max = last.h
    min = last.l
    if max - last.c > last.c - min:
        return 1.1
    elif max - last.c < last.c - min:
        return 0.9
    else:
        return 1.0

def factor_hour_trend_rsi(candles1H):
    last = candles1H[-1]
    if (70 - last.rsi) > (last.rsi - 30):
        return 1.1
    elif (70 - last.rsi) < (last.rsi - 30):
        return 0.9
    else:
        return 1.0
    
def factor_hour_trend_stc(candles1H):
    last = candles1H[-1]
    if ((75 - last.stc) > (last.stc - 25)):
        return 1.1
    elif ((75 - last.stc) < (last.stc - 25)):
        return 0.9
    else:
        return 1.0



def factor_5m_trend(candles5m):
    last = candles5m[-1]
    max = last.h
    min = last.l
    if max - last.c > last.c - min:
        return 1.1
    elif max - last.c < last.c - min:
        return 0.9
    else:
        return 1.0

def factor_5m_trend_rsi(candles5m):
    last = candles5m[-1]
    if (70 - last.rsi) > (last.rsi - 30):
        return 1.1
    elif (70 - last.rsi) < (last.rsi - 30):
        return 0.9
    else:
        return 1.0
    
def factor_5m_trend_stc(candles5m):
    last = candles5m[-1]
    if ((75 - last.stc) > (last.stc - 25)):
        return 1.1
    elif ((75 - last.stc) < (last.stc - 25)):
        return 0.9
    else:
        return 1.0
    

def factor_1m_trend(candles5m):
    last = candles5m[-1]
    max = last.h
    min = last.l
    if max - last.c > last.c - min:
        return 1.1
    elif max - last.c < last.c - min:
        return 0.9
    else:
        return 1.0

def factor_1m_trend_rsi(candles1m):
    last = candles1m[-1]
    if (70 - last.rsi) > (last.rsi - 30):
        return 1.1
    elif (70 - last.rsi) < (last.rsi - 30):
        return 0.9
    else:
        return 1.0
    
def factor_1m_trend_stc(candles1m):
    last = candles1m[-1]
    if ((75 - last.stc) > (last.stc - 25)):
        return 1.1
    elif ((75 - last.stc) < (last.stc - 25)):
        return 0.9
    else:
        return 1.0






def compute_trade_coef(candles1W, candles1H, candles5m, candles1m):
    coef = 1.0
    coef *= factor_week_trend(candles1W)
    coef *= factor_week_trend_rsi(candles1W)
    coef *= factor_week_trend_stc(candles1W)
    coef *= factor_hour_trend(candles1H)
    coef *= factor_hour_trend_rsi(candles1H)
    coef *= factor_hour_trend_stc(candles1H)
    coef *= factor_5m_trend(candles5m)
    coef *= factor_5m_trend_rsi(candles5m)
    coef *= factor_5m_trend_stc(candles5m)
    coef *= factor_1m_trend(candles1m)
    coef *= factor_1m_trend_rsi(candles1m)
    coef *= factor_1m_trend_stc(candles1m)
    dt = datetime.strptime(str(candles1m[-1].t), "%Y-%m-%d %H:%M:%S")
    dt_plus_one = dt + timedelta(minutes=2)

    # Получаем только часы и минуты
    result = dt_plus_one.strftime("%H:%M")
    if coef > 1:
        return "LONG", coef, result
    if coef < 1:
        return "SHORT", coef,result
    return "NEUTRAL", coef, result


def get_asset(asset_name: str):
    if not asset_name:
        print("[ANALYSE] asset_name пустой")
        return
    symbol = asset_name.replace(" ", "").upper()  # например "EUR / USD OTC" -> "EUR/USD OTC"

    candles1m = attach_indicators(fetch_candles(symbol, "1min", 2000))
    candles5m = attach_indicators(aggregate_by_timeframe(candles1m, "5m"))

    candles1H = attach_indicators(fetch_candles(symbol, "1h", 2000))
    candles4H = attach_indicators(aggregate_by_timeframe(candles1H, "4h"))

    candles1D = attach_indicators(fetch_candles(symbol, "1day", 1000))
    candles1W = attach_indicators(aggregate_by_timeframe(candles1D, "1w"))
    candles1M = attach_indicators(aggregate_by_timeframe(candles1D, "1mo"))
    result = compute_trade_coef(candles1W, candles1H, candles5m, candles1m)
    print(result, symbol)
    
    # Запись в файл
    with open("trading_signals.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} | {result} | {symbol}\n")

