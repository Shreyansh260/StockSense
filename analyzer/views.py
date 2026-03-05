from django.shortcuts import render
from .news_fetcher import get_news
from .sentiment import analyze_sentiment
from .utils import aggregate_sentiment
from .stock_price import get_stock_data

# Move outside the function — no need to rebuild this dict on every request
TICKER_MAP = {
    "AAPL": "Apple stock",
    "TSLA": "Tesla stock",
    "GOOGL": "Google stock",
    "MSFT": "Microsoft stock",
    "AMZN": "Amazon stock",
    "NVDA": "Nvidia stock",
    "RELIANCE.NS": "Reliance Industries stock",
    "TCS.NS": "TCS Tata Consultancy stock",
    "INFY.NS": "Infosys stock",
    "HDFCBANK.NS": "HDFC Bank stock",
    "ICICIBANK.NS": "ICICI Bank stock",
    "BAJFINANCE.NS": "Bajaj Finance stock",
    "MARUTI.NS": "Maruti Suzuki stock",
    "HINDUNILVR.NS": "Hindustan Unilever stock",
    "SBIN.NS": "State Bank of India stock",
}


def home(request):
    return render(request, "home.html")


def analyze_stock(request):

    sentiment_score = None
    recommendation = None
    articles = []
    price_labels = None
    price_values = None

    if request.method == "POST":

        stock = request.POST.get("stock", "").strip().upper()

        if not stock:
            return render(request, 'error.html', {'message': 'Please enter a stock symbol.'})

        # Get news using a descriptive query for better results
        query = TICKER_MAP.get(stock, f"{stock} stock market")
        articles = get_news(query)

        if not articles:
            return render(request, 'error.html', {'message': f'No news found for "{stock}". Try again later.'})

        # Analyze sentiment for each article
        scores = [analyze_sentiment(article) for article in articles]

        # Aggregate scores
        sentiment_score = aggregate_sentiment(scores)

        # Recommendation with tighter thresholds for reliability
        if sentiment_score > 0.5:
            recommendation = "BUY"
        elif sentiment_score < -0.5:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        # Fetch stock price data
        price_data = get_stock_data(stock)

        if price_data is None or price_data.empty:
            return render(request, 'error.html', {
                'message': f'Stock "{stock}" not found. Use a valid ticker like AAPL or RELIANCE.NS'
            })

        # Convert DataFrame to plain lists — safe for Django templates
        price_labels = price_data.index.strftime('%Y-%m-%d').tolist()
        price_values = price_data['Close'].round(2).tolist()

    return render(request, "dashboard.html", {
        "score": sentiment_score,
        "recommendation": recommendation,
        "articles": articles,
        "price_labels": price_labels,
        "price_values": price_values,
    })