from data_extractor import fetch_smart_data, load_clean_tickers, fetch_and_prepare_data
from data_visV2_test import DataVisualizer


tickers = load_clean_tickers('tickers.txt')
df = fetch_smart_data(tickers, interval='30m')

# Check which tickers actually made it into the dataframe
# Level 1 is where our Ticker names live now
try:
    retrieved_tickers = df.columns.get_level_values(1).unique().tolist()
except KeyError:
    print("Error: No valid tickers found in the dataframe.")
    retrieved_tickers = []

# --- 2. DATA VISUALIZATION ---
# Only pass tickers that exist in the df to avoid KeyErrors

print(f"Tickers in DataFrame: {retrieved_tickers}")

visualizer = DataVisualizer(df, retrieved_tickers)
visualizer.run()