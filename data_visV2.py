import dearpygui.dearpygui as dpg
import pandas as pd


class TickerSeries:
    def __init__(self, ticker, df, parent_axis, mode="line"):
        self.ticker = ticker
        self.df = df
        self.parent_axis = parent_axis
        self.mode = mode
        
        # DPG Tags
        self.line_tag = f"line_{ticker}"
        self.candle_tag = f"candle_{ticker}"
        self.theme_tag = f"theme_{ticker}"
        
        self._create_series()
        self._setup_theme()
        self.toggle_mode(self.mode)

    def _create_series(self):
        x = list(range(len(self.df)))
        # Add Line
        dpg.add_line_series(x, self.df['Close'].tolist(), label=self.ticker, 
                            tag=self.line_tag, parent=self.parent_axis)
        # Add Candle
        dpg.add_candle_series(x, self.df['Open'].tolist(), self.df['Close'].tolist(), 
                              self.df['Low'].tolist(), self.df['High'].tolist(), 
                              tag=self.candle_tag, parent=self.parent_axis)

    def _setup_theme(self):
        if not dpg.does_item_exist(self.theme_tag):
            with dpg.theme(tag=self.theme_tag):
                with dpg.theme_component(dpg.mvAll):
                    # Initial state: Full visibility
                    dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.0, category=dpg.mvThemeCat_Plots)
            dpg.bind_item_theme(self.line_tag, self.theme_tag)
            dpg.bind_item_theme(self.candle_tag, self.theme_tag)

    def toggle_mode(self, mode):
        self.mode = mode
        if mode == "line":
            dpg.show_item(self.line_tag)
            dpg.hide_item(self.candle_tag)
        else:
            dpg.hide_item(self.line_tag)
            dpg.show_item(self.candle_tag)

class DataVisualizer:
    def __init__(self, df, tickers):
        print("Initializing DataVisualizer...")
        dpg.create_context()
        
        self.df = df
        self.tickers = tickers
        self.ticker_objects = []
        self.view_mode = "overlay" 
        self.series_mode = "line"
        
        self.create_window()
        
        dpg.create_viewport(title="Data Lab v3", width=1200, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def create_window(self):
        with dpg.window(label="Data Lab", tag="MainVisualWindow", width=1200, height=800):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Toggle Overlay/Grid", callback=self.switch_layout)
                dpg.add_button(label="Toggle Line/Candle", callback=self.switch_series_type)
            
            with dpg.child_window(tag="PlotContainer", border=False):
                self.rebuild_plots()

    def switch_layout(self):
        self.view_mode = "grid" if self.view_mode == "overlay" else "overlay"
        self.rebuild_plots()

    def switch_series_type(self):
        self.series_mode = "candle" if self.series_mode == "line" else "line"
        for obj in self.ticker_objects:
            obj.toggle_mode(self.series_mode)

    def rebuild_plots(self):
        if dpg.does_item_exist("PlotContainer"):
            dpg.delete_item("PlotContainer", children_only=True)
        
        self.ticker_objects = []

        if self.view_mode == "overlay":
            with dpg.plot(parent="PlotContainer", height=-1, width=-1, tag="MainPlot"):
                dpg.add_plot_legend()
                x_ax = dpg.add_plot_axis(dpg.mvXAxis, label="Days")
                y_ax = dpg.add_plot_axis(dpg.mvYAxis, label="Change (%)")
                
                for t in self.tickers:
                    # Normalization logic for Overlay (%)
                    raw_data = self.df.xs(t, axis=1, level=1)
                    norm_data = (raw_data / raw_data['Close'].iloc[0]) * 100
                    obj = TickerSeries(t, norm_data, y_ax, mode=self.series_mode)
                    self.ticker_objects.append(obj)
        else:
            # Grid mode: Individual Absolute Price ($)
            for t in self.tickers:
                with dpg.plot(parent="PlotContainer", height=300, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis)
                    y_ax = dpg.add_plot_axis(dpg.mvYAxis, label=f"{t} ($)")
                    raw_data = self.df.xs(t, axis=1, level=1)
                    obj = TickerSeries(t, raw_data, y_ax, mode=self.series_mode)
                    self.ticker_objects.append(obj)

    def run(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        dpg.destroy_context()












    






    # Inside your DataVisualizer class in data_visV2.py

    def create_window(self):
        # Import the evaluator here or at the top
        from data_intepretor import MarketEvaluator
        self.evaluator = MarketEvaluator(self.df)
        diag = self.evaluator.get_market_diagnosis()

        with dpg.window(label="Data Lab Control Center", width=300, height=800, pos=[1200, 0]):
            dpg.add_text("MARKET EVALUATION", color=[0, 255, 0])
            dpg.add_separator()
            
            # Display the "Chess Move" logic
            dpg.add_text(f"Status: {diag['status']}")
            dpg.add_text(f"Score: {diag['score']}")
            dpg.add_separator()
            
            dpg.add_text("PREDICTION (1 WEEK):", color=[255, 200, 0])
            dpg.add_text(diag['prediction'], wrap=280)
            
            dpg.add_spacing(count=5)
            dpg.add_text("LOGIC FOUNDATION:")
            for msg in diag['logic']:
                dpg.add_text(f"- {msg}", color=[200, 200, 200], wrap=280)

            dpg.add_spacing(count=10)
            dpg.add_button(label="RE-EVALUATE", callback=self.update_eval)