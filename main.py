from data_extractor import load_clean_tickers, fetch_and_prepare_data
from data_visV2_test import DataVisualizer


# --- 1. DATA EXTRACTION ---
# Load formatting rules and fetch Yahoo Finance data
tickers = load_clean_tickers('tickers.txt')
df = fetch_and_prepare_data(tickers, interval='30m', period='2mo')

# --- 2. DATA VISUALIZATION ---
# Render the finplot dashboard
visualizer = DataVisualizer(df, tickers)
visualizer.run()