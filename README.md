# Binance Futures Auto-Analysis Dashboard

Streamlit dashboard with Telegram notifications for automated analysis of top volatile Binance Futures pairs.

## Features

- 📊 Fetch top N volatile pairs (by 24h price change)
- 📈 Calculate ATR, approximate CVD, Open Interest & Funding Rate
- 🎯 Generate recommendation signals (Scalp Long / Scalp Short / Wait)
- 🔄 Auto-refresh functionality
- 📱 Telegram notifications for new signals
- 📉 Interactive candlestick charts

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <project-folder>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

Edit `.env` file with your credentials:
```bash
COINGLASS_API_KEY=your_key_here  # Optional
TG_BOT_TOKEN=your_bot_token      # Optional
TG_CHAT_ID=your_chat_id          # Optional
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

## Project Structure
```
project/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration and environment variables
├── api/                  # API integrations
│   ├── binance.py       # Binance Futures API
│   └── coinglass.py     # Coinglass API (optional)
├── indicators/          # Technical indicators
│   └── technical.py     # ATR, CVD calculations
├── signals/             # Signal generation
│   └── generator.py     # Trading signal logic
├── utils/               # Utility functions
│   ├── data.py         # Data processing
│   └── telegram.py     # Telegram notifications
└── requirements.txt     # Python dependencies
```

## Deployment

### Streamlit Cloud

1. Push to GitHub
2. Connect your repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in Streamlit Cloud dashboard:
   - `COINGLASS_API_KEY`
   - `TG_BOT_TOKEN`
   - `TG_CHAT_ID`

### Local/Server
```bash
streamlit run app.py --server.port 8501
```

## Disclaimer

⚠️ **This is a starter dashboard for educational purposes only.**

- Tune thresholds before live trading
- Add proper backtesting
- Use testnet and small position sizes
- Not financial advice - do your own research

## License

MIT License
