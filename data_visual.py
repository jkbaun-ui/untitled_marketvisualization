import finplot as fplt
import pyqtgraph as pg

class FinplotDashboard:
    def __init__(self, df, tickers):
        self.df = df
        self.tickers = tickers
        self.state = {'mode': 'all', 'type': 'line'}
        self.plots = []
        self._setup_plots()
        self._setup_hover()

    def _setup_hover(self):
        """Connects mouse movement to a hover detection function."""
        # If fplt.add_label throws an error, use pg.TextItem directly:
        self.hover_label = pg.TextItem("", color='#000')
        self.overlay_ax.addItem(self.hover_label)
        self.hover_label.hide()
        
        # Connect the mouse move event 
        win = fplt.windows[0]
        # Use direct pg import if fplt.pyqtgraph doesn't work in your version
        win.proxy = pg.SignalProxy(win.scene().sigMouseMoved, rateLimit=60, slot=self.on_mouse_moved)

    def on_mouse_moved(self, event):
        """Detects which line is closest to the mouse cursor."""
        pos = event[0]
        
        # Check if mouse is over the overlay axis
        if self.overlay_ax.sceneBoundingRect().contains(pos):
            mouse_point = self.overlay_ax.vb.mapSceneToView(pos)
            x, y = mouse_point.x(), mouse_point.y()
            
            closest_ticker = None
            min_dist = float('inf')

            # Look through all lines in the overlay to find the closest one to the cursor
            for p in self.plots:
                if p['ax'] == self.overlay_ax and p['line'].isVisible():
                    # Get the y-value of the line at this specific x (time)
                    data = p['line'].getData()[1] # [0] is x, [1] is y
                    idx = int(x)
                    
                    if 0 <= idx < len(data):
                        line_y = data[idx]
                        dist = abs(y - line_y)
                        
                        # Set a threshold for "proximity" (e.g., 2% difference)
                        if dist < min_dist and dist < 2.0: 
                            min_dist = dist
                            closest_ticker = p['ticker']


            if closest_ticker:
                print(f"Hovering over: {closest_ticker} (Distance: {min_dist:.2f})")
                self.hover_label.setPos(x, y)
                self.hover_label.setText(f"Focused: {closest_ticker}")
                self.hover_label.show()
            else:
                self.hover_label.hide()

    def _setup_plots(self):
        self.axes = fplt.create_plot('WSB Interactive Dashboard', rows=len(self.tickers) + 1)
        self.overlay_ax = self.axes[0]

        # A & B. Loop through tickers once to setup both Overlay and Individual charts
        for i, ticker in enumerate(self.tickers):
            raw_data = self.df.xs(ticker, axis=1, level=1)
            
            # 1. Setup Overlay (Normalized to 100%)
            norm_data = (raw_data / raw_data['Close'].iloc[0]) * 100
            o_line = fplt.plot(norm_data['Close'], ax=self.overlay_ax, legend=ticker)
            o_candle = fplt.candlestick_ochl(norm_data[['Open', 'Close', 'High', 'Low']], ax=self.overlay_ax)
            o_candle.hide()
            self.plots.append({'line': o_line, 'candle': o_candle, 'ax': self.overlay_ax, 'ticker': ticker})

            # 2. Setup Individual (Raw Price)
            ax = self.axes[i+1]
            i_line = fplt.plot(raw_data['Close'], ax=ax, legend=f"{ticker} ($)")
            i_candle = fplt.candlestick_ochl(raw_data[['Open', 'Close', 'High', 'Low']], ax=ax)
            i_candle.hide()
            self.plots.append({'line': i_line, 'candle': i_candle, 'ax': ax, 'ticker': ticker})

    def key_press(self, event):
        key = event.text()
        if key == 'o':
            self.overlay_ax.show()
            for p in self.plots: 
                if p['ax'] != self.overlay_ax: p['ax'].hide()
        elif key == 'm':
            self.overlay_ax.hide()
            for p in self.plots: 
                if p['ax'] != self.overlay_ax: p['ax'].show()
        elif key == 'a':
            for ax in self.axes: ax.show()
        
        # This loop now handles both Overlay and Individual candles automatically

        if key == 'x':
            print("Mode: Mixed (Leader Focus)")
            for i, p in enumerate(self.plots):
                # We assume the first ticker added is the "Leader"
                # Note: i < 2 because each ticker has 2 entries (Overlay + Individual)
                if i < 2: 
                    p['line'].hide()
                    p['candle'].show()
                else:
                    p['line'].show()
                    p['candle'].hide()

        # Update the 'T' toggle to reset the state back to uniform
        elif key == 't':
            self.state['type'] = 'candle' if self.state['type'] == 'line' else 'line'
            for p in self.plots:
                if self.state['type'] == 'candle':
                    p['line'].hide()
                    p['candle'].show()
                else:
                    p['line'].show()
                    p['candle'].hide()

def render_dashboard(df, tickers):
    dashboard = FinplotDashboard(df, tickers)
    fplt.windows[0].keyPressEvent = dashboard.key_press
    fplt.show()