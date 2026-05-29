"""
indicators.py — Python порт Pine Script индикаторов

Источники:
  • ML-GMM | AlphaNatt  (Pine v6, overlay=false)
  • ATR Bands | TheTrdFloor  (Pine v5, overlay=true)

Все функции принимают pd.Series / pd.DataFrame и возвращают pd.Series / pd.DataFrame.
Индексы сохраняются — можно конкатенировать с исходным df напрямую.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════
#  ПАРАМЕТРЫ (dataclasses — удобно прокидывать в compute_indicators)
# ══════════════════════════════════════════════════════════════════

@dataclass
class GMMParams:
    training_period: int   = 100    # lookback для нормализации
    n_components:    int   = 3      # кол-во гауссиан (сейчас всегда 3)
    momentum_length: int   = 14     # ROC / RSI период
    learning_rate:   float = 0.3    # шаг M-step
    smoothing:       int   = 3      # EMA-сглаживание осциллятора


@dataclass
class ATRParams:
    atr_period:       int   = 3     # период ATR
    atr_multiplier:   float = 2.5   # множитель полос
    tp_scale_factor:  float = 1.5   # R:R для TP-полос


@dataclass
class ADXParams:
    di_len:  int = 14   # DI Length
    adx_len: int = 14   # ADX Smoothing


@dataclass
class EMAParams:
    length: int = 200


# ══════════════════════════════════════════════════════════════════
#  БАЗОВЫЕ MA / TA — точные аналоги Pine built-ins
# ══════════════════════════════════════════════════════════════════

def _rma(series: pd.Series, length: int) -> pd.Series:
    """
    Wilder's MA — та же формула что ta.rma() в Pine.
    alpha = 1/length, инициализация через SMA первых `length` баров.
    """
    arr = series.to_numpy(dtype=float)
    out = np.full(len(arr), np.nan)

    # Найдём первый не-NaN индекс
    first = 0
    while first < len(arr) and np.isnan(arr[first]):
        first += 1

    seed_end = first + length  # исключительно
    if seed_end > len(arr):
        return pd.Series(out, index=series.index)

    out[seed_end - 1] = np.nanmean(arr[first:seed_end])
    alpha = 1.0 / length
    for i in range(seed_end, len(arr)):
        if np.isnan(arr[i]):
            out[i] = out[i - 1]          # Pine fixnan-поведение
        else:
            out[i] = alpha * arr[i] + (1.0 - alpha) * out[i - 1]

    return pd.Series(out, index=series.index)


def _ema(series: pd.Series, length: int) -> pd.Series:
    """ta.ema — стандартный EMA с adjust=False."""
    return series.ewm(span=length, adjust=False).mean()


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def _stdev(series: pd.Series, length: int) -> pd.Series:
    """ta.stdev — sample std (ddof=1), совпадает с Pine."""
    return series.rolling(length).std(ddof=1)


def _roc(series: pd.Series, length: int) -> pd.Series:
    """ta.roc — % изменение относительно `length` баров назад."""
    return (series / series.shift(length) - 1.0) * 100.0


def _rsi(series: pd.Series, length: int) -> pd.Series:
    """
    ta.rsi — стандартный RSI через Wilder's MA.
    Идентично Pine: первое seed = SMA прироста/потерь.
    """
    delta = series.diff()
    gain  = delta.clip(lower=0.0)
    loss  = (-delta).clip(lower=0.0)
    avg_gain = _rma(gain, length)
    avg_loss = _rma(loss, length)
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Pine: на bar[0] prev_close = na → слагаемые с na игнорируются → TR = high - low
    tr.iloc[0] = high.iloc[0] - low.iloc[0]
    return tr


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """ta.atr — RMA от True Range."""
    return _rma(_true_range(high, low, close), length)


# ══════════════════════════════════════════════════════════════════
#  ADX  (точный порт dirmov + adx из Pine v6)
# ══════════════════════════════════════════════════════════════════

def calc_adx(
    high:    pd.Series,
    low:     pd.Series,
    close:   pd.Series,
    params:  ADXParams = None,
) -> pd.DataFrame:
    """
    Возвращает DataFrame с колонками:
        adx, plus_di, minus_di
    """
    if params is None:
        params = ADXParams()

    up   = high.diff()   # bar[0] → NaN (как в Pine: na(up))
    down = (-low.diff()) # bar[0] → NaN

    # Pine: na(up) ? na : ... — NaN на bar[0], не 0.0
    # np.where превращает NaN > X в False → писал бы 0.0; делаем маску явно
    valid = up.notna() & down.notna()

    plus_dm  = pd.Series(np.nan, index=high.index)
    minus_dm = pd.Series(np.nan, index=high.index)
    plus_dm[valid]  = np.where((up[valid] > down[valid]) & (up[valid] > 0),   up[valid],   0.0)
    minus_dm[valid] = np.where((down[valid] > up[valid]) & (down[valid] > 0), down[valid], 0.0)

    tr_rma = _rma(_true_range(high, low, close), params.di_len)

    plus_di  = 100.0 * _rma(plus_dm,  params.di_len) / tr_rma
    minus_di = 100.0 * _rma(minus_dm, params.di_len) / tr_rma

    # fixnan — Pine форвард-заполняет после первых NaN
    plus_di  = plus_di.ffill()
    minus_di = minus_di.ffill()

    di_sum = (plus_di + minus_di).replace(0.0, 1.0)
    dx = 100.0 * (plus_di - minus_di).abs() / di_sum
    adx_val = _rma(dx, params.adx_len)

    return pd.DataFrame({
        "adx":      adx_val,
        "plus_di":  plus_di,
        "minus_di": minus_di,
    }, index=high.index)


# ══════════════════════════════════════════════════════════════════
#  ATR BANDS  (порт ATR Bands v5 — TheTrdFloor)
# ══════════════════════════════════════════════════════════════════

def calc_atr_bands(
    high:   pd.Series,
    low:    pd.Series,
    close:  pd.Series,
    params: ATRParams = None,
) -> pd.DataFrame:
    """
    Возвращает DataFrame с колонками:
        upper_atr, lower_atr  — стоп-полосы
        tp_long,   tp_short   — TP-цели (по tpScaleFactor)
        scaled_atr            — сырое ATR * multiplier
        ema_200               — EMA(200, close)  [добавлена сюда для удобства]

    Источник offset: 'close' (как в оригинале, wicks-опция убрана автором).
    """
    if params is None:
        params = ATRParams()

    atr_val    = _atr(high, low, close, params.atr_period)
    scaled_atr = atr_val * params.atr_multiplier

    upper_atr = close + scaled_atr
    lower_atr = close - scaled_atr

    # TP считается как расстояние от close до стоп-полосы × scaleFactor
    tp_long  = close + (close - lower_atr) * params.tp_scale_factor
    tp_short = close - (upper_atr - close) * params.tp_scale_factor

    return pd.DataFrame({
        "upper_atr":  upper_atr,
        "lower_atr":  lower_atr,
        "tp_long":    tp_long,
        "tp_short":   tp_short,
        "scaled_atr": scaled_atr,
    }, index=close.index)


# ══════════════════════════════════════════════════════════════════
#  GMM OSCILLATOR  (порт ML-GMM | AlphaNatt, Pine v6)
# ══════════════════════════════════════════════════════════════════

def _gaussian_pdf(x: float, mean: float, variance: float) -> float:
    """Одномерный Гауссов PDF — функция gaussian_prob из Pine."""
    variance = max(variance, 0.001)
    return (
        (1.0 / np.sqrt(2.0 * np.pi * variance))
        * np.exp(-0.5 * (x - mean) ** 2 / variance)
    )


def _normalize_rolling(series: pd.Series, length: int) -> pd.Series:
    """
    normalize() из Pine:
        (val - rolling_min) / (rolling_max - rolling_min)
    При нулевом диапазоне возвращает 0.5.
    """
    roll_min = series.rolling(length).min()
    roll_max = series.rolling(length).max()
    rng      = roll_max - roll_min
    result   = (series - roll_min) / rng
    result   = result.where(rng != 0.0, 0.5)
    return result


def calc_gmm(
    high:    pd.Series,
    low:     pd.Series,
    close:   pd.Series,
    volume:  pd.Series,
    params:  GMMParams = None,
) -> pd.DataFrame:
    """
    Возвращает DataFrame с колонками:
        oscillator   — сглаженный GMM-осциллятор
        regime       — 1 / 2 / 3 (текущий режим)
        confidence   — max(resp1, resp2, resp3) ∈ [0, 1]
        resp1/2/3    — нормированные ответственности компонент

    Логика:
        • Features: momentum (ROC), volatility (stdev(close, 20)), volume_ratio
        • Нормализация по rolling window = training_period
        • E-step: гауссовые вероятности с variance=0.1
        • M-step: каждые 10 баров, с learning_rate
        • Weighted oscillator: RSI·resp1 + ROC·resp2 + Z-score·resp3
        • Сглаживание EMA(smoothing)
    """
    if params is None:
        params = GMMParams()

    tp = params.training_period
    ml = params.momentum_length
    lr = params.learning_rate
    VAR = 0.1  # фиксированная дисперсия гауссиан (как в Pine)

    # ── Features ──
    mom       = _roc(close, ml)
    vol       = _stdev(close, 20)
    vol_ratio = volume / _sma(volume, 20)

    norm_mom = _normalize_rolling(mom,       tp)
    norm_vol = _normalize_rolling(vol,       tp)
    # norm_volume вычисляется в Pine, но в осциллятор не входит — только для полноты

    # Pre-compute вспомогательные ряды (numpy для скорости в цикле)
    nm_arr   = norm_mom.to_numpy(dtype=float)
    nv_arr   = norm_vol.to_numpy(dtype=float)
    cl_arr   = close.to_numpy(dtype=float)

    rsi_arr  = _rsi(close, ml).to_numpy(dtype=float)
    mom_arr  = mom.to_numpy(dtype=float)
    sma_arr  = _sma(close, ml).to_numpy(dtype=float)
    std_arr  = _stdev(close, ml).to_numpy(dtype=float)

    n = len(close)

    # Буферы результатов
    osc_raw   = np.full(n, np.nan)
    conf_arr  = np.full(n, np.nan)
    reg_arr   = np.full(n, np.nan)
    r1_arr    = np.full(n, np.nan)
    r2_arr    = np.full(n, np.nan)
    r3_arr    = np.full(n, np.nan)

    # Начальные средние компонент (var в Pine)
    m1_m, m2_m, m3_m = 0.25, 0.50, 0.75   # по momentum
    m1_v, m2_v, m3_v = 0.30, 0.50, 0.70   # по volatility

    for i in range(n):
        nm_i = nm_arr[i]
        nv_i = nv_arr[i]
        if np.isnan(nm_i) or np.isnan(nv_i):
            continue

        # ── E-step ──
        p1 = _gaussian_pdf(nm_i, m1_m, VAR) * _gaussian_pdf(nv_i, m1_v, VAR)
        p2 = _gaussian_pdf(nm_i, m2_m, VAR) * _gaussian_pdf(nv_i, m2_v, VAR)
        p3 = _gaussian_pdf(nm_i, m3_m, VAR) * _gaussian_pdf(nv_i, m3_v, VAR)

        total = p1 + p2 + p3
        if total <= 0.0:
            total = 1.0

        r1 = p1 / total
        r2 = p2 / total
        r3 = p3 / total

        # ── M-step (каждые 10 баров) ──
        if i % 10 == 0:
            m1_m = m1_m * (1.0 - lr) + nm_i * r1 * lr
            m2_m = m2_m * (1.0 - lr) + nm_i * r2 * lr
            m3_m = m3_m * (1.0 - lr) + nm_i * r3 * lr
            m1_v = m1_v * (1.0 - lr) + nv_i * r1 * lr
            m2_v = m2_v * (1.0 - lr) + nv_i * r2 * lr
            m3_v = m3_v * (1.0 - lr) + nv_i * r3 * lr

        # ── Сохраняем ответственности ──
        r1_arr[i] = r1
        r2_arr[i] = r2
        r3_arr[i] = r3

        # ── Текущий режим ──
        if r1 > r2 and r1 > r3:
            reg_arr[i] = 1
        elif r2 > r1 and r2 > r3:
            reg_arr[i] = 2
        else:
            reg_arr[i] = 3

        # ── Компоненты осциллятора по режимам ──
        #   Режим 1 (low vol):    RSI - 50
        #   Режим 2 (normal):     ROC * 5
        #   Режим 3 (high vol):   Z-score * 20
        reg1_mom = (rsi_arr[i] - 50.0) if not np.isnan(rsi_arr[i]) else 0.0
        reg2_mom = (mom_arr[i] * 5.0)  if not np.isnan(mom_arr[i]) else 0.0

        if not np.isnan(std_arr[i]) and std_arr[i] != 0.0:
            reg3_mom = (cl_arr[i] - sma_arr[i]) / std_arr[i] * 20.0
        else:
            reg3_mom = 0.0

        osc_raw[i] = reg1_mom * r1 + reg2_mom * r2 + reg3_mom * r3
        conf_arr[i] = max(r1, r2, r3)

    # ── Сглаживание EMA ──
    # Сглаживание EMA — точный аналог Pine ta.ema при na: state carry-forward
    osc_series = pd.Series(osc_raw, index=close.index)
    osc_smoothed = osc_series.ffill().ewm(span=params.smoothing, adjust=False).mean()
    # Восстанавливаем ведущие NaN (до первого валидного бара)
    osc_smoothed[osc_series.ffill().isna()] = np.nan

    return pd.DataFrame({
        "gmm_oscillator": osc_smoothed,
        "gmm_regime":     pd.Series(reg_arr,  index=close.index),
        "gmm_confidence": pd.Series(conf_arr, index=close.index),
        "gmm_resp1":      pd.Series(r1_arr,   index=close.index),
        "gmm_resp2":      pd.Series(r2_arr,   index=close.index),
        "gmm_resp3":      pd.Series(r3_arr,   index=close.index),
    }, index=close.index)


# ══════════════════════════════════════════════════════════════════
#  EMA 200
# ══════════════════════════════════════════════════════════════════

def calc_ema(close: pd.Series, params: EMAParams = None) -> pd.Series:
    if params is None:
        params = EMAParams()
    result = _ema(close, params.length)
    result.name = f"ema_{params.length}"
    return result


# ══════════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ ВХОД — compute_indicators()
# ══════════════════════════════════════════════════════════════════

def compute_indicators(
    df:         pd.DataFrame,
    gmm_params: GMMParams  = None,
    atr_params: ATRParams  = None,
    adx_params: ADXParams  = None,
    ema_params: EMAParams  = None,
) -> pd.DataFrame:
    """
    Принимает OHLCV DataFrame с колонками:
        open, high, low, close, volume

    Возвращает тот же df + все индикаторные колонки:
        adx, plus_di, minus_di
        upper_atr, lower_atr, tp_long, tp_short, scaled_atr
        ema_200
        gmm_oscillator, gmm_regime, gmm_confidence, gmm_resp1/2/3

    Пример:
        result = compute_indicators(df)
        print(result[["close", "adx", "gmm_oscillator", "upper_atr"]].tail())
    """
    required = {"open", "high", "low", "close", "volume"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"В DataFrame отсутствуют колонки: {missing}")

    result = df.copy()

    # 1. ADX
    adx_df = calc_adx(df["high"], df["low"], df["close"], adx_params)
    result  = pd.concat([result, adx_df], axis=1)

    # 2. ATR Bands
    atr_df = calc_atr_bands(df["high"], df["low"], df["close"], atr_params)
    result  = pd.concat([result, atr_df], axis=1)

    # 3. EMA
    ema_series       = calc_ema(df["close"], ema_params)
    result[ema_series.name] = ema_series

    # 4. GMM (самое тяжёлое — O(n) цикл)
    gmm_df = calc_gmm(df["high"], df["low"], df["close"], df["volume"], gmm_params)
    result  = pd.concat([result, gmm_df], axis=1)

    return result


# ══════════════════════════════════════════════════════════════════
#  БЫСТРАЯ ПРОВЕРКА (python indicators.py)
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import numpy as np

    np.random.seed(42)
    n = 300
    price = 1.1000 + np.cumsum(np.random.randn(n) * 0.0005)
    high  = price + np.random.uniform(0.0002, 0.0010, n)
    low   = price - np.random.uniform(0.0002, 0.0010, n)
    vol   = np.random.randint(500, 5000, n).astype(float)

    df = pd.DataFrame({
        "open":   price,
        "high":   high,
        "low":    low,
        "close":  price,
        "volume": vol,
    })

    result = compute_indicators(df)

    cols = ["close", "adx", "upper_atr", "lower_atr", "ema_200",
            "gmm_oscillator", "gmm_regime", "gmm_confidence"]
    print(result[cols].tail(10).round(6).to_string())
    print(f"\nВсего колонок: {len(result.columns)}")
    print("OK — все индикаторы посчитаны")