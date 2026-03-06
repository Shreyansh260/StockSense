import pandas as pd
import yfinance as yf

VALID_PERIODS = ["3mo", "6mo", "1y", "2y"]


def get_stock_data(symbol: str, period: str = "6mo"):
    """
    Fetch OHLCV data and compute technical indicators for the given period.
    Minimum recommended period is 6mo for stable MA50.
    """
    if period not in VALID_PERIODS:
        period = "6mo"

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df is None or df.empty:
            return None

        df = df[['Close', 'Volume']].copy()
        df.dropna(inplace=True)

        # --- RSI (14) ---
        delta = df['Close'].diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = -delta.clip(upper=0).rolling(14).mean()
        rs    = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # --- MACD ---
        ema12           = df['Close'].ewm(span=12, adjust=False).mean()
        ema26           = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD']      = ema12 - ema26
        df['Signal']    = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']

        # --- Moving Averages ---
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()

        return df.dropna()

    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return None


def get_technical_score(df) -> float:
    """
    Returns a technical score between -1.0 (bearish) and +1.0 (bullish).
    Combines RSI, MACD, and MA crossover signals.
    """
    if df is None or len(df) < 52:
        return 0.0

    latest = df.iloc[-1]
    prev   = df.iloc[-2]

    # Guard against NaN in any indicator
    required = ['RSI', 'MACD', 'Signal', 'MACD_Hist', 'MA20', 'MA50']
    if any(pd.isna(latest[col]) for col in required):
        return 0.0

    score   = 0.0
    signals = 0

    # ── RSI signal ───────────────────────────────────────
    rsi = latest['RSI']
    if rsi < 35:
        score += 1.0      # oversold → bullish
    elif rsi > 65:
        score -= 1.0      # overbought → bearish
    else:
        score += (50 - rsi) / 50
    signals += 1

    # ── MACD crossover ───────────────────────────────────
    if latest['MACD'] > latest['Signal']:
        score += 1.0
    else:
        score -= 1.0
    signals += 1

    # ── MACD histogram momentum ──────────────────────────
    hist      = latest['MACD_Hist']
    prev_hist = prev['MACD_Hist']
    if hist > 0 and hist > prev_hist:
        score += 0.5
    elif hist < 0 and hist < prev_hist:
        score -= 0.5
    signals += 0.5

    # ── MA crossover ─────────────────────────────────────
    if latest['MA20'] > latest['MA50']:
        score += 1.0      # golden cross → bullish
    else:
        score -= 1.0      # death cross → bearish
    signals += 1

    # ── 10-day price trend ───────────────────────────────
    recent_trend = df['Close'].iloc[-1] - df['Close'].iloc[-10]
    if recent_trend > 0:
        score += 0.5
    else:
        score -= 0.5
    signals += 0.5

    return round(score / signals, 4)