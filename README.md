# 📈 StockSense — Market Sentiment Analyzer

<div align="center">

![StockSense AI](https://img.shields.io/badge/StockSense-AI-00e5a0?style=for-the-badge&logo=python&logoColor=black)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-DistilBERT-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

**AI-powered stock analysis combining NLP sentiment with technical indicators to generate BUY / SELL / HOLD signals.**

[🚀 Live Demo](https://shreyansh260.pythonanywhere.com) · [📖 How It Works](#how-it-works) · [⚙️ Setup](#setup)

</div>

---

## ✨ Features

- 🧠 **DistilBERT Sentiment Analysis** — NLP model analyzes full news article content, not just headlines
- 📊 **Technical Indicators** — RSI, MACD, MA20/MA50 computed from live Yahoo Finance data
- ⚡ **Combined Signal Score** — 60% news sentiment + 40% technical analysis with confirmation logic
- 🌍 **Worldwide Stock Search** — Search any stock from NYSE, NASDAQ, NSE, BSE, LSE, TSE and more
- 🔐 **Google OAuth Login** — Secure sign-in with Gmail account
- 📱 **Mobile Responsive** — Works on all screen sizes
- ⚡ **Prediction Caching** — Results cached for 30 minutes for instant repeat lookups
- 📰 **Full Article Intelligence** — Fetches and analyzes complete article content in parallel

---

## 🖥️ Screenshots

| Home Page | Dashboard | Results |
|---|---|---|
| Dark terminal UI with animated hero | Stock selector with worldwide search | BUY/SELL/HOLD with charts |

---

## 🏗️ How It Works

```
User selects stock + period
         ↓
1. NewsAPI fetches 10 latest articles
         ↓
2. BeautifulSoup scrapes full article content (parallel)
         ↓
3. DistilBERT analyzes sentiment (batch inference)
         ↓
4. yFinance fetches price data
         ↓
5. RSI + MACD + MA20/MA50 computed via pandas
         ↓
6. Combined Score = (Sentiment × 0.6) + (Technical × 0.4)
         ↓
7. BUY / SELL / HOLD signal generated
```

**Confirmation Logic:**
| Sentiment | Technical | Signal |
|---|---|---|
| > +0.3 | ≥ 0 | 📈 BUY |
| < -0.3 | ≤ 0 | 📉 SELL |
| Mixed signals | Any | ⏸ HOLD |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.2 |
| **NLP Model** | DistilBERT (HuggingFace Transformers) |
| **Stock Data** | yFinance |
| **News Data** | NewsAPI |
| **Auth** | django-allauth + Google OAuth2 |
| **Charts** | Chart.js |
| **Web Scraping** | BeautifulSoup4 |
| **Data Processing** | pandas, PyTorch |
| **Deployment** | Render (free tier) |
| **Static Files** | WhiteNoise |

---

## ⚙️ Setup

### Prerequisites
- Python 3.11+
- [NewsAPI key](https://newsapi.org) (free)
- [Google OAuth credentials](https://console.cloud.google.com)

### 1. Clone the repo
```bash
git clone https://github.com/Shreyansh260/StockSense.git
cd StockSense
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
NEWS_API_KEY=your-newsapi-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SITE_DOMAIN=127.0.0.1:8000
```

### 4. Run migrations
```bash
python manage.py migrate
python manage.py setup_oauth
```

### 5. Start the server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## 🚀 Deployment (Render)

### Environment Variables
Set these in Render → Environment:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `False` |
| `NEWS_API_KEY` | NewsAPI key |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SITE_DOMAIN` | your-app.onrender.com |
| `ALLOWED_HOSTS` | your-app.onrender.com,127.0.0.1 |
| `DJANGO_SUPERUSER_EMAIL` | Admin email |
| `DJANGO_SUPERUSER_PASSWORD` | Admin password |

### Start Command
```
python manage.py migrate && python manage.py setup_oauth && gunicorn stock_ai.wsgi:application
```

### Google Console Setup
Add this to **Authorised redirect URIs**:
```
https://your-app.onrender.com/accounts/google/login/callback/
```

---

## 📁 Project Structure

```
StockSense/
├── stock_ai/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── analyzer/                  # Main app
│   ├── management/
│   │   └── commands/
│   │       └── setup_oauth.py # Auto OAuth setup
│   ├── views.py               # Routes + caching logic
│   ├── news_fetcher.py        # Parallel news fetching
│   ├── sentiment.py           # DistilBERT batch inference
│   ├── stock_price.py         # yFinance + technical indicators
│   └── utils.py               # Score aggregation
├── templates/
│   ├── home.html              # Landing page
│   ├── dashboard.html         # Main analysis page
│   ├── error.html             # Error page
│   ├── account/
│   │   └── login.html         # Styled Google login
│   └── socialaccount/
│       └── login.html         # OAuth confirmation page
├── requirements.txt
├── Procfile
├── render.yaml
└── .env.example
```

---

## 📊 Supported Markets

| Market | Examples |
|---|---|
| 🇺🇸 US (NASDAQ/NYSE) | AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN |
| 🇮🇳 India (NSE) | RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS |
| 🌍 Worldwide Search | Any stock from LSE, TSE, BSE, and more |

---

## ⚡ Performance

| Optimization | Impact |
|---|---|
| Parallel news fetching (ThreadPoolExecutor) | 80s → 10s |
| Batch DistilBERT inference | 60 calls → 1 batch |
| In-memory prediction cache (30 min TTL) | Instant repeat lookups |
| Lazy model loading | Saves RAM on free tier |

---

## ⚠️ Disclaimer

> This tool is for **educational and informational purposes only**.
> It is **not financial advice**. Always do your own research before making investment decisions.

---

## 📄 License

MIT License — feel free to use, modify and distribute.

---

<div align="center">
Built with ❤️ using Django · DistilBERT · Chart.js · yFinance
</div>
