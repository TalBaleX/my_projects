
"""
╔══════════════════════════════════════════════════════════════════╗
║           SMC BACKTEST ENGINE – Python Port                      ║
║   Ported from: 🔱 AETHER FLOW SYSTEM (Pine Script v6)           ║
║   Logic: Order Blocks + FVG + Chandelier Exit + PDH/PDL          ║
║   Session: NY only (9:30–16:00 ET)                               ║
╚══════════════════════════════════════════════════════════════════╝
"""
 
from twelvedata import TDClient
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import pytz
import warnings
warnings.filterwarnings("ignore")
 
load_dotenv()
td = TDClient(apikey=os.getenv("apikey"))
 
NY_TZ = pytz.timezone("America/New_York")
BERLIN_TZ = pytz.timezone("Europe/Berlin")
 
 
# ══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════
 
@dataclass
class Candle:
    t: datetime
    o: float
    h: float
    l: float
    c: float
    v: float = 0.0
 
@dataclass
class OrderBlock:
    top: float
    btm: float
    avg: float
    t: datetime
    is_bull: bool
    mitigated: bool = False
 
@dataclass
class FVG:
    top: float
    btm: float
    is_bull: bool
    t: datetime
    mitigated: bool = False
 
@dataclass
class Signal:
    t: datetime                    # время сигнала (Berlin)
    direction: str                 # LONG / SHORT
    entry: float
    stop: float
    take_profit: float             # PDL или PDH
    atr: float
    ob_used: Optional[OrderBlock]
    fvg_present: bool
    ce_distance_atr: float         # расстояние до CE в ATR
    ob_distance_atr: float         # расстояние OB до цены в ATR
    # результат бектеста
    result: str = "OPEN"           # WIN / LOSS / OPEN
    exit_price: float = 0.0
    exit_t: Optional[datetime] = None
    rr_achieved: float = 0.0
 
 
# ══════════════════════════════════════════════════════════════════
# DATA FETCHING
# ══════════════════════════════════════════════════════════════════
 
def fetch_candles(symbol: str, interval: str = "15min", outputsize: int = 2000, end_date: str = None) -> list[Candle]:
    kwargs = dict(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
        timezone="Europe/Berlin",
        order="ASC",
    )
    if end_date:
        kwargs["end_date"] = end_date

    data = td.time_series(**kwargs).as_json()
 
    if isinstance(data, (tuple, list)):
        values = list(data)
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
            v=float(r.get("volume", 0)),
        ))
    return candles
 
 
def fetch_daily_candles(symbol: str, outputsize: int = 100) -> list[Candle]:
    """Загрузка дневных свечей для PDH/PDL"""
    data = td.time_series(
        symbol=symbol,
        interval="1day",
        outputsize=outputsize,
        timezone="Europe/Berlin",
        order="ASC",
    ).as_json()
 
    if isinstance(data, (tuple, list)):
        values = list(data)
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
            v=float(r.get("volume", 0)),
        ))
    return candles
 
 
# ══════════════════════════════════════════════════════════════════
# INDICATORS
# ══════════════════════════════════════════════════════════════════
 
def calc_atr(candles: list[Candle], period: int = 14) -> list[float]:
    """ATR через True Range"""
    tr_list = []
    for i, c in enumerate(candles):
        if i == 0:
            tr_list.append(c.h - c.l)
        else:
            prev = candles[i-1]
            tr = max(c.h - c.l, abs(c.h - prev.c), abs(c.l - prev.c))
            tr_list.append(tr)
 
    atr = [0.0] * len(tr_list)
    if len(tr_list) < period:
        return atr
 
    atr[period-1] = sum(tr_list[:period]) / period
    for i in range(period, len(tr_list)):
        atr[i] = (atr[i-1] * (period - 1) + tr_list[i]) / period
 
    return atr
 
 
def calc_chandelier_exit(
    candles: list[Candle],
    period: int = 22,
    mult: float = 3.0,
    use_close: bool = True
) -> tuple[list[float], list[float], list[int]]:
    """
    Chandelier Exit — точный порт из Pine Script.
    Возвращает (long_stop, short_stop, direction)
    direction: 1 = лонг, -1 = шорт
    """
    atr_vals = calc_atr(candles, period)
    n = len(candles)
 
    long_stop  = [0.0] * n
    short_stop = [0.0] * n
    direction  = [1]   * n
 
    for i in range(n):
        atr = atr_vals[i] * mult
        closes = [candles[j].c for j in range(max(0, i - period + 1), i + 1)]
        highs  = [candles[j].h for j in range(max(0, i - period + 1), i + 1)]
        lows   = [candles[j].l for j in range(max(0, i - period + 1), i + 1)]
 
        ls = (max(closes) if use_close else max(highs)) - atr
        ss = (min(closes) if use_close else min(lows))  + atr
 
        if i == 0:
            long_stop[i]  = ls
            short_stop[i] = ss
        else:
            # long stop ratchet
            ls_prev = long_stop[i-1]
            if candles[i-1].c > ls_prev:
                long_stop[i] = max(ls, ls_prev)
            else:
                long_stop[i] = ls
 
            # short stop ratchet
            ss_prev = short_stop[i-1]
            if candles[i-1].c < ss_prev:
                short_stop[i] = min(ss, ss_prev)
            else:
                short_stop[i] = ss
 
            # direction
            if candles[i].c > short_stop[i-1]:
                direction[i] = 1
            elif candles[i].c < long_stop[i-1]:
                direction[i] = -1
            else:
                direction[i] = direction[i-1]
 
    return long_stop, short_stop, direction
 
 
def detect_order_blocks(
    candles: list[Candle],
    length: int = 5,
    mitigation: str = "Wick"
) -> list[OrderBlock]:
    n = len(candles)
    obs: list[OrderBlock] = []
    
    # Сначала вычисляем os для КАЖДОГО бара и сохраняем
    os_history = [0] * n
    os = 0
    
    for i in range(n):
        if i < length:
            os_history[i] = os
            continue
        
        upper = max(c.h for c in candles[i - length + 1 : i + 1])
        lower = min(c.l for c in candles[i - length + 1 : i + 1])
        
        if candles[i - length].h > upper:
            os = 0
        elif candles[i - length].l < lower:
            os = 1
        
        os_history[i] = os
    
    # Теперь ищем pivot и берём os НА МОМЕНТ ПИВОТА
    for i in range(length * 2, n):
        pivot_idx = i - length
        pivot_vol = candles[pivot_idx].v
        
        is_pivot = True
        for j in range(pivot_idx - length, pivot_idx + length + 1):
            if j < 0 or j >= n or j == pivot_idx:
                continue
            if candles[j].v > pivot_vol:
                is_pivot = False
                break
        
        if not is_pivot:
            continue
        
        # os берём на момент бара i (как в Pine — os актуален на текущем баре)
        current_os = os_history[i]
        
        if current_os == 1:
            hl2 = (candles[pivot_idx].h + candles[pivot_idx].l) / 2
            obs.append(OrderBlock(
                top=hl2,
                btm=candles[pivot_idx].l,
                avg=hl2,
                t=candles[pivot_idx].t,
                is_bull=True,
            ))
        elif current_os == 0:
            hl2 = (candles[pivot_idx].h + candles[pivot_idx].l) / 2
            obs.append(OrderBlock(
                top=candles[pivot_idx].h,
                btm=hl2,
                avg=hl2,
                t=candles[pivot_idx].t,
                is_bull=False,
            ))
    
    # Митигация — без изменений
    for ob in obs:
        ob_idx = next((j for j, c in enumerate(candles) if c.t == ob.t), None)
        if ob_idx is None:
            continue
        for j in range(ob_idx + 1, n):
            c = candles[j]
            if ob.is_bull:
                target = c.l if mitigation == "Wick" else c.c
                if target < ob.btm:
                    ob.mitigated = True
                    break
            else:
                target = c.h if mitigation == "Wick" else c.c
                if target > ob.top:
                    ob.mitigated = True
                    break
    
    return obs
 
 
def detect_fvg(
    candles: list[Candle],
    threshold_pct: float = 0.0
) -> list[FVG]:
    """
    LuxAlgo FVG — порт из Pine Script.
    bull_fvg: low[0] > high[2] and close[1] > high[2]
    bear_fvg: high[0] < low[2] and close[1] < low[2]
    """
    fvgs: list[FVG] = []
    n = len(candles)
 
    for i in range(2, n):
        c0, c1, c2 = candles[i], candles[i-1], candles[i-2]
 
        # Bull FVG
        if c0.l > c2.h and c1.c > c2.h:
            gap = (c0.l - c2.h) / c2.h
            if gap > threshold_pct / 100:
                fvgs.append(FVG(top=c0.l, btm=c2.h, is_bull=True, t=c0.t))
 
        # Bear FVG
        elif c0.h < c2.l and c1.c < c2.l:
            gap = (c2.l - c0.h) / c0.h
            if gap > threshold_pct / 100:
                fvgs.append(FVG(top=c2.l, btm=c0.h, is_bull=False, t=c0.t))
 
    # Митигация FVG
    for fvg in fvgs:
        fvg_idx = next((j for j, c in enumerate(candles) if c.t == fvg.t), None)
        if fvg_idx is None:
            continue
        for j in range(fvg_idx + 1, n):
            c = candles[j]
            if fvg.is_bull and c.c < fvg.btm:
                fvg.mitigated = True
                break
            elif not fvg.is_bull and c.c > fvg.top:
                fvg.mitigated = True
                break
 
    return fvgs
 
 
def get_pdh_pdl(daily_candles: list[Candle], date: datetime.date) -> tuple[float, float]:
    """
    Возвращает PDH и PDL для заданной даты.
    Ищем дневную свечу предыдущего торгового дня.
    """
    prev_candle = None
    for c in daily_candles:
        c_date = c.t.date() if isinstance(c.t, datetime) else c.t
        if c_date < date:
            prev_candle = c
        elif c_date >= date:
            break
 
    if prev_candle:
        return prev_candle.h, prev_candle.l
    return float("nan"), float("nan")
 
 
# ══════════════════════════════════════════════════════════════════
# NY SESSION FILTER
# ══════════════════════════════════════════════════════════════════
 
def is_ny_session(t: datetime) -> bool:
    """Проверяет, входит ли время (Berlin) в NY-сессию 8:30–16:45 ET"""
    if t.tzinfo is None:
        t_berlin = BERLIN_TZ.localize(t)
    else:
        t_berlin = t
 
    t_ny = t_berlin.astimezone(NY_TZ)
    start = t_ny.replace(hour=8, minute=30, second=0, microsecond=0)
    end   = t_ny.replace(hour=16, minute=45, second=0, microsecond=0)
    return start <= t_ny < end
 
 
def get_ny_session_end(t: datetime) -> datetime:
    """Возвращает конец NY-сессии для данного дня"""
    if t.tzinfo is None:
        t_berlin = BERLIN_TZ.localize(t)
    else:
        t_berlin = t
    t_ny = t_berlin.astimezone(NY_TZ)
    end_ny = t_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return end_ny.astimezone(BERLIN_TZ)
 
 
# ══════════════════════════════════════════════════════════════════
# SIGNAL DETECTION (CORE RULES)
# ══════════════════════════════════════════════════════════════════
 
def check_entry_conditions(
    i: int,
    candles: list[Candle],
    atr_vals: list[float],
    long_stops: list[float],
    short_stops: list[float],
    directions: list[int],
    obs: list[OrderBlock],
    fvgs: list[FVG],
    pdh: float,
    pdl: float,
    # параметры
    ob_max_dist_atr: float = 1.5,
    ce_min_dist_atr: float = 0.5,
    rr_min: float = 2.0,
) -> Optional[Signal]:
    """
    Проверяет все 5 условий входа на свече i.
    Возвращает Signal если все условия выполнены.
    """
    if i < 30:  # нужно достаточно истории
        return None
 
    c     = candles[i]
    atr   = atr_vals[i]
    if atr == 0:
        return None
 
    price    = c.c
    ls       = long_stops[i]
    ss       = short_stops[i]
    direction = directions[i]
 
    # ── Условие 2: Цена расположена относительно CE ──────────────
    # LONG: цена выше green CE (long_stop)
    # SHORT: цена ниже red CE (short_stop)
    is_long_context  = direction == 1   # цена выше CE → бычий режим
    is_short_context = direction == -1  # цена ниже CE → медвежий режим
 
    if not is_long_context and not is_short_context:
        return None
 
    # ── Условие 3: Расстояние до CE минимум 0.5 ATR ──────────────
    if is_long_context:
        ce_dist = price - ls
    else:
        ce_dist = ss - price
 
    if ce_dist < ce_min_dist_atr * atr:
        return None
 
    ce_dist_atr = ce_dist / atr
 
    # ── Условие 1: Order Block ────────────────────────────────────
    # Ищем ближайший не-митигированный OB в нужном направлении
    best_ob = None
    best_ob_dist = float("inf")
 
    for ob in obs:
        if ob.mitigated:
            continue
        if ob.t >= c.t:  # OB должен быть до текущей свечи
            continue
 
        if is_long_context and ob.is_bull:
            # Бычий OB должен быть ПОД ценой
            if ob.top < price:
                dist = price - ob.top  # дистанция от цены до верха OB
                dist_atr = dist / atr
                if dist_atr <= ob_max_dist_atr and dist < best_ob_dist:
                    best_ob_dist = dist
                    best_ob = ob
 
        elif is_short_context and not ob.is_bull:
            # Медвежий OB должен быть НАД ценой
            if ob.btm > price:
                dist = ob.btm - price
                dist_atr = dist / atr
                if dist_atr <= ob_max_dist_atr and dist < best_ob_dist:
                    best_ob_dist = dist
                    best_ob = ob
 
    if best_ob is None:
        return None
 
    ob_dist_atr = best_ob_dist / atr
 
    # ── Условие 4 (опционально): FVG в том же направлении ────────
    fvg_present = False
    for fvg in fvgs:
        if fvg.mitigated:
            continue
        if fvg.t >= c.t:
            continue
        if is_long_context and fvg.is_bull and fvg.btm < price:
            fvg_present = True
            break
        if is_short_context and not fvg.is_bull and fvg.top > price:
            fvg_present = True
            break
 
    # ── Условие 5: PDH/PDL как таргет, RR >= 2x ──────────────────
    if is_long_context:
        if pd.isna(pdh):
            return None
        stop_dist  = price - best_ob.btm  # стоп под OB
        tp_dist    = pdh - price
        target     = pdh
    else:
        if pd.isna(pdl):
            return None
        stop_dist  = best_ob.top - price  # стоп над OB
        tp_dist    = price - pdl
        target     = pdl
 
    if stop_dist <= 0 or tp_dist <= 0:
        return None
 
    rr = tp_dist / stop_dist
    if rr < rr_min:
        return None
 
    # ── Все условия выполнены → Signal ───────────────────────────
    direction_str = "LONG" if is_long_context else "SHORT"
    stop_price    = best_ob.btm if is_long_context else best_ob.top
 
    return Signal(
        t              = c.t,
        direction      = direction_str,
        entry          = price,
        stop           = stop_price,
        take_profit    = target,
        atr            = atr,
        ob_used        = best_ob,
        fvg_present    = fvg_present,
        ce_distance_atr = ce_dist_atr,
        ob_distance_atr = ob_dist_atr,
    )
 
 
# ══════════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ══════════════════════════════════════════════════════════════════
 
def run_backtest(
    symbol: str,
    # временной промежуток
    start_berlin: str = "2024-01-01 08:30",
    end_berlin: str   = "2024-06-01 16:45",
    # таймфрейм анализа
    tf: str = "15min",
    # параметры CE (Chandelier Exit)
    ce_period: int    = 22,
    ce_mult: float    = 3.0,
    ce_use_close: bool = True,
    # параметры OB
    ob_length: int    = 5,
    ob_mitigation: str = "Wick",
    ob_max_dist_atr: float = 1.5,
    # параметры FVG
    fvg_threshold: float = 0.0,
    # условия входа
    ce_min_dist_atr: float = 0.5,
    rr_min: float = 2.0,
    # вывод
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Полный бэктест SMC-системы.
    Прогоняет данные за период, находит сигналы, оценивает результат.
    """
    print(f"\n{'═'*65}")
    print(f"  SMC BACKTEST ENGINE")
    print(f"  Symbol : {symbol}")
    print(f"  Period : {start_berlin} → {end_berlin} (Berlin)")
    print(f"  TF     : {tf}")
    print(f"{'═'*65}\n")
 
    # ── Загрузка данных ───────────────────────────────────────────
    print("📥 Загрузка данных...")
    all_candles   = fetch_candles(symbol, tf, outputsize=5000)
    daily_candles = fetch_daily_candles(symbol, outputsize=500)
 
    start_dt = datetime.fromisoformat(start_berlin)
    end_dt   = datetime.fromisoformat(end_berlin)
 
    # Берём все свечи для расчёта индикаторов (нужна история до start)
    work_candles = all_candles  # используем всё для точности индикаторов
 
    print(f"   Свечей загружено : {len(work_candles)}")
    print(f"   Дневных свечей   : {len(daily_candles)}")
 
    # ── Расчёт индикаторов ────────────────────────────────────────
    print("📊 Расчёт индикаторов...")
    atr_vals = calc_atr(work_candles, ce_period)
    long_stops, short_stops, directions = calc_chandelier_exit(
        work_candles, ce_period, ce_mult, ce_use_close
    )
    obs  = detect_order_blocks(work_candles, ob_length, ob_mitigation)
    fvgs = detect_fvg(work_candles, fvg_threshold)
 
    print(f"   Order Blocks найдено : {len(obs)}")
    print(f"   FVG найдено          : {len(fvgs)}")
 
    # ── Основной цикл по свечам ───────────────────────────────────
    signals: list[Signal] = []
    active_signal: Optional[Signal] = None
 
    print("🔍 Сканирование сигналов...\n")
 
    for i, c in enumerate(work_candles):
        # Фильтр по временному промежутку бектеста
        if c.t < start_dt or c.t > end_dt:
            continue
 
        # Только NY-сессия
        if not is_ny_session(c.t):
            continue
 
        # ── Проверка активного сигнала ────────────────────────────
        if active_signal is not None:
            price = c.c
 
            # Конец NY-сессии → закрываем по рынку
            session_end = get_ny_session_end(c.t)
            if BERLIN_TZ.localize(c.t) >= session_end:
                active_signal.result = "EXPIRED"
                active_signal.exit_price = price
                active_signal.exit_t = c.t
                rr = ((price - active_signal.entry) /
                      (active_signal.entry - active_signal.stop)
                      if active_signal.direction == "LONG"
                      else (active_signal.entry - price) /
                           (active_signal.stop - active_signal.entry))
                active_signal.rr_achieved = round(rr, 2)
                active_signal = None
                continue
 
            if active_signal.direction == "LONG":
                # Стоп
                if c.l <= active_signal.stop:
                    active_signal.result = "LOSS"
                    active_signal.exit_price = active_signal.stop
                    active_signal.exit_t = c.t
                    active_signal.rr_achieved = -1.0
                    active_signal = None
                # Тейк
                elif c.h >= active_signal.take_profit:
                    active_signal.result = "WIN"
                    active_signal.exit_price = active_signal.take_profit
                    active_signal.exit_t = c.t
                    tp_dist = active_signal.take_profit - active_signal.entry
                    sl_dist = active_signal.entry - active_signal.stop
                    active_signal.rr_achieved = round(tp_dist / sl_dist, 2)
                    active_signal = None
 
            else:  # SHORT
                if c.h >= active_signal.stop:
                    active_signal.result = "LOSS"
                    active_signal.exit_price = active_signal.stop
                    active_signal.exit_t = c.t
                    active_signal.rr_achieved = -1.0
                    active_signal = None
                elif c.l <= active_signal.take_profit:
                    active_signal.result = "WIN"
                    active_signal.exit_price = active_signal.take_profit
                    active_signal.exit_t = c.t
                    tp_dist = active_signal.entry - active_signal.take_profit
                    sl_dist = active_signal.stop - active_signal.entry
                    active_signal.rr_achieved = round(tp_dist / sl_dist, 2)
                    active_signal = None
 
            continue  # пока есть активный сигнал — новые не ищем
 
        # ── Определяем PDH/PDL для текущего дня ──────────────────
        curr_date = c.t.date()
        pdh, pdl = get_pdh_pdl(daily_candles, curr_date)
 
        # ── Проверка условий входа ────────────────────────────────
        signal = check_entry_conditions(
            i, work_candles, atr_vals,
            long_stops, short_stops, directions,
            obs, fvgs, pdh, pdl,
            ob_max_dist_atr=ob_max_dist_atr,
            ce_min_dist_atr=ce_min_dist_atr,
            rr_min=rr_min,
        )
 
        if signal:
            signals.append(signal)
            active_signal = signal
 
            if verbose:
                fvg_tag = "✅ FVG" if signal.fvg_present else "  (no FVG)"
                print(
                    f"  [{signal.t.strftime('%Y-%m-%d %H:%M')}] "
                    f"{signal.direction:5s} | "
                    f"Entry={signal.entry:.5f} | "
                    f"SL={signal.stop:.5f} | "
                    f"TP={signal.take_profit:.5f} | "
                    f"RR≈{(abs(signal.take_profit - signal.entry) / abs(signal.entry - signal.stop)):.1f} | "
                    f"CE_dist={signal.ce_distance_atr:.2f}ATR | "
                    f"OB_dist={signal.ob_distance_atr:.2f}ATR | "
                    f"{fvg_tag}"
                )
 
    # ── Статистика ────────────────────────────────────────────────
    if not signals:
        print("\n⚠️  Сигналов не найдено в указанном периоде.")
        return pd.DataFrame()
 
    df = pd.DataFrame([{
        "Дата/Время (Berlin)":  s.t.strftime("%Y-%m-%d %H:%M"),
        "Направление":          s.direction,
        "Вход":                 round(s.entry, 5),
        "Стоп":                 round(s.stop, 5),
        "Тейк (PDH/PDL)":       round(s.take_profit, 5),
        "RR_план":              round(abs(s.take_profit - s.entry) / abs(s.entry - s.stop), 2),
        "ATR":                  round(s.atr, 5),
        "CE dist (ATR)":        round(s.ce_distance_atr, 2),
        "OB dist (ATR)":        round(s.ob_distance_atr, 2),
        "FVG":                  "✅" if s.fvg_present else "–",
        "Результат":            s.result,
        "RR_факт":              s.rr_achieved,
        "Выход":                round(s.exit_price, 5) if s.exit_price else "",
        "Выход время":          s.exit_t.strftime("%Y-%m-%d %H:%M") if s.exit_t else "",
    } for s in signals])
 
    # ── Итоги ─────────────────────────────────────────────────────
    wins     = len([s for s in signals if s.result == "WIN"])
    losses   = len([s for s in signals if s.result == "LOSS"])
    expired  = len([s for s in signals if s.result == "EXPIRED"])
    total    = len(signals)
    wr       = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
 
    with_fvg    = len([s for s in signals if s.fvg_present])
    wins_fvg    = len([s for s in signals if s.fvg_present and s.result == "WIN"])
    wr_fvg      = wins_fvg / with_fvg * 100 if with_fvg > 0 else 0
 
    print(f"\n{'═'*65}")
    print(f"  РЕЗУЛЬТАТЫ БЭКТЕСТА")
    print(f"{'═'*65}")
    print(f"  Всего сигналов : {total}")
    print(f"  WIN            : {wins}  ({wr:.1f}%)")
    print(f"  LOSS           : {losses}")
    print(f"  EXPIRED (EOD)  : {expired}")
    print(f"  Winrate        : {wr:.1f}%")
    print(f"─{'─'*64}")
    print(f"  С FVG подтверждением : {with_fvg} сигналов, WR = {wr_fvg:.1f}%")
    print(f"{'═'*65}\n")
 
    return df
 
 
# ══════════════════════════════════════════════════════════════════
# LIVE ANALYSIS (точечный анализ конкретного момента)
# ══════════════════════════════════════════════════════════════════
 
def analyze_moment(
    symbol: str,
    berlin_time: str,     # "2024-03-15 14:22" — момент для анализа
    tf: str = "15min",
    candles_to_load: int = 1000,
    ce_period: int = 22,
    ce_mult: float = 3.0,
    ob_length: int = 5,
    ob_mitigation: str = "Wick",
    ob_max_dist_atr: float = 1.5,
    ce_min_dist_atr: float = 0.5,
    fvg_threshold: float = 0.0,
    rr_min: float = 2.0,
):
    """
    Анализирует конкретный момент времени.
    Загружает N свечей до указанного времени, прогоняет все условия.
    """
    target_dt = datetime.fromisoformat(berlin_time)
 
    print(f"\n{'═'*65}")
    print(f"  SMC SNAPSHOT ANALYSIS")
    print(f"  Symbol : {symbol}")
    print(f"  Момент : {berlin_time} (Berlin)")
    print(f"  TF     : {tf}  |  Свечей: {candles_to_load}")
    print(f"{'═'*65}\n")
 
    print("📥 Загрузка данных...")
    candles = fetch_candles(symbol, tf, outputsize=candles_to_load, end_date=berlin_time)
    daily_candles = fetch_daily_candles(symbol, outputsize=100)
 
    # Берём только свечи ДО target_dt
    candles = [c for c in candles if c.t <= target_dt]
    if not candles:
        print("❌ Нет данных для указанного момента")
        return
 
    print(f"   Свечей в окне: {len(candles)}")
 
    # Расчёт индикаторов
    atr_vals = calc_atr(candles, ce_period)
    long_stops, short_stops, directions = calc_chandelier_exit(
        candles, ce_period, ce_mult
    )
    obs  = detect_order_blocks(candles, ob_length, ob_mitigation)
    fvgs = detect_fvg(candles, fvg_threshold)
 
    i   = len(candles) - 1
    c   = candles[i]
    atr = atr_vals[i]
 
    pdh, pdl = get_pdh_pdl(daily_candles, target_dt.date())
 
    direction   = directions[i]
    ls          = long_stops[i]
    ss          = short_stops[i]
    price       = c.c
    ce_level    = ls if direction == 1 else ss
    ce_dist     = abs(price - ce_level)
    ce_dist_atr = ce_dist / atr if atr else 0
 
    print(f"📌 ТЕКУЩАЯ КАРТИНА ({c.t.strftime('%Y-%m-%d %H:%M')} Berlin)")
    print(f"   Цена         : {price:.5f}")
    print(f"   ATR          : {atr:.5f}")
    print(f"   CE направл.  : {'LONG (green)' if direction == 1 else 'SHORT (red)'}")
    print(f"   CE уровень   : {ce_level:.5f}")
    print(f"   Дист до CE   : {ce_dist:.5f}  ({ce_dist_atr:.2f} ATR)")
    print(f"   PDH          : {pdh:.5f}" if not pd.isna(pdh) else "   PDH          : N/A")
    print(f"   PDL          : {pdl:.5f}" if not pd.isna(pdl) else "   PDL          : N/A")
    print()
 
    # Проверка условий
    signal = check_entry_conditions(
        i, candles, atr_vals,
        long_stops, short_stops, directions,
        obs, fvgs, pdh, pdl,
        ob_max_dist_atr=ob_max_dist_atr,
        ce_min_dist_atr=ce_min_dist_atr,
        rr_min=rr_min,
    )
 
    # Детальный вывод по каждому условию
    print("🔎 ПРОВЕРКА УСЛОВИЙ ВХОДА:")
    print(f"{'─'*55}")
 
    # Условие 2: CE
    cond2 = direction == 1 or direction == -1
    cond2_detail = f"цена {'выше' if direction == 1 else 'ниже'} CE {'(green ✅)' if direction == 1 else '(red ✅)'}"
    print(f"  {'✅' if cond2 else '❌'} [2] CE направление   : {cond2_detail}")
 
    # Условие 3: CE дистанция
    cond3 = ce_dist_atr >= ce_min_dist_atr
    print(f"  {'✅' if cond3 else '❌'} [3] CE дистанция      : {ce_dist_atr:.2f} ATR (мин {ce_min_dist_atr})")
 
    # Условие 1: OB
    best_ob = None
    best_ob_dist_atr = float("inf")
    for ob in obs:
        if ob.mitigated or ob.t >= c.t:
            continue
        if direction == 1 and ob.is_bull and ob.top < price:
            d = (price - ob.top) / atr
            if d <= ob_max_dist_atr and d < best_ob_dist_atr:
                best_ob_dist_atr = d
                best_ob = ob
        elif direction == -1 and not ob.is_bull and ob.btm > price:
            d = (ob.btm - price) / atr
            if d <= ob_max_dist_atr and d < best_ob_dist_atr:
                best_ob_dist_atr = d
                best_ob = ob
 
    cond1 = best_ob is not None
    if cond1:
        ob_dir = "Bullish" if best_ob.is_bull else "Bearish"
        print(f"  ✅ [1] Order Block        : {ob_dir} OB @ {best_ob.btm:.5f}–{best_ob.top:.5f}, дист {best_ob_dist_atr:.2f} ATR")
    else:
        print(f"  ❌ [1] Order Block        : не найден в радиусе {ob_max_dist_atr} ATR")
 
    # Условие 4: FVG
    fvg_ok = False
    for fvg in fvgs:
        if fvg.mitigated or fvg.t >= c.t:
            continue
        if direction == 1 and fvg.is_bull and fvg.btm < price:
            fvg_ok = True
            break
        if direction == -1 and not fvg.is_bull and fvg.top > price:
            fvg_ok = True
            break
    print(f"  {'✅' if fvg_ok else '➖'} [4] FVG               : {'есть (бонус +)' if fvg_ok else 'нет (опционально)'}")
 
    # Условие 5: PDH/PDL RR
    cond5 = False
    rr_val = 0.0
    if cond1 and not pd.isna(pdh) and not pd.isna(pdl):
        if direction == 1:
            sl_dist = price - best_ob.btm
            tp_dist = pdh - price
        else:
            sl_dist = best_ob.top - price
            tp_dist = price - pdl
        if sl_dist > 0 and tp_dist > 0:
            rr_val = tp_dist / sl_dist
            cond5 = rr_val >= rr_min
 
    print(f"  {'✅' if cond5 else '❌'} [5] PDH/PDL RR        : {rr_val:.2f}x (мин {rr_min}x) | "
          f"{'PDH' if direction == 1 else 'PDL'} = {pdh if direction == 1 else pdl:.5f}")
 
    print(f"{'─'*55}")
 
    if signal:
        rr = abs(signal.take_profit - signal.entry) / abs(signal.entry - signal.stop)
        print(f"\n  🟢 СИГНАЛ ОБНАРУЖЕН!")
        print(f"     Направление : {signal.direction}")
        print(f"     Вход        : {signal.entry:.5f}")
        print(f"     Стоп        : {signal.stop:.5f}")
        print(f"     Тейк (PDH/PDL): {signal.take_profit:.5f}")
        print(f"     RR          : {rr:.2f}x")
        print(f"     FVG бонус   : {'да ✅' if signal.fvg_present else 'нет'}")
    else:
        failed = []
        if not cond2: failed.append("[2] CE направление")
        if not cond3: failed.append("[3] CE дистанция")
        if not cond1: failed.append("[1] Order Block")
        if not cond5: failed.append("[5] RR к PDH/PDL")
        print(f"\n  🔴 СИГНАЛА НЕТ")
        print(f"     Не выполнено: {', '.join(failed) if failed else 'см. выше'}")
 
    print(f"\n{'═'*65}\n")
    return signal
 
 
# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════
 

def predict_direction(
    symbol: str,
    signal_time: str,
    session_end: str,
    tf: str = "15min",
    ce_period: int = 22,
    ce_mult: float = 3.0,
    ob_length: int = 5,
    ob_mitigation: str = "Wick",
    ob_max_dist_atr: float = 1.5,
    ce_min_dist_atr: float = 0.5,
    fvg_threshold: float = 0.0,
    rr_min: float = 1.0,
):
    signal_dt = datetime.fromisoformat(signal_time)
    end_dt    = datetime.fromisoformat(session_end)

    print(f"\n{'═'*65}")
    print(f"  SMC DIRECTION FORECAST")
    print(f"  Symbol   : {symbol}")
    print(f"  Сигнал   : {signal_time} (Berlin)")
    print(f"  Сессия до: {session_end} (Berlin)")
    print(f"{'═'*65}\n")

    # Загрузка данных
    candles       = fetch_candles(symbol, tf, outputsize=1000, end_date=signal_time)
    daily_candles = fetch_daily_candles(symbol, outputsize=100)
    all_candles   = fetch_candles(symbol, tf, outputsize=5000)

    # Только свечи ДО момента сигнала
    candles = [c for c in candles if c.t <= signal_dt]
    if not candles:
        print("❌ Нет данных для указанного момента")
        return

    # Расчёт индикаторов
    atr_vals = calc_atr(candles, ce_period)
    long_stops, short_stops, directions = calc_chandelier_exit(candles, ce_period, ce_mult)
    obs  = detect_order_blocks(candles, ob_length, ob_mitigation)
    fvgs = detect_fvg(candles, fvg_threshold)

    i     = len(candles) - 1
    c     = candles[i]
    atr   = atr_vals[i]
    price = c.c

    pdh, pdl = get_pdh_pdl(daily_candles, signal_dt.date())

    direction = directions[i]
    ls        = long_stops[i]
    ss        = short_stops[i]
    ce_level  = ls if direction == 1 else ss
    ce_dist   = abs(price - ce_level)
    ce_dist_atr = ce_dist / atr if atr else 0

    print(f"📌 КАРТИНА НА {c.t.strftime('%Y-%m-%d %H:%M')} (Berlin)")
    print(f"   Цена   : {price:.5f}")
    print(f"   ATR    : {atr:.5f}")
    print(f"   CE     : {'LONG ↑' if direction == 1 else 'SHORT ↓'} @ {ce_level:.5f} ({ce_dist_atr:.2f} ATR)")
    print(f"   PDH    : {pdh:.5f}" if not pd.isna(pdh) else "   PDH    : N/A")
    print(f"   PDL    : {pdl:.5f}" if not pd.isna(pdl) else "   PDL    : N/A")
    print()

    # Проверка условий
    signal = check_entry_conditions(
        i, candles, atr_vals,
        long_stops, short_stops, directions,
        obs, fvgs, pdh, pdl,
        ob_max_dist_atr=ob_max_dist_atr,
        ce_min_dist_atr=ce_min_dist_atr,
        rr_min=rr_min,
    )

    if not signal:
        print("  🔴 ПРОГНОЗ НЕВОЗМОЖЕН — условия не собраны")
        print(f"{'═'*65}\n")
        return None

    # Прогноз вынесен — теперь проверяем исход по реальным свечам
    rr_plan = abs(signal.take_profit - signal.entry) / abs(signal.entry - signal.stop)

    print(f"  🟢 ПРОГНОЗ: {'⬆️  LONG' if signal.direction == 'LONG' else '⬇️  SHORT'}")
    print(f"     Вход  : {signal.entry:.5f}")
    print(f"     Стоп  : {signal.stop:.5f}")
    print(f"     Цель  : {signal.take_profit:.5f}  ({'PDH' if signal.direction == 'LONG' else 'PDL'})")
    print(f"     RR    : {rr_plan:.2f}x")
    print(f"     FVG   : {'✅' if signal.fvg_present else '–'}")
    print()

    # Проверка исхода по свечам после signal_time до session_end
    future = [c for c in all_candles if signal_dt < c.t <= end_dt]

    if not future:
        print("  ⏳ Результат: свечи после сигнала ещё не доступны (live)")
        print(f"{'═'*65}\n")
        return signal

    result     = "OPEN"
    exit_price = None
    exit_time  = None

    for fc in future:
        if signal.direction == "LONG":
            if fc.l <= signal.stop:
                result     = "❌ LOSS"
                exit_price = signal.stop
                exit_time  = fc.t
                break
            elif fc.h >= signal.take_profit:
                result     = "✅ WIN"
                exit_price = signal.take_profit
                exit_time  = fc.t
                break
        else:
            if fc.h >= signal.stop:
                result     = "❌ LOSS"
                exit_price = signal.stop
                exit_time  = fc.t
                break
            elif fc.l <= signal.take_profit:
                result     = "✅ WIN"
                exit_price = signal.take_profit
                exit_time  = fc.t
                break

    if result == "OPEN":
        last = future[-1]
        exit_price = last.c
        exit_time  = last.t
        rr_actual = ((exit_price - signal.entry) / (signal.entry - signal.stop)
                     if signal.direction == "LONG"
                     else (signal.entry - exit_price) / (signal.stop - signal.entry))
        result = f"⏹ EXPIRED (RR={rr_actual:.2f})"

    print(f"  Результат : {result}")
    print(f"  Выход     : {exit_price:.5f} в {exit_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*65}\n")

    return signal

def batch_predict(
    symbols: list[str],
    date_from: str,          # "2026-04-01"
    date_to: str,            # "2026-05-22"
    signal_hour: int = 14,   # час старта в Berlin
    signal_minute: int = 20,
    session_end_hour: int = 22,
    session_end_minute: int = 45,
    tf: str = "15min",
    ce_period: int = 22,
    ce_mult: float = 3.0,
    ob_length: int = 5,
    ob_mitigation: str = "Wick",
    ob_max_dist_atr: float = 1.5,
    ce_min_dist_atr: float = 0.5,
    fvg_threshold: float = 0.0,
    rr_min: float = 1.0,
):
    from datetime import date, timedelta

    start_date = datetime.fromisoformat(date_from).date()
    end_date   = datetime.fromisoformat(date_to).date()

    # Генерируем все рабочие дни в периоде
    all_dates = []
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:  # пн–пт
            all_dates.append(d)
        d += timedelta(days=1)

    results = []

    for symbol in symbols:
        print(f"\n{'█'*65}")
        print(f"  СИМВОЛ: {symbol}  |  Дней для анализа: {len(all_dates)}")
        print(f"{'█'*65}")

        # Загружаем все свечи один раз для всего периода
        print("📥 Загрузка данных...")
        all_candles   = fetch_candles(symbol, tf, outputsize=5000)
        daily_candles = fetch_daily_candles(symbol, outputsize=500)

        for day in all_dates:
            signal_time = f"{day} {signal_hour:02d}:{signal_minute:02d}"
            session_end = f"{day} {session_end_hour:02d}:{session_end_minute:02d}"

            signal_dt = datetime.fromisoformat(signal_time)
            end_dt    = datetime.fromisoformat(session_end)

            # Свечи до момента сигнала
            candles = [c for c in all_candles if c.t <= signal_dt]
            if len(candles) < 50:
                continue

            # Расчёт индикаторов
            atr_vals = calc_atr(candles, ce_period)
            long_stops, short_stops, directions = calc_chandelier_exit(candles, ce_period, ce_mult)
            obs  = detect_order_blocks(candles, ob_length, ob_mitigation)
            fvgs = detect_fvg(candles, fvg_threshold)

            i     = len(candles) - 1
            c     = candles[i]
            atr   = atr_vals[i]
            price = c.c

            pdh, pdl = get_pdh_pdl(daily_candles, signal_dt.date())

            signal = check_entry_conditions(
                i, candles, atr_vals,
                long_stops, short_stops, directions,
                obs, fvgs, pdh, pdl,
                ob_max_dist_atr=ob_max_dist_atr,
                ce_min_dist_atr=ce_min_dist_atr,
                rr_min=rr_min,
            )

            if not signal:
                print(f"  {day}  🔴 нет сигнала")
                results.append({
                    "Символ": symbol,
                    "Дата": str(day),
                    "Прогноз": "NO SIGNAL",
                    "Вход": "", "Стоп": "", "Цель": "",
                    "RR_план": "", "FVG": "",
                    "Результат": "", "Выход": "", "Выход время": "",
                })
                continue

            rr_plan = abs(signal.take_profit - signal.entry) / abs(signal.entry - signal.stop)

            # Проверка исхода
            future = [c for c in all_candles if signal_dt < c.t <= end_dt]

            result     = "OPEN"
            exit_price = 0.0
            exit_time  = None

            for fc in future:
                if signal.direction == "LONG":
                    if fc.l <= signal.stop:
                        result = "LOSS"
                        exit_price = signal.stop
                        exit_time  = fc.t
                        break
                    elif fc.h >= signal.take_profit:
                        result = "WIN"
                        exit_price = signal.take_profit
                        exit_time  = fc.t
                        break
                else:
                    if fc.h >= signal.stop:
                        result = "LOSS"
                        exit_price = signal.stop
                        exit_time  = fc.t
                        break
                    elif fc.l <= signal.take_profit:
                        result = "WIN"
                        exit_price = signal.take_profit
                        exit_time  = fc.t
                        break

            if result == "OPEN" and future:
                last = future[-1]
                exit_price = last.c
                exit_time  = last.t
                rr_actual = ((exit_price - signal.entry) / (signal.entry - signal.stop)
                             if signal.direction == "LONG"
                             else (signal.entry - exit_price) / (signal.stop - signal.entry))
                result = f"EXPIRED(RR={rr_actual:.2f})"

            icon = "✅" if result == "WIN" else "❌" if result == "LOSS" else "⏹"
            print(
                f"  {day}  {'⬆️ LONG ' if signal.direction == 'LONG' else '⬇️ SHORT'}  "
                f"Entry={signal.entry:.5f}  TP={signal.take_profit:.5f}  "
                f"RR={rr_plan:.1f}x  {icon} {result}"
            )

            results.append({
                "Символ":    symbol,
                "Дата":      str(day),
                "Прогноз":   signal.direction,
                "Вход":      round(signal.entry, 5),
                "Стоп":      round(signal.stop, 5),
                "Цель":      round(signal.take_profit, 5),
                "RR_план":   round(rr_plan, 2),
                "FVG":       "✅" if signal.fvg_present else "–",
                "Результат": result,
                "Выход":     round(exit_price, 5) if exit_price else "",
                "Выход время": exit_time.strftime("%Y-%m-%d %H:%M") if exit_time else "",
            })

    df = pd.DataFrame(results)

    if df.empty:
        print("\n⚠️ Нет данных для отчёта")
        return df

    # Итоговая статистика
    for sym in symbols:
        sub = df[df["Символ"] == sym]
        wins   = len(sub[sub["Результат"] == "WIN"])
        losses = len(sub[sub["Результат"] == "LOSS"])
        total  = wins + losses
        wr     = wins / total * 100 if total > 0 else 0
        print(f"\n  {sym}: сигналов {len(sub)} | WIN {wins} | LOSS {losses} | WR {wr:.1f}%")

    # Сохраняем
    out = f"batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n💾 Сохранено: {out}")

    return df



if __name__ == "__main__":
    batch_predict(
        symbols        = ["EUR/USD"],
        date_from      = "2026-04-01",
        date_to        = "2026-05-22",
        signal_hour    = 14,
        signal_minute  = 20,
        session_end_hour   = 22,
        session_end_minute = 45,
        tf             = "15min",
        ce_period      = 22,
        ce_mult        = 3.0,
        ob_length      = 5,
        ob_mitigation  = "Wick",
        ob_max_dist_atr = 1.5,
        ce_min_dist_atr = 0.5,
        fvg_threshold  = 0.0,
        rr_min         = 1.0,
    )
