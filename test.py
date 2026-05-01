import finplot as fplt
import yfinance as yf
import pandas as pd
from PyQt6 import QtCore

# --- 1. DATA LOADING & GAP FILLING ---
def load_clean_tickers(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    clean_list = []
    ignore = ['cryptocurrencies', 'stocks', 'indices', 'macro', 'indicators']
    for line in lines:
        text = line.strip().replace("'", "").replace(",", "").split('(')[0].strip()
        if not text or any(word in text.lower() for word in ignore):
            continue
        if text in ['BTC', 'ETH', 'SOL']: text = f"{text}-USD"
        mapping = {'SPX': '^GSPC', 'NDX': '^NDX', 'VIX': '^VIX', 'DXY': 'DX-Y.NYB', 'US10Y': '^TNX'}
        clean_list.append(mapping.get(text, text))
    return list(dict.fromkeys(clean_list))

tickers = load_clean_tickers('tickers.txt')
print(f"Fetching OHLC data for: {tickers}...")

# Fetching full OHLC for candles
df = yf.download(tickers, period='1y', interval='1d')

# Visual Gap Filling (Weekend Carry-over)
all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
df = df.reindex(all_days).ffill()

# --- 2. PLOTTING SETUP ---
# We create 1 row for Overlay + 1 row for every individual ticker
num_tickers = len(tickers)
axes = fplt.create_plot('WSB Interactive Dashboard', rows=num_tickers + 1)

overlay_ax = axes[0]
individual_axes = axes[1:]

# A. Setup Overlay (Percentage View)
# We use the 'Close' prices normalized to 100%
closes = df['Close']
norm_data = (closes / closes.iloc[0]) * 100
for col in norm_data.columns:
    fplt.plot(norm_data[col], ax=overlay_ax, legend=col)

# B. Setup Individual Charts (Price View)
# We store these plots in a list so we can toggle them later
plots = []
for ax, ticker in zip(individual_axes, tickers):
    # Get OHLC for this specific ticker
    ticker_data = df.xs(ticker, axis=1, level=1)
    
    # We plot BOTH line and candle, but hide one initially
    line = fplt.plot(ticker_data['Close'], ax=ax, legend=f"{ticker} (Line)")
    candle = fplt.candlestick_ochl(ticker_data[['Open', 'Close', 'High', 'Low']], ax=ax)
    candle.hide() # Start with lines
    
    plots.append({'line': line, 'candle': candle, 'ax': ax})

# --- 3. INTERACTIVE LOGIC ---
state = {'mode': 'all', 'type': 'line'}

def key_press(event):
    # 'O' for Overlay only
    if event.text() == 'o':
        overlay_ax.show()
        for p in plots: p['ax'].hide()
        print("View: Overlay Only")
        
    # 'm' for Multi-chart only
    elif event.text() == 'm':
        overlay_ax.hide()
        for p in plots: p['ax'].show()
        print("View: Multi-Charts")
        
    # 'a' for All (Dashboard)
    elif event.text() == 'a':
        overlay_ax.show()
        for p in plots: p['ax'].show()
        print("View: Dashboard")
        
    # 't' for Toggle Chart Type (Line vs Candle)
    elif event.text() == 't':
        state['type'] = 'candle' if state['type'] == 'line' else 'line'
        for p in plots:
            if state['type'] == 'candle':
                p['line'].hide()
                p['candle'].show()
            else:
                p['line'].show()
                p['candle'].hide()
        print(f"Type: {state['type'].upper()}")

# --- 4. LAUNCH ---
if __name__ == '__main__':
    print("\n" + "="*40)
    print("DASHBOARD CONTROLS (Click window first):")
    print(" [O] - View Overlay Only (%)")
    print(" [M] - View Multi-Charts Only ($)")
    print(" [A] - View All (Full Dashboard)")
    print(" [T] - Toggle Chart Type (Line/Candle)")
    print("="*40)

    # Attach the key press event to the main window
    win = fplt.show(qt_exec=False)
    win.keyPressEvent = key_press
    fplt.show()