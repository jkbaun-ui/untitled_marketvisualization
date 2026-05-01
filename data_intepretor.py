import pandas as pd
import numpy as np

class MarketEvaluator:
    def __init__(self, df):
        self.df = df
        self.target = 'BTC-USD'

    def get_market_diagnosis(self):
        # 1. Prepare returns data for all tickers
        # We look at the last 30 days to find recent patterns
        close_prices = self.df.xs('Close', axis=1, level=0)
        returns_df = close_prices.pct_change().dropna()
        
        # 2. Calculate Correlation Matrix specifically for BTC
        correlations = returns_df.corr()[self.target].sort_values(ascending=False)

        # 3. Analyze "Board State"
        signals = []
        eval_score = 0
        
        # Recent Performance (Last 3 days)
        recent_returns = ((close_prices.iloc[-1] / close_prices.iloc[-4]) - 1) * 100
        btc_perf = recent_returns[self.target]

        # --- THE PLAYGROUND: Dynamic Rules ---
        
        # Rule: The "Sympathy" Move
        # Find tickers with > 0.7 correlation (Strongly linked)
        strong_links = correlations[(correlations > 0.7) & (correlations < 1.0)].index.tolist()
        for ticker in strong_links:
            ticker_perf = recent_returns[ticker]
            # If a linked stock is up but BTC is down -> "Spring Loading"
            if ticker_perf > 2 and btc_perf < 0:
                eval_score += 2
                signals.append(f"Divergence: {ticker} is pumping, BTC usually follows (+0.7 corr).")
            # If linked stock is crashing but BTC is holding -> "Falling Knife"
            if ticker_perf < -3 and btc_perf > -1:
                eval_score -= 2
                signals.append(f"Risk: {ticker} is dropping. BTC is currently overextended.")

        # Rule: The "Inverse" Hedge
        # Find tickers with negative correlation (e.g., DXY or VIX)
        inverse_links = correlations[correlations < -0.3].index.tolist()
        for ticker in inverse_links:
            if recent_returns[ticker] > 1.5:
                eval_score -= 3
                signals.append(f"Inverse Pressure: {ticker} up, causing headwind for BTC.")

        # 4. Determine Behavior Prediction
        prediction = "Consolidating (Sideways)"
        if eval_score >= 4: prediction = "Bullish: Catch-up Rally Imminent"
        if eval_score <= -4: prediction = "Bearish: Correction Likely"
        if abs(eval_score) < 2 and abs(btc_perf) > 5: prediction = "Blow-off Top / Exhaustion"

        return {
            "score": eval_score,
            "status": "STRONG" if eval_score > 0 else "WEAK",
            "prediction": prediction,
            "logic": signals[:5] # Top 5 most important signals
        }