import yfinance as yf
import pandas as pd

def load_clean_tickers(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    clean_list = []
    ignore = ['cryptocurrencies', 'stocks', 'indices', 'macro', 'indicators']

    for line in lines:
        text = line.strip().replace("'", "").replace(",", "").split('(')[0].strip()
        if not text or any(word in text.lower() for word in ignore):
            continue
        if text in ['BTC', 'ETH', 'SOL']:
            text = f"{text}-USD"
        mapping = {'SPX': '^GSPC', 'NDX': '^NDX', 'VIX': '^VIX', 'DXY': 'DX-Y.NYB', 'US10Y': '^TNX'}
        clean_list.append(mapping.get(text, text))

    print(f"Cleaned Tickers: {clean_list}")
    return list(dict.fromkeys(clean_list))

def fetch_and_prepare_data(tickers, period='1y', interval='1d'):
    print(f"Fetching OHLC data for: {tickers}...")
    
    # Fetching full OHLC for candles
    df = yf.download(tickers, period=period, interval=interval)

    # Visual Gap Filling (Weekend Carry-over)
    all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df = df.reindex(all_days).ffill()
    
    return df

if __name__ == "__main__":
    tickers = load_clean_tickers('tickers.txt')
    df = fetch_and_prepare_data(tickers)
    print(df.head())