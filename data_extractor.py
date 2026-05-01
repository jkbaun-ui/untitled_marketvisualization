import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

VAULT_DIR = "market_vault/daily"

def get_hybrid_market_data(ticker, interval='1d'):
    # Create interval-specific storage
    interval_dir = os.path.join(VAULT_DIR, interval)
    os.makedirs(interval_dir, exist_ok=True)
    vault_file = os.path.join(interval_dir, f"{ticker}.parquet")
    
    # 30m/1h data has much shorter history limits on Yahoo Finance
    lookback = "10y" if 'd' in interval else "60d"

    # 1. Load or Initialize the Cold Vault
    if os.path.exists(vault_file):
        df_vault = pd.read_parquet(vault_file)
        # CRITICAL: Strip timezone awareness to allow comparison
        if df_vault.index.tz is not None:
            df_vault.index = df_vault.index.tz_localize(None)
        last_date = df_vault.index.max()
    else:
        print(f"Building initial {interval} Vault for {ticker}...")
        df_vault = yf.download(ticker, period=lookback, interval=interval)
        if df_vault.empty:
            return pd.DataFrame()
        
        # Strip timezone immediately after download
        if df_vault.index.tz is not None:
            df_vault.index = df_vault.index.tz_localize(None)
            
        df_vault.to_parquet(vault_file)
        last_date = df_vault.index.max()

    # 2. Check if we need fresh data
    today = pd.Timestamp.today().normalize()
    
    # Comparison now works because both are tz-naive
    if last_date < today - pd.Timedelta(days=1):
        print(f"Vault is behind. Fetching missing data for {ticker}...")
        
        start_date = (last_date + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        df_recent = yf.download(ticker, start=start_date, interval=interval)
        
        if not df_recent.empty:
            if df_recent.index.tz is not None:
                df_recent.index = df_recent.index.tz_localize(None)
                
            # Stitching logic
            closed_days = df_recent[df_recent.index < today]
            if not closed_days.empty:
                df_vault = pd.concat([df_vault, closed_days])
                df_vault.to_parquet(vault_file)
            
            live_today = df_recent[df_recent.index >= today]
            return pd.concat([df_vault, live_today])
            
    return df_vault

# Usage:
# df = get_hybrid_market_data("AAPL")

def fetch_smart_data(tickers, interval='1d'):
    processed_dfs = {}

    for ticker in tickers:
        df_ticker = get_hybrid_market_data(ticker, interval=interval)
        if not df_ticker.empty:
            processed_dfs[ticker] = df_ticker

    if not processed_dfs:
        print("Error: No data was retrieved for any tickers.")
        return pd.DataFrame()

    # Combine: Ticker becomes Level 0
    final_df = pd.concat(processed_dfs, axis=1)

    # Swap: Column name (Close) becomes Level 0, Ticker becomes Level 1
    final_df.columns = final_df.columns.swaplevel(0, 1)
    final_df = final_df.sort_index(axis=1)
    
    return final_df





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