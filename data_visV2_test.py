import dearpygui.dearpygui as dpg
import pandas as pd
from data_intepretor import MarketEvaluator # Ensure the filename matches yours

class TickerSeries:
    def __init__(self, ticker, df, parent_axis, mode="line"):
        self.ticker = ticker
        self.df = df
        self.parent_axis = parent_axis
        self.mode = mode
        self.line_tag = f"line_{ticker}"
        self.candle_tag = f"candle_{ticker}"
        self.theme_tag = f"theme_{ticker}"
        self._create_series()
        self._setup_theme()
        self.toggle_mode(self.mode)

    def _create_series(self):
        x = list(range(len(self.df)))
        dpg.add_line_series(x, self.df['Close'].tolist(), label=self.ticker, tag=self.line_tag, parent=self.parent_axis)
        dpg.add_candle_series(x, self.df['Open'].tolist(), self.df['Close'].tolist(), 
                              self.df['Low'].tolist(), self.df['High'].tolist(), tag=self.candle_tag, parent=self.parent_axis)

    def _setup_theme(self):
        if not dpg.does_item_exist(self.theme_tag):
            with dpg.theme(tag=self.theme_tag):
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.0, category=dpg.mvThemeCat_Plots)
            dpg.bind_item_theme(self.line_tag, self.theme_tag)
            dpg.bind_item_theme(self.candle_tag, self.theme_tag)

    def toggle_mode(self, mode):
        self.mode = mode
        if mode == "line":
            dpg.show_item(self.line_tag); dpg.hide_item(self.candle_tag)
        else:
            dpg.hide_item(self.line_tag); dpg.show_item(self.candle_tag)

class DataVisualizer:
    def __init__(self, df, tickers):
        dpg.create_context()
        self.df = df
        self.tickers = tickers
        self.view_mode = "overlay" 
        self.series_mode = "line"
        self.evaluator = MarketEvaluator(self.df)
        
        self.create_window()
        
        dpg.create_viewport(title="Data Lab v3", width=1600, height=900)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def create_window(self):
        # MAIN CHART WINDOW
        with dpg.window(label="Data Lab", width=1100, height=800, pos=[0,0]):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Toggle Layout", callback=self.switch_layout)
                dpg.add_button(label="Toggle Series", callback=self.switch_series_type)
            with dpg.child_window(tag="PlotContainer"):
                self.rebuild_plots()

        # SIDE EVALUATOR WINDOW
        diag = self.evaluator.get_market_diagnosis()
        with dpg.window(label="Control Center", width=400, height=800, pos=[1105, 0]):
            dpg.add_text("MARKET EVALUATION", color=[0, 255, 0])
            dpg.add_separator()
            
            dpg.add_text(f"Status: {diag['status']}", tag="eval_status")
            dpg.add_text(f"Score: {diag['score']}", tag="eval_score")
            dpg.add_separator()
            
            dpg.add_text("PREDICTION (1 WEEK):", color=[255, 200, 0])
            dpg.add_text(diag['prediction'], tag="eval_pred", wrap=380)
            
            dpg.add_spacing(count=5)
            dpg.add_text("LOGIC FOUNDATION:")
            dpg.add_text("\n".join([f"- {m}" for m in diag['logic']]), tag="eval_logic", wrap=380)

            dpg.add_spacing(count=10)
            dpg.add_button(label="RE-EVALUATE", callback=self.update_eval)

    def update_eval(self):
        diag = self.evaluator.get_market_diagnosis()
        
        # NEW: Find the single highest correlated ticker
        corr_matrix = self.df.xs('Close', axis=1, level=0).pct_change().corr()
        leader = corr_matrix['BTC-USD'].sort_values(ascending=False).index[1] # [1] because [0] is BTC itself
        
        dpg.set_value("eval_status", f"Current Market Leader: {leader}")
        dpg.set_value("eval_score", f"Engine Eval: {diag['score']}")
        dpg.set_value("eval_pred", diag['prediction'])
        dpg.set_value("eval_logic", "\n".join(diag['logic']))
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
            with dpg.plot(parent="PlotContainer", height=-1, width=-1):
                dpg.add_plot_legend()
                x_ax = dpg.add_plot_axis(dpg.mvXAxis, label="Days")
                y_ax = dpg.add_plot_axis(dpg.mvYAxis, label="Change (%)")
                for t in self.tickers:
                    raw_data = self.df.xs(t, axis=1, level=1)
                    norm_data = (raw_data / raw_data['Close'].iloc[0]) * 100
                    self.ticker_objects.append(TickerSeries(t, norm_data, y_ax, mode=self.series_mode))
        else:
            for t in self.tickers:
                with dpg.plot(parent="PlotContainer", height=300, width=-1):
                    dpg.add_plot_axis(dpg.mvXAxis)
                    y_ax = dpg.add_plot_axis(dpg.mvYAxis, label=f"{t} ($)")
                    self.ticker_objects.append(TickerSeries(t, self.df.xs(t, axis=1, level=1), y_ax, mode=self.series_mode))

    def run(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        dpg.destroy_context()