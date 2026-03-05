import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .news_fetcher import get_news
from .sentiment import analyze_sentiment_batch
from .utils import aggregate_sentiment
from .stock_price import get_stock_data, get_technical_score, VALID_PERIODS

TICKER_MAP = {
    "AAPL":          "Apple stock",
    "TSLA":          "Tesla stock",
    "GOOGL":         "Google stock",
    "MSFT":          "Microsoft stock",
    "AMZN":          "Amazon stock",
    "NVDA":          "Nvidia stock",
    "RELIANCE.NS":   "Reliance Industries stock",
    "TCS.NS":        "TCS Tata Consultancy stock",
    "INFY.NS":       "Infosys stock",
    "HDFCBANK.NS":   "HDFC Bank stock",
    "ICICIBANK.NS":  "ICICI Bank stock",
    "BAJFINANCE.NS": "Bajaj Finance stock",
    "MARUTI.NS":     "Maruti Suzuki stock",
    "HINDUNILVR.NS": "Hindustan Unilever stock",
    "SBIN.NS":       "State Bank of India stock",
}

PERIOD_LABELS = {
    "3mo": "3 Months",
    "6mo": "6 Months",
    "1y":  "1 Year",
    "2y":  "2 Years",
}


def home(request):
    return render(request, "home.html")


@login_required(login_url='/accounts/login/')
def search_ticker(request):
    """
    AJAX endpoint — searches Yahoo Finance for a company name.
    Returns JSON list of {ticker, name, exchange, type}.
    """
    query = request.GET.get("q", "").strip()

    if not query or len(query) < 2:
        return JsonResponse({"results": []})

    try:
        url     = "https://query1.finance.yahoo.com/v1/finance/search"
        params  = {"q": query, "quotesCount": 8, "newsCount": 0, "listsCount": 0}
        headers = {"User-Agent": "Mozilla/5.0"}
        resp    = requests.get(url, params=params, headers=headers, timeout=6)

        if resp.status_code != 200:
            return JsonResponse({"results": []})

        results = []
        for q in resp.json().get("quotes", []):
            if q.get("quoteType") not in ("EQUITY", "ETF"):
                continue
            results.append({
                "ticker":   q.get("symbol", ""),
                "name":     q.get("longname") or q.get("shortname") or q.get("symbol"),
                "exchange": q.get("exchDisp", ""),
                "type":     q.get("quoteType", ""),
            })

        return JsonResponse({"results": results})

    except Exception as e:
        return JsonResponse({"results": [], "error": str(e)})


@login_required(login_url='/accounts/login/')
def analyze_stock(request):

    sentiment_score = None
    technical_score = None
    combined_score  = None
    recommendation  = None
    article_titles  = []
    price_labels    = None
    price_values    = None
    ma20_values     = None
    ma50_values     = None
    rsi_values      = None
    selected_period = "6mo"
    selected_stock  = None

    if request.method == "POST":

        stock  = request.POST.get("stock", "").strip().upper()
        period = request.POST.get("period", "6mo").strip()

        if not stock:
            return render(request, "error.html", {
                "message": "Please select or search for a stock symbol."
            })

        if period not in VALID_PERIODS:
            period = "6mo"

        selected_period = period
        selected_stock  = stock

        # ── 1. FETCH NEWS ─────────────────────────────────────────────
        query    = TICKER_MAP.get(stock, f"{stock} stock")
        articles = get_news(query)

        if not articles:
            return render(request, "error.html", {
                "message": f'No news found for "{stock}". Try again later.'
            })

        # ── 2. BATCH SENTIMENT (single model call) ────────────────────
        scores          = analyze_sentiment_batch(articles)
        sentiment_score = aggregate_sentiment(scores)
        article_titles  = [a["title"] for a in articles]

        # ── 3. PRICE DATA + TECHNICAL ─────────────────────────────────
        price_data = get_stock_data(stock, period=period)

        if price_data is None or price_data.empty:
            return render(request, "error.html", {
                "message": (
                    f'Stock "{stock}" not found on Yahoo Finance. '
                    f'Use a valid ticker like AAPL or RELIANCE.NS'
                )
            })

        technical_score = get_technical_score(price_data)

        # ── 4. COMBINED SCORE ─────────────────────────────────────────
        combined_score = round(
            (sentiment_score * 0.6) + (technical_score * 0.4), 4
        )

        # ── 5. RECOMMENDATION ────────────────────────────────────────
        if sentiment_score > 0.3 and technical_score >= 0:
            recommendation = "BUY"
        elif sentiment_score < -0.3 and technical_score <= 0:
            recommendation = "SELL"
        elif sentiment_score > 0.3 and technical_score < 0:
            recommendation = "HOLD"
        elif sentiment_score < -0.3 and technical_score > 0:
            recommendation = "HOLD"
        else:
            recommendation = "HOLD"

        # ── 6. CHART DATA ─────────────────────────────────────────────
        price_labels = price_data.index.strftime("%Y-%m-%d").tolist()
        price_values = price_data["Close"].round(2).tolist()
        ma20_values  = price_data["MA20"].round(2).tolist()
        ma50_values  = price_data["MA50"].round(2).tolist()
        rsi_values   = price_data["RSI"].round(2).tolist()

    return render(request, "dashboard.html", {
        "score":           combined_score,
        "sentiment_score": round(sentiment_score, 4) if sentiment_score is not None else None,
        "technical_score": round(technical_score, 4) if technical_score is not None else None,
        "recommendation":  recommendation,
        "articles":        article_titles,
        "price_labels":    price_labels,
        "price_values":    price_values,
        "ma20_values":     ma20_values,
        "ma50_values":     ma50_values,
        "rsi_values":      rsi_values,
        "selected_period": selected_period,
        "selected_stock":  selected_stock,
        "period_label":    PERIOD_LABELS.get(selected_period, selected_period),
        "valid_periods":   [(p, PERIOD_LABELS[p]) for p in VALID_PERIODS],
    })