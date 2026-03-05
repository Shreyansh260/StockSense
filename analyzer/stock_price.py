import yfinance as yf

def get_stock_data(stock_symbol: str):
    try:
        ticker = yf.Ticker(stock_symbol)
        data = ticker.history(period="1mo")

        if data.empty:
            print(f"No data found for symbol: {stock_symbol}")
            return None

        return data

    except Exception as e:
        print(f"Error fetching stock data for {stock_symbol}: {e}")
        return None